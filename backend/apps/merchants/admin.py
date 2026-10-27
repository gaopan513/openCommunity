"""
商家模块 Django Admin 配置

注册商家、分类、图片、活动、评价模型，提供管理界面。
管理员在此处审核商家入驻申请。
"""
from django.contrib import admin
from .models import MerchantCategory, Merchant, MerchantImage, Activity, MerchantReview


class MerchantImageInline(admin.TabularInline):
    """商家图片内联编辑"""
    model = MerchantImage
    extra = 0
    readonly_fields = ['created_at']


@admin.register(MerchantCategory)
class MerchantCategoryAdmin(admin.ModelAdmin):
    """商家分类管理"""
    list_display = ['id', 'name', 'slug', 'icon', 'sort_order']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order']


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    """商家管理后台

    管理员在此审核商家入驻申请（修改 status 字段）。
    """
    list_display = [
        'id', 'name', 'user', 'category', 'phone',
        'status', 'avg_rating', 'review_count', 'created_at'
    ]
    list_filter = ['status', 'category', 'created_at']
    list_editable = ['status']
    search_fields = ['name', 'user__username', 'phone', 'address']
    raw_id_fields = ['user', 'category']
    inlines = [MerchantImageInline]
    readonly_fields = ['avg_rating', 'review_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """商家活动管理"""
    list_display = [
        'id', 'title', 'merchant', 'start_time', 'end_time', 'created_at'
    ]
    list_filter = ['created_at', 'start_time']
    search_fields = ['title', 'description', 'merchant__name']
    raw_id_fields = ['merchant']
    readonly_fields = ['created_at']


@admin.register(MerchantReview)
class MerchantReviewAdmin(admin.ModelAdmin):
    """商家评价管理"""
    list_display = [
        'id', 'merchant', 'user', 'rating', 'replied_at', 'created_at'
    ]
    list_filter = ['rating', 'created_at']
    search_fields = ['content', 'merchant__name', 'user__username']
    raw_id_fields = ['merchant', 'user']
    readonly_fields = ['created_at']
