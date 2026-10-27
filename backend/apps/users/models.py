"""
用户模块数据模型

扩展 Django 内置 User，增加角色、头像、小区信息等字段。
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from common.utils import avatar_upload_path
from common.validators import validate_phone_number


class User(AbstractUser):
    """自定义用户模型
    
    在 Django AbstractUser 基础上扩展：
    - role: 用户角色（居民/商家/管理员）
    - phone: 手机号
    - avatar: 头像
    - community_name: 所属小区名称
    - address: 详细地址
    - openid/unionid: 微信身份（小程序静默登录使用）
    
    角色说明：
    - resident: 普通居民，可发帖、交易、预约
    - merchant: 商家用户，可入驻、发布活动
    - admin: 管理员/物业，可审核、管理
    """
    
    class Role(models.TextChoices):
        RESIDENT = 'resident', '普通居民'
        MERCHANT = 'merchant', '商家用户'
        ADMIN = 'admin', '管理员'
    
    role = models.CharField(
        '用户角色',
        max_length=20,
        choices=Role.choices,
        default=Role.RESIDENT
    )
    phone = models.CharField(
        '手机号',
        max_length=11,
        blank=True,
        default='',
        validators=[validate_phone_number]
    )
    avatar = models.ImageField(
        '头像',
        upload_to=avatar_upload_path,
        blank=True,
        null=True
    )
    community_name = models.CharField(
        '所属小区',
        max_length=100,
        blank=True,
        default=''
    )
    address = models.CharField(
        '详细地址',
        max_length=200,
        blank=True,
        default=''
    )
    openid = models.CharField(
        '微信openid',
        max_length=64,
        unique=True,
        null=True,
        blank=True
    )
    unionid = models.CharField(
        '微信unionid',
        max_length=64,
        unique=True,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField('注册时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username}({self.get_role_display()})"
    
    @property
    def is_merchant(self):
        """是否为商家角色"""
        return self.role == self.Role.MERCHANT
    
    @property
    def is_admin(self):
        """是否为管理员角色"""
        return self.role == self.Role.ADMIN


@receiver(post_delete, sender=User)
def delete_user_avatar_file(sender, instance, **kwargs):
    """删除用户时同步清理头像物理文件，避免孤儿文件残留"""
    if instance.avatar:
        instance.avatar.delete(save=False)
