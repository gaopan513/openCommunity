"""
家政服务模块后台管理配置

注册所有模型到 Django Admin，提供管理界面。
"""
from django.contrib import admin
from .models import (
    ServiceCategory, ServiceProvider, ServiceItem,
    Booking, ServiceReview
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """服务分类管理"""
    list_display = ['id', 'name', 'slug', 'sort_order']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ServiceItemInline(admin.TabularInline):
    """服务项目内联（在提供者详情中展示）"""
    model = ServiceItem
    extra = 0
    fields = ['category', 'title', 'price_min', 'price_max', 'duration']


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    """服务提供者管理"""
    list_display = [
        'id', 'name', 'user', 'phone', 'status',
        'avg_rating', 'review_count', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'user__username', 'phone']
    inlines = [ServiceItemInline]
    readonly_fields = ['avg_rating', 'review_count', 'created_at', 'updated_at']


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    """服务项目管理"""
    list_display = ['id', 'title', 'provider', 'category', 'price_min', 'price_max', 'duration']
    list_filter = ['category']
    search_fields = ['title', 'provider__name']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """预约订单管理"""
    list_display = [
        'id', 'user', 'service_item', 'provider',
        'preferred_date', 'preferred_time', 'status', 'created_at'
    ]
    list_filter = ['status', 'preferred_date', 'created_at']
    search_fields = ['user__username', 'provider__name', 'service_item__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    """服务评价管理"""
    list_display = ['id', 'user', 'provider', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'provider__name', 'content']
    readonly_fields = ['created_at']
