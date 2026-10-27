"""
经验问答模块序列化器

提供问题和回答的请求/响应数据序列化。
"""
from rest_framework import serializers
from django.utils.text import slugify
from .models import QuestionTag, Question, Answer
from apps.users.serializers import UserSimpleSerializer


class QuestionTagSerializer(serializers.ModelSerializer):
    """问题标签序列化器"""
    
    class Meta:
        model = QuestionTag
        fields = ['id', 'name', 'slug']


class AnswerSerializer(serializers.ModelSerializer):
    """回答序列化器
    
    包含作者信息。
    """
    author_info = UserSimpleSerializer(source='author', read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = [
            'id', 'question', 'author', 'author_info', 'content',
            'is_accepted', 'like_count', 'is_liked', 'created_at'
        ]
        read_only_fields = ['id', 'author', 'is_accepted', 'like_count', 'created_at']
    
    def get_is_liked(self, obj):
        """当前用户是否已点赞（命中 prefetch 缓存时不再逐条查库）"""
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            return False
        if 'likes' in getattr(obj, '_prefetched_objects_cache', {}):
            return any(like.user_id == request.user.id for like in obj.likes.all())
        return obj.likes.filter(user=request.user).exists()


class QuestionListSerializer(serializers.ModelSerializer):
    """问题列表序列化器（轻量版）

    用于列表页展示，包含作者信息和标签。
    注意：author/is_solved/计数字段在 update 时不得可写，否则提问者可绕过
    accept @action 的采纳逻辑、改问题归属、伪造热度数据。
    """
    author_info = UserSimpleSerializer(source='author', read_only=True)
    tags = QuestionTagSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id', 'title', 'content', 'author', 'author_info',
            'tags', 'is_solved', 'view_count', 'like_count',
            'answer_count', 'is_liked', 'created_at', 'updated_at'
        ]
        # 提问者更新问题时仅允许改 title/content；其余字段强制只读，
        # 防止绕过 accept（仅提问者可采纳）逻辑、改问题归属、伪造计数。
        read_only_fields = [
            'id', 'author', 'is_solved',
            'view_count', 'like_count', 'answer_count',
            'created_at', 'updated_at'
        ]

    def get_is_liked(self, obj):
        """当前用户是否已点赞（命中 prefetch 缓存时不再逐条查库）"""
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            return False
        if 'likes' in getattr(obj, '_prefetched_objects_cache', {}):
            return any(like.user_id == request.user.id for like in obj.likes.all())
        return obj.likes.filter(user=request.user).exists()


class QuestionDetailSerializer(serializers.ModelSerializer):
    """问题详情序列化器（完整版）
    
    包含回答列表和标签信息。
    """
    author_info = UserSimpleSerializer(source='author', read_only=True)
    tags = QuestionTagSerializer(many=True, read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'title', 'content', 'author', 'author_info',
            'tags', 'is_solved', 'view_count', 'like_count',
            'answer_count', 'answers', 'is_liked', 'created_at', 'updated_at'
        ]

    def get_is_liked(self, obj):
        """当前用户是否已点赞（命中 prefetch 缓存时不再逐条查库）"""
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            return False
        if 'likes' in getattr(obj, '_prefetched_objects_cache', {}):
            return any(like.user_id == request.user.id for like in obj.likes.all())
        return obj.likes.filter(user=request.user).exists()


class QuestionCreateSerializer(serializers.ModelSerializer):
    """问题创建序列化器
    
    支持通过标签名称列表创建/关联标签。
    """
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True,
        help_text='标签名称列表，不存在则自动创建'
    )
    
    class Meta:
        model = Question
        fields = ['title', 'content', 'tags']
    
    def create(self, validated_data):
        """创建问题并关联标签（不存在则创建）"""
        tag_names = validated_data.pop('tags', [])
        question = Question.objects.create(**validated_data)
        
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            slug = slugify(name, allow_unicode=True)
            if not slug:
                slug = name
            tag, _ = QuestionTag.objects.get_or_create(
                slug=slug,
                defaults={'name': name}
            )
            question.tags.add(tag)
        
        return question


class AnswerCreateSerializer(serializers.ModelSerializer):
    """回答创建序列化器
    
    仅接受内容字段。
    """
    
    class Meta:
        model = Answer
        fields = ['content']
