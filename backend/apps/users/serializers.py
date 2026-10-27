"""
用户模块序列化器

提供注册、登录、资料管理的请求/响应数据序列化。
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from common.validators import validate_image


class RegisterSerializer(serializers.ModelSerializer):
    """注册序列化器

    处理用户注册请求，验证用户名唯一性和密码强度。
    角色固定为 resident（商家身份需入驻审核通过后授予），
    请求体中的 role 字段被忽略，防止自封商家角色。
    """
    password = serializers.CharField(
        write_only=True, 
        min_length=6,
        style={'input_type': 'password'},
        help_text='密码，至少6位'
    )
    
    class Meta:
        model = User
        fields = ['username', 'password', 'phone', 'community_name']
        extra_kwargs = {
            'username': {'help_text': '用户名，3-30个字符'},
        }

    def validate_password(self, value):
        """执行 Django 密码强度校验（AUTH_PASSWORD_VALIDATORS）"""
        validate_password(value)
        return value
    
    def create(self, validated_data):
        """创建用户并加密密码
        
        Args:
            validated_data: 验证后的数据
            
        Returns:
            User: 新创建的用户实例
        """
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器

    用于展示和编辑用户个人资料。
    """
    role_display = serializers.CharField(
        source='get_role_display', 
        read_only=True,
        help_text='角色中文名'
    )
    avatar = serializers.ImageField(
        required=False, allow_null=True, validators=[validate_image],
        help_text='头像，不超过5MB，仅支持 jpg/jpeg/png/webp'
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'role', 'role_display',
            'phone', 'avatar', 'community_name', 'address',
            'email', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'role', 'created_at']


class UserSimpleSerializer(serializers.ModelSerializer):
    """用户简要信息序列化器
    
    用于在帖子、评论等场景中嵌套展示作者信息。
    """
    
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'role']
        read_only_fields = fields
