"""
自由发言模块 Django Admin 配置
"""
from django.contrib import admin
from .models import Post, PostImage, Comment, PostLike


class PostImageInline(admin.TabularInline):
    """帖子图片内联编辑"""
    model = PostImage
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """帖子管理后台"""
    list_display = [
        'title', 'author', 'post_type', 'is_top', 'is_featured',
        'view_count', 'like_count', 'comment_count', 'created_at'
    ]
    list_filter = ['post_type', 'is_top', 'is_featured', 'created_at']
    search_fields = ['title', 'content', 'tags']
    list_editable = ['is_top', 'is_featured']
    inlines = [PostImageInline]
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """评论管理后台"""
    list_display = ['post', 'author', 'content_preview', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username']
    
    @admin.display(description='评论内容')
    def content_preview(self, obj):
        """评论内容预览（截取前50字）"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
