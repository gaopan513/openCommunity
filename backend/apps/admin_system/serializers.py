"""
系统管理模块序列化器
"""
from rest_framework import serializers
from .models import Announcement, Report
from apps.users.serializers import UserSimpleSerializer


class AnnouncementSerializer(serializers.ModelSerializer):
    """公告序列化器"""
    author_info = UserSimpleSerializer(source='author', read_only=True)
    
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'author', 'author_info',
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class ReportSerializer(serializers.ModelSerializer):
    """举报序列化器"""
    reporter_info = UserSimpleSerializer(source='reporter', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Report
        fields = ['id', 'reporter', 'reporter_info', 'content_type',
                  'object_id', 'reason', 'status', 'status_display',
                  'handle_note', 'handled_at', 'created_at']
        read_only_fields = ['id', 'reporter', 'status', 'handled_at', 'created_at']


class ReportCreateSerializer(serializers.ModelSerializer):
    """举报创建序列化器"""
    
    class Meta:
        model = Report
        fields = ['content_type', 'object_id', 'reason']
