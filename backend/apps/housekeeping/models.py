"""
家政服务模块数据模型

包含服务分类、服务提供者、服务项目、预约订单、服务评价等模型。
"""
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from common.utils import housekeeping_upload_path
from common.validators import validate_rating, validate_phone_number


class ServiceCategory(models.Model):
    """家政服务分类

    如：保洁、维修、搬家、月嫂等。
    """
    name = models.CharField('分类名称', max_length=50)
    slug = models.SlugField('标识', max_length=50, unique=True)
    icon = models.CharField('图标', max_length=100, blank=True, default='')
    sort_order = models.IntegerField('排序', default=0)

    class Meta:
        verbose_name = '服务分类'
        verbose_name_plural = '服务分类'
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class ServiceProvider(models.Model):
    """家政服务提供者

    商家用户申请成为家政服务提供者，需管理员审核通过。
    """

    class Status(models.TextChoices):
        PENDING = 'pending', '待审核'
        APPROVED = 'approved', '已通过'
        REJECTED = 'rejected', '已拒绝'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_profile',
        verbose_name='关联用户'
    )
    name = models.CharField('服务名称', max_length=100)
    service_area = models.CharField('服务区域', max_length=200, blank=True, default='')
    description = models.TextField('服务描述', blank=True, default='')
    qualification_image = models.ImageField(
        '资质图片',
        upload_to=housekeeping_upload_path,
        null=True,
        blank=True
    )
    phone = models.CharField('联系电话', max_length=20, validators=[validate_phone_number])
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
    review_count = models.PositiveIntegerField('评价数量', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '服务提供者'
        verbose_name_plural = '服务提供者'
        ordering = ['-avg_rating']

    def __str__(self):
        return self.name


class ServiceItem(models.Model):
    """具体服务项目

    服务提供者发布的具体服务，如"两居室深度保洁"。
    """
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='服务提供者'
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='服务分类'
    )
    title = models.CharField('服务标题', max_length=200)
    description = models.TextField('服务描述', blank=True, default='')
    price_min = models.DecimalField('最低价', max_digits=10, decimal_places=2)
    price_max = models.DecimalField('最高价', max_digits=10, decimal_places=2)
    duration = models.CharField('服务时长', max_length=50, blank=True, default='')

    class Meta:
        verbose_name = '服务项目'
        verbose_name_plural = '服务项目'
        ordering = ['category', 'title']

    def __str__(self):
        return self.title


class Booking(models.Model):
    """家政服务预约订单

    居民用户预约某个服务项目，由服务提供者确认并执行。
    """

    class Status(models.TextChoices):
        PENDING = 'pending', '待确认'
        CONFIRMED = 'confirmed', '已确认'
        IN_SERVICE = 'in_service', '服务中'
        COMPLETED = 'completed', '已完成'
        REVIEWED = 'reviewed', '已评价'
        REJECTED = 'rejected', '已拒绝'
        CANCELLED = 'cancelled', '已取消'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='预约用户'
    )
    service_item = models.ForeignKey(
        ServiceItem,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='服务项目'
    )
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='服务提供者'
    )
    preferred_date = models.DateField('预约日期')
    preferred_time = models.CharField('预约时段', max_length=50)
    status = models.CharField(
        '订单状态',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    remark = models.TextField('备注', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '预约订单'
        verbose_name_plural = '预约订单'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.service_item.title}"


class ServiceReview(models.Model):
    """家政服务评价

    居民在服务完成后对服务提供者进行评价。
    """
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='关联订单'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_reviews',
        verbose_name='评价用户'
    )
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='服务提供者'
    )
    rating = models.IntegerField('评分', validators=[validate_rating])
    content = models.TextField('评价内容', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '服务评价'
        verbose_name_plural = '服务评价'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} 评价 {self.provider.name} ({self.rating}分)"


@receiver(post_delete, sender=ServiceProvider)
def delete_provider_qualification_file(sender, instance, **kwargs):
    """删除服务提供者时同步清理资质图片物理文件，避免孤儿文件残留"""
    if instance.qualification_image:
        instance.qualification_image.delete(save=False)
