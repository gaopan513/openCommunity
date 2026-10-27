"""
二手市场模块序列化器

提供商品分类、商品列表、商品详情、商品创建、商品评论的序列化。
"""
from rest_framework import serializers
from django.db import transaction
from apps.users.serializers import UserSimpleSerializer
from common.validators import validate_image
from .models import ProductCategory, Product, ProductImage, ProductComment


class ProductCategorySerializer(serializers.ModelSerializer):
    """商品分类序列化器"""

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'slug', 'sort_order']
        read_only_fields = fields


class ProductImageSerializer(serializers.ModelSerializer):
    """商品图片序列化器"""

    class Meta:
        model = ProductImage
        fields = ['id', 'image']
        read_only_fields = ['id']


class ProductCommentSerializer(serializers.ModelSerializer):
    """商品评论序列化器

    包含评论者的简要信息。
    """
    author_info = UserSimpleSerializer(source='author', read_only=True)

    class Meta:
        model = ProductComment
        fields = ['id', 'product', 'author', 'author_info', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'author_info', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """商品列表序列化器

    用于列表页展示，包含卖家信息、图片数量和首图。
    """
    seller_info = UserSimpleSerializer(source='seller', read_only=True)
    image_count = serializers.SerializerMethodField()
    first_image = serializers.SerializerMethodField()
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'condition',
            'condition_display', 'status', 'status_display',
            'seller', 'seller_info', 'category', 'view_count',
            'image_count', 'first_image', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_image_count(self, obj):
        """获取商品图片数量"""
        return obj.images.count()

    def get_first_image(self, obj):
        """获取商品首图 URL"""
        first = obj.images.first()
        if first and first.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first.image.url)
            return first.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """商品详情序列化器

    包含完整的图片列表、评论列表和卖家信息。
    """
    seller_info = UserSimpleSerializer(source='seller', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    comments = ProductCommentSerializer(many=True, read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'condition',
            'condition_display', 'status', 'status_display',
            'seller', 'seller_info', 'category', 'view_count',
            'images', 'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class ProductCreateSerializer(serializers.ModelSerializer):
    """商品创建/更新序列化器

    支持同时上传多张图片（最多9张）。
    """
    images = serializers.ListField(
        child=serializers.ImageField(validators=[validate_image]),
        max_length=9,
        required=False,
        write_only=True,
        help_text='商品图片列表，最多9张，单张不超过5MB，仅支持 jpg/jpeg/png/webp'
    )

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'condition',
            'status', 'category', 'images'
        ]
        # status 必须只读，卖家不得通过 update 绕过 change_status @action 的状态机
        # （否则 sold 可直接改回 on_sale）。状态变更只能走 /products/<pk>/change_status/。
        read_only_fields = ['id', 'status']

    def validate_price(self, value):
        """验证价格必须大于0"""
        if value <= 0:
            raise serializers.ValidationError('价格必须大于0')
        return value

    def validate_images(self, value):
        """验证图片数量不超过9张"""
        if len(value) > 9:
            raise serializers.ValidationError('最多上传9张图片')
        return value

    def create(self, validated_data):
        """创建商品及关联图片"""
        images_data = validated_data.pop('images', [])
        with transaction.atomic():
            product = Product.objects.create(**validated_data)
            ProductImage.objects.bulk_create(
                [ProductImage(product=product, image=image) for image in images_data]
            )
        return product

    def update(self, instance, validated_data):
        """更新商品信息

        传入 images 时为全量替换语义（删除旧图后写入新图，总数受 ≤9 校验约束）；
        未传 images 字段时保持原有图片不变。
        """
        images_data = validated_data.pop('images', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        with transaction.atomic():
            instance.save()
            if images_data is not None:
                # 删除旧图记录（post_delete 信号同步清理物理文件）再批量建新
                instance.images.all().delete()
                ProductImage.objects.bulk_create(
                    [ProductImage(product=instance, image=image) for image in images_data]
                )
        return instance
