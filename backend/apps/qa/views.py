"""
经验问答模块视图

提供问题 CRUD、回答、采纳、点赞等接口。
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db import transaction
from django.db.models import F, Q
from django_filters.rest_framework import DjangoFilterBackend

from common.permissions import IsOwnerOrAdmin
from common.response import success_response, created_response, error_response, list_response, no_content_response
from common.pagination import StandardPagination
from common.utils import toggle_like
from .models import Question, Answer, QuestionLike, AnswerLike
from .serializers import (
    QuestionListSerializer, QuestionDetailSerializer,
    QuestionCreateSerializer, AnswerSerializer, AnswerCreateSerializer
)


class QuestionViewSet(viewsets.ModelViewSet):
    """问题视图集
    
    提供问题的完整 CRUD 和互动功能：
    - list: 问题列表（支持标签筛选、搜索、排序）
    - create: 提问
    - retrieve: 问题详情（自动增加浏览量）
    - destroy: 删除问题（作者或管理员）
    - answer: 回答问题
    - accept: 采纳回答（仅提问者）
    - like: 点赞/取消点赞问题
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filterset_fields = ['is_solved']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'view_count', 'like_count']
    ordering = ['-is_solved', '-created_at']
    
    def get_queryset(self):
        """获取问题列表，支持标签筛选，预加载关联数据

        - likes：列表/详情序列化 is_liked 命中 prefetch 缓存，避免每行一次查询
        - retrieve 时额外预取回答的作者与点赞（详情页嵌套回答列表）
        """
        queryset = Question.objects.select_related('author').prefetch_related('tags', 'likes')
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('answers__author', 'answers__likes')

        # 按标签筛选
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__slug=tag)

        return queryset
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return QuestionCreateSerializer
        elif self.action == 'retrieve':
            return QuestionDetailSerializer
        return QuestionListSerializer
    
    def get_permissions(self):
        """删除操作需要所有者或管理员权限"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """创建问题时关联当前用户"""
        serializer.save(author=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """问题列表"""
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
    
    def retrieve(self, request, *args, **kwargs):
        """获取问题详情，同时增加浏览量"""
        instance = self.get_object()
        # 浏览量 +1
        Question.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)
    
    def create(self, request, *args, **kwargs):
        """提问"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 返回完整问题信息
        question = Question.objects.prefetch_related('tags').get(pk=serializer.instance.pk)
        output_serializer = QuestionDetailSerializer(question, context={'request': request})
        return created_response(data=output_serializer.data, message='提问成功')

    def update(self, request, *args, **kwargs):
        """编辑问题（作者或管理员，仅可改 title/content）"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, '更新成功')

    def destroy(self, request, *args, **kwargs):
        """删除问题（作者或管理员）"""
        instance = self.get_object()
        instance.delete()
        return no_content_response('删除成功')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def answer(self, request, pk=None):
        """回答问题
        
        请求体：
            content: 回答内容
        """
        question = self.get_object()
        
        serializer = AnswerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 回答与问题回答数是两步写，包事务避免计数失真
        with transaction.atomic():
            answer = Answer.objects.create(
                question=question,
                author=request.user,
                content=serializer.validated_data['content']
            )

            # 更新问题回答数
            Question.objects.filter(pk=question.pk).update(answer_count=F('answer_count') + 1)
        
        output_serializer = AnswerSerializer(answer, context={'request': request})
        return created_response(data=output_serializer.data, message='回答成功')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        """采纳回答（仅提问者可操作）
        
        请求体：
            answer_id: 要采纳的回答 ID
        """
        question = self.get_object()
        
        # 仅提问者可采纳
        if question.author != request.user:
            return error_response('仅提问者可采纳回答', code=40300, http_status=403)
        
        answer_id = request.data.get('answer_id')
        if not answer_id:
            return error_response('请指定要采纳的回答', code=40001)
        
        try:
            answer = Answer.objects.get(pk=answer_id, question=question)
        except Answer.DoesNotExist:
            return error_response('回答不存在', code=40004)
        
        # 取消旧采纳 → 采纳新回答 → 标记问题已解决，三步写必须原子完成，
        # 部分失败会出现"旧采纳已取消但新采纳未生效"的中间态
        with transaction.atomic():
            question.answers.filter(is_accepted=True).update(is_accepted=False)

            answer.is_accepted = True
            answer.save(update_fields=['is_accepted'])

            question.is_solved = True
            question.save(update_fields=['is_solved'])
        
        output_serializer = AnswerSerializer(answer, context={'request': request})
        return success_response(data=output_serializer.data, message='采纳成功')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """点赞/取消点赞问题

        通过 QuestionLike 记录配合 like_count 冗余计数；
        并发首赞/取消的原子处理统一收敛在 common.utils.toggle_like。
        """
        question = self.get_object()
        liked, like_count = toggle_like(QuestionLike, question, request.user, 'question')
        return success_response(
            data={'liked': liked, 'like_count': like_count},
            message='点赞成功' if liked else '已取消点赞'
        )

    @action(detail=True, methods=['post'],
            url_path=r'answers/(?P<answer_pk>\d+)/like',
            permission_classes=[IsAuthenticated])
    def answer_like(self, request, pk=None, answer_pk=None):
        """回答点赞/取消点赞

        POST /questions/<pk>/answers/<answer_pk>/like/
        回答必须属于当前问题；已点赞再调用为取消。
        """
        question = self.get_object()
        try:
            answer = Answer.objects.get(pk=answer_pk, question=question)
        except Answer.DoesNotExist:
            return error_response('回答不存在', code=40004, http_status=404)

        liked, like_count = toggle_like(AnswerLike, answer, request.user, 'answer')
        return success_response(
            data={'liked': liked, 'like_count': like_count},
            message='点赞成功' if liked else '已取消点赞'
        )
