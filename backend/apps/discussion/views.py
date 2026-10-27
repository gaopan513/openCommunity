"""
自由发言模块视图

提供帖子 CRUD、评论、点赞、管理操作等接口。
"""
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db import transaction
from django.db.models import F, Q
from django_filters.rest_framework import DjangoFilterBackend

from common.permissions import IsOwnerOrAdmin, IsAdminUser
from common.response import success_response, created_response, error_response, list_response, no_content_response
from common.pagination import StandardPagination, SmallPagination
from common.utils import toggle_like
from .models import Post, Comment, PostLike
from .serializers import (
    PostListSerializer, PostDetailSerializer,
    PostCreateSerializer, CommentSerializer
)


class PostViewSet(viewsets.ModelViewSet):
    """帖子视图集
    
    提供帖子的完整 CRUD 和互动功能：
    - list: 帖子列表（支持筛选、搜索、排序）
    - create: 发布帖子
    - retrieve: 帖子详情（自动增加浏览量）
    - update/partial_update: 编辑帖子（作者或管理员）
    - destroy: 删除帖子（作者或管理员）
    - like: 点赞/取消点赞
    - comments: 获取/发表评论
    - feature: 置顶/加精（管理员）
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filterset_fields = ['post_type', 'is_top', 'is_featured']
    search_fields = ['title', 'content', 'tags']
    ordering_fields = ['created_at', 'view_count', 'like_count', 'comment_count']
    ordering = ['-is_top', '-created_at']
    
    def get_queryset(self):
        """获取帖子列表，预加载关联数据"""
        return Post.objects.select_related('author').prefetch_related('images', 'likes')
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer
    
    def get_permissions(self):
        """编辑/删除操作需要所有者或管理员权限"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        if self.action == 'feature':
            return [IsAdminUser()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """创建帖子时关联当前用户"""
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """获取帖子详情，同时增加浏览量"""
        instance = self.get_object()
        # 浏览量 +1
        Post.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)
    
    def list(self, request, *args, **kwargs):
        """帖子列表"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return list_response(
                results=serializer.data,
                total=self.paginator.page.paginator.count,
                page=self.paginator.page.number,
                page_size=self.paginator.get_page_size(request),
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)
    
    def create(self, request, *args, **kwargs):
        """发布帖子"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 返回完整帖子信息
        post = Post.objects.get(pk=serializer.instance.pk)
        output_serializer = PostDetailSerializer(post, context={'request': request})
        return created_response(data=output_serializer.data, message='发布成功')

    def update(self, request, *args, **kwargs):
        """编辑帖子（作者或管理员，post_type/置顶/加精等字段只读）"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, '更新成功')

    def destroy(self, request, *args, **kwargs):
        """删除帖子（作者或管理员）"""
        instance = self.get_object()
        instance.delete()
        return no_content_response('删除成功')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """点赞/取消点赞

        如果已点赞则取消，未点赞则添加。
        并发首赞/取消的原子处理统一收敛在 common.utils.toggle_like。
        """
        post = self.get_object()
        liked, like_count = toggle_like(PostLike, post, request.user, 'post')
        return success_response(
            data={'liked': liked, 'like_count': like_count},
            message='点赞成功' if liked else '已取消点赞'
        )
    
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """获取或发表评论
        
        GET: 获取帖子的评论列表
        POST: 发表评论（需登录）
        """
        post = self.get_object()
        
        if request.method == 'GET':
            comments = post.comments.filter(parent=None).select_related('author').prefetch_related('replies__author')
            paginator = SmallPagination()
            page = paginator.paginate_queryset(comments, request)
            serializer = CommentSerializer(page, many=True)
            return list_response(
                results=serializer.data,
                total=paginator.page.paginator.count,
                page=paginator.page.number,
                page_size=paginator.get_page_size(request),
            )
        
        # POST: 发表评论
        if not request.user.is_authenticated:
            return error_response('请先登录再评论', code=40100, http_status=401)
        
        content = request.data.get('content', '').strip()
        parent_id = request.data.get('parent')
        
        if not content:
            return error_response('评论内容不能为空', code=40001)
        if len(content) > 2000:
            return error_response('评论内容不能超过2000字', code=40005)
        
        # 验证父评论存在且属于同一帖子
        parent = None
        if parent_id:
            try:
                parent = Comment.objects.get(pk=parent_id, post=post)
            except Comment.DoesNotExist:
                return error_response('回复的评论不存在', code=40004)
        
        # 评论与帖子评论数是两步写，包事务避免计数失真
        with transaction.atomic():
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                parent=parent
            )

            # 更新帖子评论数
            Post.objects.filter(pk=post.pk).update(comment_count=F('comment_count') + 1)
        
        serializer = CommentSerializer(comment)
        return created_response(data=serializer.data, message='评论成功')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAdminUser])
    def feature(self, request, pk=None):
        """置顶/加精操作（管理员）
        
        请求体：
            is_top: bool（可选）
            is_featured: bool（可选）
        """
        post = self.get_object()

        # 显式类型校验，防止字符串 "false" 被当作真值
        bool_field = serializers.BooleanField()
        if 'is_top' in request.data:
            post.is_top = bool_field.run_validation(request.data['is_top'])
        if 'is_featured' in request.data:
            post.is_featured = bool_field.run_validation(request.data['is_featured'])
        
        post.save()
        serializer = PostListSerializer(post, context={'request': request})
        return success_response(data=serializer.data, message='操作成功')
