"""
二手市场模块数据模型

包含商品分类、商品、商品图片、商品评论等模型。
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from common.utils import product_upload_path
from common.validators import validate_positive_price


class ProductCategory(models.Model):
    """商品分类模型

    用于对二手商品进行分类管理，如家具、电子产品、图书等。
    """
    name = models.CharField('分类名称', max_length=50)
    slug = models.SlugField('分类标识', max_length=50, unique=True)
    sort_order = models.IntegerField('排序', default=0)

    class Meta:
        verbose_name = '商品分类'
        verbose_name_plural = '商品分类'
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class Product(models.Model):
    """二手商品模型

    记录二手商品的基本信息、价格、成色、状态等。
    """

    class Condition(models.TextChoices):
        BRAND_NEW = 'brand_new', '全新'
        LIKE_NEW = 'like_new', '九成新'
        GOOD = 'good', '八成新'
        FAIR = 'fair', '七成新及以下'

    class Status(models.TextChoices):
        ON_SALE = 'on_sale', '在售'
        RESERVED = 'reserved', '已预订'
        SOLD = 'sold', '已售出'
        OFF_SHELF = 'off_shelf', '已下架'

    title = models.CharField('商品标题', max_length=100)
    description = models.TextField('商品描述', blank=True, default='')
    price = models.DecimalField(
        '价格',
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive_price]
    )
    condition = models.CharField(
        '成色',
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD
    )
    status = models.CharField(
        '状态',
        max_length=20,
        choices=Status.choices,
        default=Status.ON_SALE
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='卖家'
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        related_name='products',
        verbose_name='分类',
        null=True,
        blank=True
    )
    view_count = models.PositiveIntegerField('浏览量', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '二手商品'
        verbose_name_plural = '二手商品'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """商品图片模型

    每个商品可关联多张图片（最多9张）。
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='商品'
    )
    image = models.ImageField(
        '图片',
        upload_to=product_upload_path
    )

    class Meta:
        verbose_name = '商品图片'
        verbose_name_plural = '商品图片'

    def __str__(self):
        return f"{self.product.title} - 图片{self.pk}"


@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    """删除商品图片记录时同步清理物理文件，避免孤儿文件残留"""
    if instance.image:
        instance.image.delete(save=False)


class ProductComment(models.Model):
    """商品评论模型

    用户可以对二手商品进行评论/留言。
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='商品'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_comments',
        verbose_name='评论者'
    )
    content = models.TextField('评论内容', max_length=500)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '商品评论'
        verbose_name_plural = '商品评论'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username} 评论 {self.product.title}"
