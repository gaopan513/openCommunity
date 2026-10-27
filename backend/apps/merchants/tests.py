"""
商家模块单元测试
"""
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.users.models import User
from .models import MerchantCategory, Merchant, Activity, MerchantReview


class MerchantAPITest(APITestCase):
    """商家接口测试"""

    def setUp(self):
        self.merchant_user = User.objects.create_user(
            username='shopowner', password='pass123456', role='merchant'
        )
        self.admin = User.objects.create_user(
            username='admin1', password='pass123456', role='admin'
        )
        self.resident = User.objects.create_user(
            username='resident1', password='pass123456', role='resident'
        )
        self.category = MerchantCategory.objects.create(
            name='餐饮', slug='dining', sort_order=1
        )
        self.client = APIClient()

    def test_apply_merchant(self):
        """测试商家入驻申请"""
        self.client.force_authenticate(user=self.merchant_user)
        data = {
            'name': '老王面馆',
            'category': self.category.pk,
            'address': '小区东门101',
            'phone': '13800138000',
        }
        response = self.client.post('/api/v1/merchants/apply/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Merchant.objects.filter(name='老王面馆', status='pending').exists())

    def test_resident_can_apply(self):
        """测试居民（任意登录用户）可以提交入驻申请"""
        self.client.force_authenticate(user=self.resident)
        data = {'name': '假商家', 'address': '某处', 'phone': '13900139000'}
        response = self.client.post('/api/v1/merchants/apply/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Merchant.objects.filter(user=self.resident, status='pending').exists()
        )

    def test_apply_requires_login(self):
        """测试未登录用户不能申请入驻"""
        data = {'name': '匿名商家', 'address': '某处', 'phone': '13900139000'}
        response = self.client.post('/api/v1/merchants/apply/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_approve(self):
        """测试管理员审核通过"""
        merchant = Merchant.objects.create(
            user=self.merchant_user, name='待审商家',
            address='地址', phone='13800138000', status='pending'
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f'/api/v1/merchants/{merchant.pk}/audit/',
            {'status': 'approved'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        merchant.refresh_from_db()
        self.assertEqual(merchant.status, 'approved')

    def test_approve_grants_merchant_role(self):
        """测试审核通过时同步授予申请者商家角色"""
        merchant = Merchant.objects.create(
            user=self.resident, name='居民申请店',
            address='地址', phone='13800138000', status='pending'
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f'/api/v1/merchants/{merchant.pk}/audit/',
            {'status': 'approved'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.resident.refresh_from_db()
        self.assertEqual(self.resident.role, User.Role.MERCHANT)

    def test_reject_keeps_resident_role(self):
        """测试审核拒绝时角色保持不变"""
        merchant = Merchant.objects.create(
            user=self.resident, name='居民申请店',
            address='地址', phone='13800138000', status='pending'
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f'/api/v1/merchants/{merchant.pk}/audit/',
            {'status': 'rejected'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.resident.refresh_from_db()
        self.assertEqual(self.resident.role, User.Role.RESIDENT)

    def test_list_only_approved(self):
        """测试列表仅显示已审核商家"""
        Merchant.objects.create(
            user=self.merchant_user, name='已通过', address='a', phone='1', status='approved'
        )
        other_user = User.objects.create_user(
            username='shop2', password='pass123456', role='merchant'
        )
        Merchant.objects.create(
            user=other_user, name='待审核', address='b', phone='2', status='pending'
        )
        response = self.client.get('/api/v1/merchants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 只应返回已审核的
        results = response.data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], '已通过')

    def test_create_activity(self):
        """测试商家创建活动"""
        merchant = Merchant.objects.create(
            user=self.merchant_user, name='面馆', address='a', phone='1', status='approved'
        )
        self.client.force_authenticate(user=self.merchant_user)
        data = {
            'title': '开业大酬宾',
            'description': '全场8折',
            'start_time': timezone.now().isoformat(),
            'end_time': (timezone.now() + timedelta(days=7)).isoformat(),
        }
        response = self.client.post(
            f'/api/v1/merchants/{merchant.pk}/activities/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_review(self):
        """测试居民评价商家"""
        merchant = Merchant.objects.create(
            user=self.merchant_user, name='面馆', address='a', phone='1', status='approved'
        )
        self.client.force_authenticate(user=self.resident)
        data = {'rating': 5, 'content': '味道很好'}
        response = self.client.post(
            f'/api/v1/merchants/{merchant.pk}/reviews/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        merchant.refresh_from_db()
        self.assertEqual(merchant.avg_rating, 5.0)
        self.assertEqual(merchant.review_count, 1)

    def test_one_review_per_user(self):
        """测试每人只能评价一次"""
        merchant = Merchant.objects.create(
            user=self.merchant_user, name='面馆', address='a', phone='1', status='approved'
        )
        MerchantReview.objects.create(
            merchant=merchant, user=self.resident, rating=4, content='不错'
        )
        self.client.force_authenticate(user=self.resident)
        data = {'rating': 5, 'content': '再评一次'}
        response = self.client.post(
            f'/api/v1/merchants/{merchant.pk}/reviews/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_merchant_reply_review(self):
        """测试商家回复评价"""
        merchant = Merchant.objects.create(
            user=self.merchant_user, name='面馆', address='a', phone='1', status='approved'
        )
        review = MerchantReview.objects.create(
            merchant=merchant, user=self.resident, rating=4, content='不错'
        )
        self.client.force_authenticate(user=self.merchant_user)
        response = self.client.put(
            f'/api/v1/merchants/{merchant.pk}/reviews/{review.pk}/reply/',
            {'reply': '感谢好评！'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.reply, '感谢好评！')

    def test_category_list(self):
        """测试商家分类列表"""
        response = self.client.get('/api/v1/merchant-categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MerchantAuditGuardTest(APITestCase):
    """商家审核前置检查与角色回收测试"""

    def setUp(self):
        self.merchant_user = User.objects.create_user(
            username='audit_shop', password='pass123456', role='resident'
        )
        self.admin = User.objects.create_user(
            username='audit_admin', password='pass123456', role='admin'
        )
        self.client = APIClient()

    def _create_merchant(self, status='pending'):
        return Merchant.objects.create(
            user=self.merchant_user, name='审核用商家',
            address='a', phone='13800138000', status=status
        )

    def test_cannot_audit_non_pending(self):
        """已处理的申请不允许重复审核"""
        merchant = self._create_merchant(status='approved')
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f'/api/v1/merchants/{merchant.pk}/audit/',
            {'status': 'rejected'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        merchant.refresh_from_db()
        self.assertEqual(merchant.status, 'approved')

    def test_reject_revokes_merchant_role(self):
        """拒绝申请时回收商家角色（用户此前曾通过审核）"""
        merchant = self._create_merchant(status='approved')
        # 用户当前持有商家角色（曾通过审核），复用记录重新申请后再次被拒
        self.merchant_user.role = User.Role.MERCHANT
        self.merchant_user.save(update_fields=['role'])
        merchant.status = Merchant.Status.PENDING
        merchant.save(update_fields=['status'])

        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f'/api/v1/merchants/{merchant.pk}/audit/',
            {'status': 'rejected'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.merchant_user.refresh_from_db()
        self.assertEqual(self.merchant_user.role, User.Role.RESIDENT)

    def test_reject_keeps_role_for_approved_provider(self):
        """用户持有已通过的家政服务商资质时，拒绝商家不回收角色"""
        from apps.housekeeping.models import ServiceProvider
        merchant = self._create_merchant(status='approved')
        self.merchant_user.role = User.Role.MERCHANT
        self.merchant_user.save(update_fields=['role'])
        ServiceProvider.objects.create(
            user=self.merchant_user, name='服务商', phone='13800138001',
            status=ServiceProvider.Status.APPROVED
        )
        merchant.status = Merchant.Status.PENDING
        merchant.save(update_fields=['status'])

        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f'/api/v1/merchants/{merchant.pk}/audit/',
            {'status': 'rejected'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.merchant_user.refresh_from_db()
        self.assertEqual(self.merchant_user.role, User.Role.MERCHANT)


class ActivityValidationTest(APITestCase):
    """商家活动时间校验测试"""

    def setUp(self):
        self.merchant_user = User.objects.create_user(
            username='activity_shop', password='pass123456', role='merchant'
        )
        self.merchant = Merchant.objects.create(
            user=self.merchant_user, name='活动商家',
            address='a', phone='13800138000', status='approved'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.merchant_user)

    def test_end_time_before_start_time_rejected(self):
        """结束时间早于开始时间的活动被拒绝"""
        data = {
            'title': '倒流活动',
            'start_time': (timezone.now() + timedelta(days=7)).isoformat(),
            'end_time': timezone.now().isoformat(),
        }
        response = self.client.post(
            f'/api/v1/merchants/{self.merchant.pk}/activities/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_activity_accepted(self):
        """时间区间合法的活动正常创建"""
        data = {
            'title': '正常活动',
            'start_time': timezone.now().isoformat(),
            'end_time': (timezone.now() + timedelta(days=7)).isoformat(),
        }
        response = self.client.post(
            f'/api/v1/merchants/{self.merchant.pk}/activities/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class MerchantSubListPaginationTest(APITestCase):
    """商家活动/评价列表分页测试"""

    def setUp(self):
        self.merchant_user = User.objects.create_user(
            username='page_shop', password='pass123456', role='merchant'
        )
        self.merchant = Merchant.objects.create(
            user=self.merchant_user, name='分页商家',
            address='a', phone='13800138000', status='approved'
        )
        # 评价有 unique_together(merchant, user)，需多用户生成 25 条评价
        for i in range(25):
            reviewer = User.objects.create_user(
                username=f'reviewer{i}', password='pass123456', role='resident'
            )
            MerchantReview.objects.create(
                merchant=self.merchant, user=reviewer, rating=5, content=f'第{i}条'
            )
        self.client = APIClient()

    def test_reviews_list_paginated(self):
        """评价列表返回分页结构且默认每页不超过 20 条"""
        response = self.client.get(f'/api/v1/merchants/{self.merchant.pk}/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertIn('total', data)
        self.assertIn('page', data)
        self.assertIn('results', data)
        self.assertEqual(data['total'], 25)
        self.assertLessEqual(len(data['results']), 20)
