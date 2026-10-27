"""
用户模块单元测试

覆盖注册、登录、微信小程序登录、资料管理、密码修改、权限控制等核心功能。
"""
from unittest.mock import patch, MagicMock

from django.db import IntegrityError
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User


class UserModelTest(TestCase):
    """用户模型测试"""
    
    def test_create_resident_user(self):
        """测试创建普通居民用户"""
        user = User.objects.create_user(
            username='resident1',
            password='test123456',
            role=User.Role.RESIDENT,
            phone='13800138000',
            community_name='阳光花园'
        )
        self.assertEqual(user.role, 'resident')
        self.assertEqual(user.phone, '13800138000')
        self.assertTrue(user.check_password('test123456'))
        self.assertFalse(user.is_merchant)
        self.assertFalse(user.is_admin)
    
    def test_create_merchant_user(self):
        """测试创建商家用户"""
        user = User.objects.create_user(
            username='merchant1',
            password='test123456',
            role=User.Role.MERCHANT
        )
        self.assertTrue(user.is_merchant)
        self.assertFalse(user.is_admin)
    
    def test_create_admin_user(self):
        """测试创建管理员用户"""
        user = User.objects.create_superuser(
            username='admin1',
            password='test123456'
        )
        user.role = User.Role.ADMIN
        user.save()
        self.assertTrue(user.is_admin)
    
    def test_user_str(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(
            username='testuser',
            password='test123456',
            role=User.Role.RESIDENT
        )
        self.assertIn('testuser', str(user))
        self.assertIn('普通居民', str(user))


class RegisterAPITest(APITestCase):
    """注册接口测试"""
    
    def setUp(self):
        self.url = '/api/v1/auth/register/'
    
    def test_register_resident_success(self):
        """测试居民注册成功"""
        data = {
            'username': 'newuser',
            'password': 'pass123456',
            'role': 'resident',
            'phone': '13900139000',
            'community_name': '翠湖小区'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 0)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertEqual(response.data['data']['user']['username'], 'newuser')
        self.assertEqual(response.data['data']['user']['role'], 'resident')
    
    def test_register_role_ignored(self):
        """测试注册时携带的 merchant 角色被忽略，一律为 resident

        商家身份只能通过入驻审核授予，防止自封商家角色。
        """
        data = {
            'username': 'shopowner',
            'password': 'pass123456',
            'role': 'merchant',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['user']['role'], 'resident')
    
    def test_register_duplicate_username(self):
        """测试重复用户名注册失败"""
        User.objects.create_user(username='existuser', password='pass123456')
        data = {
            'username': 'existuser',
            'password': 'pass123456',
            'role': 'resident',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_short_password(self):
        """测试密码过短被拒绝"""
        data = {
            'username': 'newuser2',
            'password': '123',
            'role': 'resident',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_admin_role_ignored(self):
        """测试注册携带 admin 角色也会被忽略，固定为 resident

        角色字段完全由服务端决定，请求体中的 role 不生效。
        """
        data = {
            'username': 'hackadmin',
            'password': 'pass123456',
            'role': 'admin',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['user']['role'], 'resident')


class LoginAPITest(APITestCase):
    """登录接口测试"""
    
    def setUp(self):
        self.url = '/api/v1/auth/login/'
        self.user = User.objects.create_user(
            username='loginuser',
            password='pass123456',
            role=User.Role.RESIDENT
        )
    
    def test_login_success(self):
        """测试登录成功"""
        data = {'username': 'loginuser', 'password': 'pass123456'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        self.assertIn('access', response.data['data'])
        self.assertEqual(response.data['data']['user']['username'], 'loginuser')
    
    def test_login_wrong_password(self):
        """测试密码错误"""
        data = {'username': 'loginuser', 'password': 'wrongpass'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_nonexistent_user(self):
        """测试不存在的用户"""
        data = {'username': 'nouser', 'password': 'pass123456'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_empty_fields(self):
        """测试空字段"""
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_disabled_user(self):
        """测试被禁用的用户：与密码错误统一提示，避免账号状态枚举"""
        self.user.is_active = False
        self.user.save()
        data = {'username': 'loginuser', 'password': 'pass123456'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileAPITest(APITestCase):
    """个人资料接口测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            password='pass123456',
            role=User.Role.RESIDENT,
            phone='13800138001'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_get_profile(self):
        """测试获取个人资料"""
        response = self.client.get('/api/v1/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['username'], 'profileuser')
        self.assertEqual(response.data['data']['phone'], '13800138001')
    
    def test_update_profile(self):
        """测试更新个人资料"""
        data = {'community_name': '和平小区', 'address': '3栋2单元501'}
        response = self.client.put('/api/v1/users/profile/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.community_name, '和平小区')
    
    def test_profile_requires_auth(self):
        """测试未认证不能访问资料"""
        client = APIClient()
        response = client.get('/api/v1/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordAPITest(APITestCase):
    """修改密码接口测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='pwduser',
            password='oldpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/users/password/'
    
    def test_change_password_success(self):
        """测试修改密码成功"""
        data = {'old_password': 'oldpass123', 'new_password': 'newpass456'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456'))
    
    def test_change_password_wrong_old(self):
        """测试旧密码错误"""
        data = {'old_password': 'wrongold', 'new_password': 'newpass456'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_too_short(self):
        """测试新密码过短"""
        data = {'old_password': 'oldpass123', 'new_password': '123'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_same_as_old(self):
        """测试新旧密码相同"""
        data = {'old_password': 'oldpass123', 'new_password': 'oldpass123'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutAPITest(APITestCase):
    """登出接口测试"""

    def setUp(self):
        self.url = '/api/v1/auth/logout/'
        self.user = User.objects.create_user(
            username='logoutuser',
            password='pass123456'
        )

    def _login(self):
        """登录并返回 refresh token"""
        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': 'logoutuser', 'password': 'pass123456'},
            format='json'
        )
        return response.data['data']['refresh']

    def test_logout_blacklists_refresh_token(self):
        """测试登出后 refresh token 被拉黑，无法再刷新"""
        refresh = self._login()
        response = self.client.post(self.url, {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)

        # 已拉黑的 token 再去刷新应被拒绝
        refresh_response = self.client.post(
            '/api/v1/auth/refresh/', {'refresh': refresh}, format='json'
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token(self):
        """测试缺少 refresh token 时返回参数错误"""
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_invalid_token_still_succeeds(self):
        """测试无效/已过期的 token 登出仍返回成功（不泄露 token 有效性）"""
        response = self.client.post(self.url, {'refresh': 'invalid-token'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


def _wx_response(payload):
    """构造模拟的微信 jscode2session HTTP 响应"""
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    return mock_resp


@override_settings(WECHAT_MINIAPP_APPID='wx-test-appid', WECHAT_MINIAPP_SECRET='test-secret')
class WechatLoginAPITest(APITestCase):
    """微信小程序登录接口测试"""

    def setUp(self):
        self.url = '/api/v1/auth/wechat-login/'

    @patch('apps.users.views.requests.get')
    def test_first_login_creates_resident(self, mock_get):
        """测试首次登录静默创建 resident 用户，密码不可用，正常签发 Token"""
        mock_get.return_value = _wx_response({'openid': 'oX-openid-001', 'unionid': 'u-union-001'})
        response = self.client.post(self.url, {'code': 'valid-code'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

        user = User.objects.get(openid='oX-openid-001')
        self.assertEqual(user.role, User.Role.RESIDENT)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.unionid, 'u-union-001')
        # token 与 user 对应
        self.assertEqual(response.data['data']['user']['username'], user.username)

    @patch('apps.users.views.requests.get')
    def test_second_login_returns_same_user(self, mock_get):
        """测试同一 openid 二次登录复用既有用户，不重复建号"""
        existing = User.objects.create(username='wx_existing', openid='oX-openid-dup')
        existing.set_unusable_password()
        existing.save()

        mock_get.return_value = _wx_response({'openid': 'oX-openid-dup'})
        response = self.client.post(self.url, {'code': 'valid-code'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['user']['username'], 'wx_existing')
        self.assertEqual(User.objects.filter(openid='oX-openid-dup').count(), 1)

    @patch('apps.users.views.requests.get')
    def test_second_login_backfills_unionid(self, mock_get):
        """测试首次未下发 unionid 的用户，再次登录时补写 unionid"""
        User.objects.create(username='wx_no_union', openid='oX-openid-backfill')

        mock_get.return_value = _wx_response({'openid': 'oX-openid-backfill', 'unionid': 'u-late'})
        response = self.client.post(self.url, {'code': 'valid-code'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(openid='oX-openid-backfill', unionid='u-late').exists())

    def test_missing_code(self):
        """测试缺少 code 返回参数错误"""
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 40001)

    @patch('apps.users.views.requests.get')
    def test_wechat_invalid_code(self, mock_get):
        """测试微信侧凭证无效（errcode=40029）不创建用户"""
        mock_get.return_value = _wx_response({'errcode': 40029, 'errmsg': 'invalid code'})
        response = self.client.post(self.url, {'code': 'bad-code'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 40102)
        self.assertFalse(User.objects.filter(openid='any').exists())

    @patch('apps.users.views.requests.get', side_effect=__import__('requests').RequestException('timeout'))
    def test_wechat_service_unreachable(self, mock_get):
        """测试微信接口网络异常时返回统一错误码，不创建用户"""
        response = self.client.post(self.url, {'code': 'valid-code'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 40102)

    @patch('apps.users.views.requests.get')
    def test_first_login_without_unionid(self, mock_get):
        """测试微信未绑定开放平台时（无 unionid）也可正常注册，unionid 保持为空"""
        mock_get.return_value = _wx_response({'openid': 'oX-openid-nounion'})
        response = self.client.post(self.url, {'code': 'valid-code'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = User.objects.get(openid='oX-openid-nounion')
        self.assertIsNone(obj.unionid)
        self.assertEqual(obj.role, User.Role.RESIDENT)

    @patch('apps.users.views.requests.get')
    def test_concurrent_first_login_race(self, mock_get):
        """测试并发首登竞态：INSERT 撞 openid 唯一约束时回退复用既有用户而非报 500"""
        User.objects.create(username='wx_racer', openid='oX-race')
        mock_get.return_value = _wx_response({'openid': 'oX-race'})

        with patch.object(User, 'save', side_effect=IntegrityError):
            response = self.client.post(self.url, {'code': 'valid-code'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['user']['username'], 'wx_racer')

    @override_settings(WECHAT_MINIAPP_APPID='', WECHAT_MINIAPP_SECRET='')
    def test_not_configured(self):
        """测试未配置 appid/secret 时返回明确错误码"""
        response = self.client.post(self.url, {'code': 'valid-code'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['code'], 50101)
