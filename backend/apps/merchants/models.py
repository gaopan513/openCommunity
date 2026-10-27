"""
商家模块数据模型

包含商家分类、商家信息、商家图片、商家活动、商家评价等模型。
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from common.utils import merchant_upload_path, activity_upload_path, merchant_logo_upload_path
from common.validators import validate_rating, validate_phone_number


class MerchantCategory(models.Model):
    """商家分类模型

    用于对商家进行分类管理，如餐饮、超市、维修等。
    """
    name = models.CharField('分类名称', max_length=50)
    slug = models.SlugField('标识', unique=True)
    icon = models.CharField('图标', max_length=50, blank=True, default='')
    sort_order = models.IntegerField('排序', default=0)

    class Meta:
        ordering = ['sort_order']
        verbose_name = '商家分类'
        verbose_name_plural = '商家分类'

    def __str__(self):
        return self.name


class Merchant(models.Model):
    """商家模型

    商家入驻信息，包含基本资料、审核状态、评分等。
    """

    class Status(models.TextChoices):
        PENDING = 'pending', '待审核'
        APPROVED = 'approved', '已通过'
        REJECTED = 'rejected', '已拒绝'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='merchant_profile',
        verbose_name='关联用户'
    )
    name = models.CharField('商家名称', max_length=100)
    category = models.ForeignKey(
        MerchantCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='merchants',
        verbose_name='商家分类'
    )
    address = models.CharField('地址', max_length=200)
    phone = models.CharField('联系电话', max_length=20, validators=[validate_phone_number])
    business_hours = models.CharField('营业时间', max_length=200, blank=True, default='')
    description = models.TextField('商家简介', blank=True, default='')
    logo = models.ImageField(
        '商家 Logo',
        upload_to=merchant_logo_upload_path,
        null=True,
        blank=True,
        help_text='店铺图标，建议 200×200 以上正方形图片'
    )
    license_image = models.ImageField(
        '营业执照',
        upload_to=merchant_upload_path,
        null=True,
        blank=True
    )
    status = models.CharField(
        '审核状态',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    avg_rating = models.DecimalField(
        '平均评分',
        max_digits=2,
        decimal_places=1,
        default=0
    )
    review_count = models.IntegerField('评价数量', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '商家'
        verbose_name_plural = '商家'

    def __str__(self):
        return self.name


class MerchantImage(models.Model):
    """商家图片模型

    商家环境照、产品图等附加图片。
    """
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='所属商家'
    )
    image = models.ImageField('图片', upload_to=merchant_upload_path)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '商家图片'
        verbose_name_plural = '商家图片'

    def __str__(self):
        return f"{self.merchant.name} - 图片{self.pk}"


class Activity(models.Model):
    """商家活动模型

    商家发布的促销、优惠等活动信息。
    """
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='所属商家'
    )
    title = models.CharField('活动标题', max_length=200)
    description = models.TextField('活动描述', blank=True, default='')
    image = models.ImageField(
        '活动图片',
        upload_to=activity_upload_path,
        null=True,
        blank=True
    )
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间')
    discount_info = models.CharField('优惠信息', max_length=200, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '商家活动'
        verbose_name_plural = '商家活动'

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        """判断活动是否正在进行中"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time


class MerchantReview(models.Model):
    """商家评价模型

    居民对商家的评价，每个用户对每个商家只能评价一次。
    """
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='所属商家'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='merchant_reviews',
        verbose_name='评价用户'
    )
    rating = models.IntegerField('评分', validators=[validate_rating])
    content = models.TextField('评价内容', blank=True, default='')
    reply = models.TextField('商家回复', blank=True, default='')
    replied_at = models.DateTimeField('回复时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        unique_together = ['merchant', 'user']
        ordering = ['-created_at']
        verbose_name = '商家评价'
        verbose_name_plural = '商家评价'

    def __str__(self):
        return f"{self.user.username} 评价 {self.merchant.name}"


@receiver(post_delete, sender=MerchantImage)
def delete_merchant_image_file(sender, instance, **kwargs):
    """删除商家图片记录时同步清理物理文件，避免孤儿文件残留"""
    if instance.image:
        instance.image.delete(save=False)


@receiver(post_delete, sender=Activity)
def delete_activity_image_file(sender, instance, **kwargs):
    """删除活动记录时同步清理活动图片物理文件"""
    if instance.image:
        instance.image.delete(save=False)


@receiver(post_delete, sender=Merchant)
def delete_merchant_image_files(sender, instance, **kwargs):
    """删除商家时同步清理 logo 与营业执照物理文件"""
    if instance.logo:
        instance.logo.delete(save=False)
    if instance.license_image:
        instance.license_image.delete(save=False)
