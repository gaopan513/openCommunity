"""
用户认证与资料视图

提供注册、登录、微信小程序登录、个人资料管理、修改密码等接口。
"""
import logging
import secrets

import requests
from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from common.response import success_response, created_response, error_response
from common.exceptions import BusinessError
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """用户注册接口
    
    POST /api/v1/auth/register/
    
    请求体：
        username: 用户名（必填）
        password: 密码（必填，至少6位）
        phone: 手机号（选填）
        community_name: 小区名称（选填）
    
    角色固定为 resident；商家身份需通过入驻申请审核后授予，
    请求中的 role 字段会被忽略。
    
    返回：
        201: 注册成功，返回用户基本信息
        400: 用户名已存在或参数错误
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """处理注册请求"""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 生成 Token，注册后自动登录
        refresh = RefreshToken.for_user(user)
        
        return created_response(
            data={
                'user': UserProfileSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            message='注册成功'
        )


class LoginView(APIView):
    """用户登录接口
    
    POST /api/v1/auth/login/
    
    请求体：
        username: 用户名
        password: 密码
    
    返回：
        200: 登录成功，返回用户信息和 Token
        401: 用户名或密码错误
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """处理登录请求"""
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        
        if not username or not password:
            return error_response('请输入用户名和密码', code=40001)
        
        # 不区分「用户不存在 / 密码错误 / 账号禁用」，统一提示，避免账号状态枚举
        user = authenticate(username=username, password=password)
        
        if user is None:
            return error_response('用户名或密码错误', code=40101, http_status=401)
        
        # 生成 JWT Token
        refresh = RefreshToken.for_user(user)
        
        return success_response(
            data={
                'user': UserProfileSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            message='登录成功'
        )


class WechatLoginView(APIView):
    """微信小程序登录接口

    POST /api/v1/auth/wechat-login/

    请求体：
        code: wx.login 获取的临时登录凭证（必填）

    流程：code 换取 openid → 已有用户直接签发 JWT；
    不存在则静默创建 resident 用户（不设置密码，仅能通过微信端登录）。
    角色沿用模型默认值，不做显式赋值（角色只能由审核授予）。

    返回：
        200: 登录成功，返回用户信息和 Token（与登录接口结构一致）
        400: 缺少 code 或微信侧凭证无效
        500: 微信登录未配置
    """
    permission_classes = [AllowAny]

    # 微信 code2session 接口地址
    JSCODE2SESSION_URL = 'https://api.weixin.qq.com/sns/jscode2session'

    def post(self, request):
        """处理微信小程序登录请求"""
        code = request.data.get('code', '')
        if not code:
            return error_response('缺少微信登录凭证', code=40001)

        appid = settings.WECHAT_MINIAPP_APPID
        secret = settings.WECHAT_MINIAPP_SECRET
        if not appid or not secret:
            logger.error('微信登录未配置：请设置 WECHAT_MINIAPP_APPID / WECHAT_MINIAPP_SECRET 环境变量')
            return error_response('微信登录暂未配置', code=50101, http_status=500)

        try:
            resp = requests.get(
                self.JSCODE2SESSION_URL,
                params={
                    'appid': appid,
                    'secret': secret,
                    'js_code': code,
                    'grant_type': 'authorization_code',
                },
                timeout=5,
            )
            result = resp.json()
        except (requests.RequestException, ValueError):
            logger.warning('调用微信 jscode2session 失败（网络异常或响应非 JSON）')
            return error_response('微信登录失败，请重试', code=40102)

        if result.get('errcode'):
            logger.warning(
                '微信 jscode2session 返回错误：errcode=%s errmsg=%s',
                result.get('errcode'), result.get('errmsg')
            )
            return error_response('微信登录失败，请重试', code=40102)

        user = self._get_or_create_wechat_user(result['openid'], result.get('unionid'))

        refresh = RefreshToken.for_user(user)
        return success_response(
            data={
                'user': UserProfileSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            message='登录成功'
        )

    @staticmethod
    def _get_or_create_wechat_user(openid, unionid=None):
        """按 openid 查找用户，不存在则静默创建

        创建的用户的密码不可用（无法走账号密码登录），
        username 使用随机串避免碰撞；openid 唯一保证一人一号。
        """
        user = User.objects.filter(openid=openid).first()
        if user:
            if unionid and not user.unionid:
                # 首次未下发 unionid、后续补发的场景
                user.unionid = unionid
                user.save(update_fields=['unionid'])
            return user

        try:
            with transaction.atomic():
                user = User(username=f"wx_{secrets.token_hex(8)}", openid=openid)
                if unionid:
                    user.unionid = unionid
                user.set_unusable_password()
                user.save()
        except IntegrityError:
            # 并发首次登录：另一请求已完成创建（openid 唯一约束冲突），直接复用
            user = User.objects.filter(openid=openid).first()
            if user is None:
                raise
        return user


class DebugWechatLoginView(WechatLoginView):
    """本地测试登录（仅 DEBUG 阶段可用，禁止用于生产）

    POST /api/v1/auth/debug-login/

    仅方便小程序在没有接入真实小程序 AppID/Secret 时本地联调登录链路。
    请求体以 openid 替代微信 code（前台用 wx.login 返回的固定 code 映射一个
    归一化 openid，再传给本接口），从而绕开 jscode2session，直接换取 JWT。

    与真实 WechatLoginView 共用 _get_or_create_wechat_user，测试流量同样
    落到 openid 用户表，切回真实一键登录后该 openid 仍可继续使用。
    生产环境（DJANGO_DEBUG=False）强行关闭，返回 404，避免留下后门。
    """

    def post(self, request):
        if not settings.DEBUG:
            # 生产：干脆当接口不存在，避免暴露
            return error_response('接口不存在', code=40400, http_status=404)

        openid = (request.data.get('openid') or '').strip()
        if not openid:
            return error_response('缺少 openid', code=40001)
        if len(openid) > 64:
            return error_response('openid 长度超出限制', code=40001)

        user = self._get_or_create_wechat_user(openid)

        refresh = RefreshToken.for_user(user)
        return success_response(
            data={
                'user': UserProfileSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            message='登录成功'
        )


class ProfileView(APIView):
    """个人资料接口
    
    GET /api/v1/users/profile/ — 获取当前用户资料
    PUT /api/v1/users/profile/ — 更新个人资料
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取当前登录用户的个人资料"""
        serializer = UserProfileSerializer(request.user)
        return success_response(data=serializer.data)
    
    def put(self, request):
        """更新个人资料
        
        可更新字段：nickname, phone, avatar, community_name, address
        """
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message='资料更新成功')


class ChangePasswordView(APIView):
    """修改密码接口
    
    PUT /api/v1/users/password/
    
    请求体：
        old_password: 旧密码
        new_password: 新密码（至少6位）
    """
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        """处理密码修改"""
        user = request.user
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')
        
        # 验证旧密码
        if not user.check_password(old_password):
            return error_response('旧密码不正确', code=40002)
        
        # 执行 Django 密码强度校验（AUTH_PASSWORD_VALIDATORS，含最小长度、常见弱密码等）
        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return error_response('；'.join(e.messages), code=40003)
        
        # 新旧密码不能相同
        if old_password == new_password:
            return error_response('新密码不能与旧密码相同', code=40004)
        
        user.set_password(new_password)
        user.save()
        
        # 将前端携带的 refresh token 拉黑，使旧会话无法续期（配合前端登出）
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                # token 无效/已过期/已拉黑，忽略
                pass

        return success_response(message='密码修改成功，请重新登录')


class LogoutView(APIView):
    """用户登出接口

    POST /api/v1/auth/logout/

    请求体：
        refresh: 登录时获得的 refresh token

    将 refresh token 加入黑名单使其无法续期；
    已签发的 access token 需等待自然过期（最长 2 小时）。
    以 refresh token 本身作为凭证，故无需 access token 也可调用。
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """处理登出请求"""
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return error_response('请提供 refresh token', code=40001)

        try:
            RefreshToken(refresh_token).blacklist()
        except Exception:
            # token 无效/已过期/已拉黑：视为已登出，不泄露 token 有效性信息
            pass

        return success_response(message='已退出登录')
