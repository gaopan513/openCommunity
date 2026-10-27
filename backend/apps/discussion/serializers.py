"""
自由发言模块序列化器

提供帖子和评论的请求/响应数据序列化。
"""
from rest_framework import serializers
from django.db import transaction
from .models import Post, PostImage, Comment, PostLike
from apps.users.serializers import UserSimpleSerializer
from common.validators import validate_image


class PostImageSerializer(serializers.ModelSerializer):
    """帖子图片序列化器"""
    
    class Meta:
        model = PostImage
        fields = ['id', 'image']


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器
    
    包含作者信息和楼中楼回复列表。
    """
    author_info = UserSimpleSerializer(source='author', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'author_info', 'content',
            'parent', 'like_count', 'replies', 'created_at'
        ]
        read_only_fields = ['id', 'author', 'like_count', 'created_at']
    
    def get_replies(self, obj):
        """获取楼中楼回复（仅一级）"""
        if obj.parent is None:
            replies = obj.replies.all()[:5]
            return CommentSerializer(replies, many=True).data
        return []


class PostListSerializer(serializers.ModelSerializer):
    """帖子列表序列化器（轻量版）

    用于列表页展示，不包含完整评论内容。
    注意：is_top/is_featured/author/post_type/计数字段在 update 时不得可写，
    否则作者可绕过管理员动作和 notice 类型限制、伪造统计数据。
    """
    author_info = UserSimpleSerializer(source='author', read_only=True)
    image_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'author_info',
            'post_type', 'tags', 'is_top', 'is_featured',
            'view_count', 'like_count', 'comment_count',
            'image_count', 'is_liked', 'created_at'
        ]
        # 作者更新帖子时仅允许改 title/content/tags；其余字段强制只读，
        # 防止绕过 feature（管理员置顶/加精）与 notice 类型限制、伪造计数。
        read_only_fields = [
            'id', 'author', 'post_type', 'is_top', 'is_featured',
            'view_count', 'like_count', 'comment_count', 'created_at'
        ]

    def get_image_count(self, obj):
        """获取图片数量"""
        return obj.images.count()

    def get_is_liked(self, obj):
        """当前用户是否已点赞（命中 prefetch 缓存时不再逐条查库）"""
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            return False
        if 'likes' in getattr(obj, '_prefetched_objects_cache', {}):
            return any(like.user_id == request.user.id for like in obj.likes.all())
        return obj.likes.filter(user=request.user).exists()


class PostDetailSerializer(serializers.ModelSerializer):
    """帖子详情序列化器（完整版）
    
    包含图片列表和热门评论。
    """
    author_info = UserSimpleSerializer(source='author', read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'author_info',
            'post_type', 'tags', 'is_top', 'is_featured',
            'view_count', 'like_count', 'comment_count',
            'images', 'comments', 'is_liked',
            'created_at', 'updated_at'
        ]
    
    def get_comments(self, obj):
        """获取顶级评论列表（最新20条）

        在同一查询内 select_related(author) + prefetch_related('replies__author')，
        序列化时 CommentSerializer.get_replies 命中缓存，固定 2 次 SQL，
        与评论数量无关（原实现逐条查询，约 100+ 次）。
        """
        comments = (
            obj.comments.filter(parent=None)
            .select_related('author')
            .prefetch_related('replies__author')
            .order_by('-created_at')[:20]
        )
        return CommentSerializer(comments, many=True, context=self.context).data
    
    def get_is_liked(self, obj):
        """当前用户是否已点赞（命中 prefetch 缓存时不再逐条查库）"""
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            return False
        if 'likes' in getattr(obj, '_prefetched_objects_cache', {}):
            return any(like.user_id == request.user.id for like in obj.likes.all())
        return obj.likes.filter(user=request.user).exists()


class PostCreateSerializer(serializers.ModelSerializer):
    """帖子创建序列化器
    
    支持同时上传图片。
    """
    images = serializers.ListField(
        child=serializers.ImageField(validators=[validate_image]),
        max_length=9,
        required=False,
        write_only=True,
        help_text='帖子图片，最多9张，单张不超过5MB，仅支持 jpg/jpeg/png/webp'
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'post_type', 'tags', 'images']
    
    def validate_post_type(self, value):
        """普通用户不能发布公告类型"""
        request = self.context.get('request')
        if value == Post.PostType.NOTICE:
            if not request or getattr(request.user, 'role', None) != 'admin':
                raise serializers.ValidationError('仅管理员可发布公告')
        return value
    
    def create(self, validated_data):
        """创建帖子并关联图片（主记录与图片原子写入）"""
        images = validated_data.pop('images', [])
        with transaction.atomic():
            post = Post.objects.create(**validated_data)

            # 批量创建图片记录
            for image in images:
                PostImage.objects.create(post=post, image=image)

        return post
