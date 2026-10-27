"""
二手市场模块后台管理配置
"""
from django.contrib import admin
from .models import Product, ProductCategory, ProductComment, ProductImage


class ProductImageInline(admin.TabularInline):
    """商品图片内联编辑"""
    model = ProductImage
    extra = 1


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """商品分类管理"""
    list_display = ['id', 'name', 'slug', 'sort_order']
    search_fields = ['name', 'slug']
    ordering = ['sort_order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """二手商品管理"""
    list_display = [
        'id', 'title', 'price', 'condition', 'status',
        'seller', 'category', 'view_count', 'created_at'
    ]
    list_filter = ['status', 'condition', 'category', 'created_at']
    search_fields = ['title', 'description']
    raw_id_fields = ['seller']
    inlines = [ProductImageInline]
    readonly_fields = ['view_count', 'created_at', 'updated_at']


@admin.register(ProductComment)
class ProductCommentAdmin(admin.ModelAdmin):
    """商品评论管理"""
    list_display = ['id', 'product', 'author', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content']
    raw_id_fields = ['product', 'author']
    readonly_fields = ['created_at']
