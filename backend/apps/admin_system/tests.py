"""
系统管理模块单元测试
"""
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.users.models import User
from .models import Announcement, Report


class AnnouncementAPITest(APITestCase):
    """公告接口测试"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin1', password='pass123456', role='admin'
        )
        self.resident = User.objects.create_user(
            username='user1', password='pass123456', role='resident'
        )
        self.announcement = Announcement.objects.create(
            title='社区通知', content='本周六停电检修', author=self.admin
        )
        self.client = APIClient()

    def test_list_announcements_public(self):
        """测试公告列表公开访问"""
        response = self.client.get('/api/v1/announcements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_announcement_admin(self):
        """测试管理员发布公告"""
        self.client.force_authenticate(user=self.admin)
        data = {'title': '新公告', 'content': '内容'}
        response = self.client.post('/api/v1/announcements/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_announcement_forbidden(self):
        """测试普通用户不能发布公告"""
        self.client.force_authenticate(user=self.resident)
        data = {'title': '假公告', 'content': '内容'}
        response = self.client.post('/api/v1/announcements/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_announcement_hidden(self):
        """测试未激活公告不在列表展示"""
        Announcement.objects.create(
            title='隐藏公告', content='不可见', author=self.admin, is_active=False
        )
        response = self.client.get('/api/v1/announcements/')
        results = response.data['data']['results']
        titles = [r['title'] for r in results]
        self.assertNotIn('隐藏公告', titles)


class ReportAPITest(APITestCase):
    """举报接口测试"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin2', password='pass123456', role='admin'
        )
        self.resident = User.objects.create_user(
            username='reporter1', password='pass123456', role='resident'
        )
        self.client = APIClient()

    def test_create_report(self):
        """测试提交举报"""
        self.client.force_authenticate(user=self.resident)
        data = {'content_type': 'post', 'object_id': 1, 'reason': '含有广告'}
        response = self.client.post('/api/v1/admin/reports/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_report_requires_auth(self):
        """测试未登录不能举报"""
        data = {'content_type': 'post', 'object_id': 1, 'reason': '违规'}
        response = self.client.post('/api/v1/admin/reports/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_handle_report(self):
        """测试管理员处理举报"""
        report = Report.objects.create(
            reporter=self.resident, content_type='post',
            object_id=1, reason='广告'
        )
        self.client.force_authenticate(user=self.admin)
        data = {'status': 'handled', 'handle_note': '已删除违规内容'}
        response = self.client.put(
            f'/api/v1/admin/reports/{report.pk}/handle/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report.refresh_from_db()
        self.assertEqual(report.status, 'handled')

    def test_non_admin_cannot_list_reports(self):
        """测试普通用户不能查看所有举报"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.get('/api/v1/admin/reports/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StatisticsAPITest(APITestCase):
    """统计接口测试"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin3', password='pass123456', role='admin'
        )
        self.resident = User.objects.create_user(
            username='user3', password='pass123456', role='resident'
        )

    def test_statistics_admin(self):
        """测试管理员获取统计"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/admin/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data['data'])
        self.assertIn('posts', response.data['data'])

    def test_statistics_forbidden(self):
        """测试普通用户不能获取统计"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.get('/api/v1/admin/statistics/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
