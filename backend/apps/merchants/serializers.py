"""
商家模块序列化器

提供商家分类、商家信息、活动、评价的序列化与反序列化。
"""
from rest_framework import serializers

from apps.users.serializers import UserSimpleSerializer
from common.validators import validate_image
from .models import MerchantCategory, Merchant, MerchantImage, Activity, MerchantReview


class MerchantCategorySerializer(serializers.ModelSerializer):
    """商家分类序列化器"""

    class Meta:
        model = MerchantCategory
        fields = '__all__'


class MerchantImageSerializer(serializers.ModelSerializer):
    """商家图片序列化器"""

    class Meta:
        model = MerchantImage
        fields = ['id', 'image', 'created_at']
        read_only_fields = fields


class ActivitySerializer(serializers.ModelSerializer):
    """商家活动序列化器（含 is_active 状态）"""
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['id', 'merchant', 'created_at']


class ActivityCreateSerializer(serializers.ModelSerializer):
    """商家活动创建序列化器"""

    # 重声明以接入统一图片校验（≤5MB、jpg/jpeg/png/webp），与其他图片入口对齐
    image = serializers.ImageField(
        required=False, allow_null=True, validators=[validate_image],
        help_text='活动图片，不超过5MB，仅支持 jpg/jpeg/png/webp'
    )

    class Meta:
        model = Activity
        fields = ['title', 'description', 'image', 'start_time', 'end_time', 'discount_info']

    def validate(self, attrs):
        """校验活动时间区间：结束时间必须晚于开始时间"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError('活动结束时间必须晚于开始时间')
        return attrs


class MerchantReviewSerializer(serializers.ModelSerializer):
    """商家评价序列化器（含用户信息）"""
    user_info = UserSimpleSerializer(source='user', read_only=True)

    class Meta:
        model = MerchantReview
        fields = [
            'id', 'merchant', 'user', 'user_info',
            'rating', 'content', 'reply', 'replied_at', 'created_at'
        ]
        read_only_fields = ['id', 'merchant', 'user', 'reply', 'replied_at', 'created_at']


class MerchantReviewCreateSerializer(serializers.ModelSerializer):
    """商家评价创建序列化器"""

    class Meta:
        model = MerchantReview
        fields = ['rating', 'content']


class MerchantListSerializer(serializers.ModelSerializer):
    """商家列表序列化器"""
    category = MerchantCategorySerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default='')

    class Meta:
        model = Merchant
        fields = [
            'id', 'name', 'category', 'category_name',
            'address', 'phone', 'business_hours',
            'status', 'avg_rating', 'review_count', 'created_at',
            'logo',
        ]
        read_only_fields = fields


class MerchantDetailSerializer(serializers.ModelSerializer):
    """商家详情序列化器（含图片、活动、评价）"""
    category = MerchantCategorySerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    images = MerchantImageSerializer(many=True, read_only=True)
    activities = ActivitySerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = [
            'id', 'user', 'name', 'category', 'category_name',
            'address', 'phone', 'business_hours', 'description',
            'logo', 'license_image', 'status', 'avg_rating', 'review_count',
            'images', 'activities', 'reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_reviews(self, obj):
        """获取最近5条评价"""
        reviews = obj.reviews.all()[:5]
        return MerchantReviewSerializer(reviews, many=True).data


class MerchantApplySerializer(serializers.ModelSerializer):
    """商家入驻申请序列化器

    logo/license_image 重新声明以接入 validate_image（大小≤5MB、格式白名单），
    与模型层 blank=True/null=True 语义保持一致。
    """
    logo = serializers.ImageField(
        required=False, allow_null=True, validators=[validate_image],
        help_text='店铺 Logo，不超过5MB，仅支持 jpg/jpeg/png/webp'
    )
    license_image = serializers.ImageField(
        required=False, allow_null=True, validators=[validate_image],
        help_text='营业执照，不超过5MB，仅支持 jpg/jpeg/png/webp'
    )

    class Meta:
        model = Merchant
        fields = [
            'name', 'category', 'address', 'phone',
            'business_hours', 'description', 'logo', 'license_image'
        ]
