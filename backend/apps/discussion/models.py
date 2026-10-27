"""
自由发言模块数据模型

包含帖子、评论、帖子图片、点赞四个核心模型。
"""
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from common.utils import post_upload_path


class Post(models.Model):
    """帖子模型
    
    自由发言板块的核心实体，支持多种帖子类型和管理操作。
    """
    
    class PostType(models.TextChoices):
        CHAT = 'chat', '闲聊'
        HELP = 'help', '求助'
        SHARE = 'share', '分享'
        NOTICE = 'notice', '公告'
    
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='作者'
    )
    post_type = models.CharField(
        '帖子类型',
        max_length=20,
        choices=PostType.choices,
        default=PostType.CHAT
    )
    tags = models.CharField('话题标签', max_length=200, blank=True, default='',
                           help_text='多个标签用逗号分隔')
    is_top = models.BooleanField('置顶', default=False)
    is_featured = models.BooleanField('精华', default=False)
    view_count = models.PositiveIntegerField('浏览量', default=0)
    like_count = models.PositiveIntegerField('点赞数', default=0)
    comment_count = models.PositiveIntegerField('评论数', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = '帖子'
        ordering = ['-is_top', '-created_at']
    
    def __str__(self):
        return self.title


class PostImage(models.Model):
    """帖子图片模型
    
    每个帖子最多关联 9 张图片。
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='所属帖子'
    )
    image = models.ImageField('图片', upload_to=post_upload_path)
    created_at = models.DateTimeField('上传时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '帖子图片'
        verbose_name_plural = '帖子图片'
    
    def __str__(self):
        return f"帖子{self.post_id}的图片"


class Comment(models.Model):
    """评论模型
    
    支持楼中楼回复（通过 parent 字段自关联）。
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='所属帖子'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='评论者'
    )
    content = models.TextField('评论内容', max_length=2000)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='父评论'
    )
    like_count = models.PositiveIntegerField('点赞数', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username}评论了《{self.post.title}》"


class PostLike(models.Model):
    """帖子点赞模型
    
    每个用户对同一帖子只能点赞一次。
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='帖子'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_likes',
        verbose_name='用户'
    )
    created_at = models.DateTimeField('点赞时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '帖子点赞'
        verbose_name_plural = '帖子点赞'
        unique_together = ['post', 'user']
    
    def __str__(self):
        return f"{self.user.username}赞了《{self.post.title}》"


@receiver(post_delete, sender=PostImage)
def delete_post_image_file(sender, instance, **kwargs):
    """删除帖子图片记录时同步清理物理文件，避免孤儿文件残留"""
    if instance.image:
        instance.image.delete(save=False)
