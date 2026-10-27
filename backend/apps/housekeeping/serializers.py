"""
家政服务模块序列化器

提供服务分类、服务提供者、服务项目、预约订单、服务评价的序列化。
"""
from rest_framework import serializers
from django.utils import timezone
from apps.users.serializers import UserSimpleSerializer
from common.validators import validate_image
from .models import (
    ServiceCategory, ServiceProvider, ServiceItem,
    Booking, ServiceReview
)


class ServiceCategorySerializer(serializers.ModelSerializer):
    """服务分类序列化器"""

    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'slug', 'icon', 'sort_order']
        read_only_fields = fields


class ServiceItemSerializer(serializers.ModelSerializer):
    """服务项目序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    provider_name = serializers.CharField(source='provider.name', read_only=True)

    class Meta:
        model = ServiceItem
        fields = [
            'id', 'provider', 'provider_name', 'category', 'category_name',
            'title', 'description', 'price_min', 'price_max', 'duration'
        ]
        read_only_fields = ['id', 'provider', 'provider_name', 'category_name']


class ServiceReviewSerializer(serializers.ModelSerializer):
    """服务评价序列化器（含用户信息）"""
    user_info = UserSimpleSerializer(source='user', read_only=True)

    class Meta:
        model = ServiceReview
        fields = [
            'id', 'booking', 'user', 'user_info', 'provider',
            'rating', 'content', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'provider', 'created_at']


class ServiceReviewCreateSerializer(serializers.ModelSerializer):
    """服务评价创建序列化器"""

    class Meta:
        model = ServiceReview
        fields = ['rating', 'content']

    def validate_rating(self, value):
        """验证评分范围"""
        if value < 1 or value > 5:
            raise serializers.ValidationError('评分必须在 1 到 5 之间')
        return value


class ServiceProviderListSerializer(serializers.ModelSerializer):
    """服务提供者列表序列化器（含分类列表和服务数量）"""
    categories = serializers.SerializerMethodField()
    service_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'name', 'service_area', 'description',
            'phone', 'avg_rating', 'review_count',
            'categories', 'service_count', 'created_at'
        ]
        read_only_fields = fields

    def get_categories(self, obj):
        """获取服务提供者涉及的所有分类

        基于视图层 prefetch 的 services__category 聚合，避免列表逐条查询。
        """
        categories = {}
        for item in obj.services.all():
            if item.category_id not in categories:
                categories[item.category_id] = item.category
        return ServiceCategorySerializer(list(categories.values()), many=True).data

    def get_service_count(self, obj):
        """获取服务提供者的服务项目数量（命中 prefetch 缓存）"""
        return len(obj.services.all())


class ServiceProviderDetailSerializer(serializers.ModelSerializer):
    """服务提供者详情序列化器（含服务列表和近期评价）"""
    services = ServiceItemSerializer(many=True, read_only=True)
    recent_reviews = serializers.SerializerMethodField()

    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'name', 'service_area', 'description',
            'qualification_image', 'phone', 'status',
            'avg_rating', 'review_count',
            'services', 'recent_reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_recent_reviews(self, obj):
        """获取最近的评价（最多5条）"""
        reviews = obj.reviews.all()[:5]
        return ServiceReviewSerializer(reviews, many=True).data


class ServiceProviderApplySerializer(serializers.ModelSerializer):
    """服务提供者申请序列化器"""
    qualification_image = serializers.ImageField(
        required=False, allow_null=True, validators=[validate_image],
        help_text='资质图片，不超过5MB，仅支持 jpg/jpeg/png/webp'
    )

    class Meta:
        model = ServiceProvider
        fields = ['name', 'service_area', 'description', 'qualification_image', 'phone']


class BookingSerializer(serializers.ModelSerializer):
    """预约订单序列化器（含服务项目和提供者信息）"""
    service_item_info = ServiceItemSerializer(source='service_item', read_only=True)
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'service_item', 'service_item_info',
            'provider', 'provider_name', 'preferred_date',
            'preferred_time', 'status', 'status_display',
            'remark', 'created_at', 'updated_at'
        ]
        # service_item 必须只读：update 时若允许改 service_item 而 provider 只读，
        # 会制造 booking.service_item.provider != booking.provider 的数据不一致
        # （订单/评价归属错乱）。如需改服务项应重新下单。
        read_only_fields = [
            'id', 'user', 'service_item', 'provider',
            'status', 'created_at', 'updated_at'
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """预约订单创建序列化器"""

    class Meta:
        model = Booking
        fields = ['service_item', 'preferred_date', 'preferred_time', 'remark']

    def validate_preferred_date(self, value):
        """预约日期不能早于今天"""
        if value < timezone.localdate():
            raise serializers.ValidationError('预约日期不能早于今天')
        return value

    def validate_service_item(self, value):
        """验证服务项目对应的提供者已通过审核"""
        if value.provider.status != ServiceProvider.Status.APPROVED:
            raise serializers.ValidationError('该服务提供者尚未通过审核，暂时无法预约')
        return value
