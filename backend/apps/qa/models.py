"""
经验问答模块数据模型

包含问题标签、问题、回答、回答点赞四个核心模型。
"""
from django.db import models
from django.conf import settings


class QuestionTag(models.Model):
    """问题标签模型
    
    用于对问题进行分类标记。
    """
    name = models.CharField('标签名称', max_length=50)
    slug = models.SlugField('标签标识', max_length=50, unique=True)
    
    class Meta:
        verbose_name = '问题标签'
        verbose_name_plural = '问题标签'
    
    def __str__(self):
        return self.name


class Question(models.Model):
    """问题模型
    
    经验问答板块的核心实体，支持标签分类、采纳回答等。
    """
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='提问者'
    )
    tags = models.ManyToManyField(
        QuestionTag,
        blank=True,
        related_name='questions',
        verbose_name='标签'
    )
    is_solved = models.BooleanField('已解决', default=False)
    view_count = models.PositiveIntegerField('浏览量', default=0)
    like_count = models.PositiveIntegerField('点赞数', default=0)
    answer_count = models.PositiveIntegerField('回答数', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '问题'
        verbose_name_plural = '问题'
        ordering = ['-is_solved', '-created_at']
    
    def __str__(self):
        return self.title


class Answer(models.Model):
    """回答模型
    
    针对问题的回答，支持被采纳为最佳答案。
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='所属问题'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='回答者'
    )
    content = models.TextField('回答内容')
    is_accepted = models.BooleanField('已采纳', default=False)
    like_count = models.PositiveIntegerField('点赞数', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '回答'
        verbose_name_plural = '回答'
        ordering = ['-is_accepted', '-like_count', '-created_at']
    
    def __str__(self):
        return f"{self.author.username}回答了《{self.question.title}》"


class AnswerLike(models.Model):
    """回答点赞模型
    
    每个用户对同一回答只能点赞一次。
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name='用户'
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='回答'
    )
    created_at = models.DateTimeField('点赞时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '回答点赞'
        verbose_name_plural = '回答点赞'
        unique_together = ['user', 'answer']
    
    def __str__(self):
        return f"{self.user.username}赞了回答"


class QuestionLike(models.Model):
    """问题点赞模型
    
    每个用户对同一问题只能点赞一次。
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='用户'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='问题'
    )
    created_at = models.DateTimeField('点赞时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '问题点赞'
        verbose_name_plural = '问题点赞'
        unique_together = ['user', 'question']
    
    def __str__(self):
        return f"{self.user.username}赞了《{self.question.title}》"
