"""
系统管理模块数据模型

包含系统公告和内容举报两个模型。
"""
from django.db import models
from django.conf import settings


class Announcement(models.Model):
    """系统公告模型
    
    管理员发布的社区公告，在首页展示。
    """
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcements',
        verbose_name='发布者'
    )
    is_active = models.BooleanField('是否展示', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '系统公告'
        verbose_name_plural = '系统公告'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Report(models.Model):
    """内容举报模型
    
    用户举报违规内容，管理员处理。
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', '待处理'
        HANDLED = 'handled', '已处理'
        DISMISSED = 'dismissed', '已驳回'
    
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='举报人'
    )
    content_type = models.CharField(
        '举报内容类型',
        max_length=50,
        help_text='如：post, comment, product, merchant, review'
    )
    object_id = models.PositiveIntegerField('被举报对象ID')
    reason = models.TextField('举报原因')
    status = models.CharField(
        '处理状态',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    handle_note = models.TextField('处理备注', blank=True, default='')
    handled_at = models.DateTimeField('处理时间', null=True, blank=True)
    created_at = models.DateTimeField('举报时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '内容举报'
        verbose_name_plural = '内容举报'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"举报{self.content_type}#{self.object_id}({self.get_status_display()})"
