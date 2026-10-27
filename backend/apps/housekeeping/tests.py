"""
家政服务模块测试

覆盖服务提供者申请、管理员审核、预约订单、状态流转、评价等核心流程。
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models import User
from .models import (
    ServiceCategory, ServiceProvider, ServiceItem,
    Booking, ServiceReview
)


class HousekeepingBaseTestCase(TestCase):
    """家政服务测试基类，提供通用的测试数据"""

    def setUp(self):
        """创建测试用户和基础数据"""
        self.client = APIClient()

        # 创建不同角色的用户
        self.resident = User.objects.create_user(
            username='resident_user', password='test123456', role='resident'
        )
        self.merchant = User.objects.create_user(
            username='merchant_user', password='test123456', role='merchant'
        )
        self.admin_user = User.objects.create_user(
            username='admin_user', password='test123456', role='admin'
        )

        # 创建服务分类
        self.category = ServiceCategory.objects.create(
            name='保洁服务', slug='cleaning', sort_order=1
        )
        self.category2 = ServiceCategory.objects.create(
            name='维修服务', slug='repair', sort_order=2
        )

    def _create_approved_provider(self):
        """创建已审核通过的服务提供者"""
        provider = ServiceProvider.objects.create(
            user=self.merchant,
            name='张师傅保洁',
            service_area='全城',
            phone='13800138000',
            status=ServiceProvider.Status.APPROVED
        )
        return provider

    def _create_service_item(self, provider=None):
        """创建服务项目"""
        if provider is None:
            provider = self._create_approved_provider()
        return ServiceItem.objects.create(
            provider=provider,
            category=self.category,
            title='两居室深度保洁',
            description='专业深度保洁服务',
            price_min=Decimal('150.00'),
            price_max=Decimal('300.00'),
            duration='2小时'
        )


class ServiceCategoryTestCase(HousekeepingBaseTestCase):
    """服务分类接口测试"""

    def test_list_categories_allow_any(self):
        """匿名用户可以获取分类列表"""
        response = self.client.get('/api/v1/housekeeping/categories/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertEqual(len(data['data']), 2)

    def test_categories_ordered_by_sort_order(self):
        """分类按 sort_order 排序"""
        response = self.client.get('/api/v1/housekeeping/categories/')
        data = response.json()['data']
        self.assertEqual(data[0]['slug'], 'cleaning')
        self.assertEqual(data[1]['slug'], 'repair')


class ServiceProviderApplyTestCase(HousekeepingBaseTestCase):
    """服务提供者申请测试"""

    def test_merchant_can_apply(self):
        """商家用户可以提交申请"""
        self.client.force_authenticate(user=self.merchant)
        response = self.client.post('/api/v1/housekeeping/providers/apply/', {
            'name': '李师傅家政',
            'service_area': '朝阳区',
            'description': '专业家政服务',
            'phone': '13900139000',
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertTrue(
            ServiceProvider.objects.filter(user=self.merchant).exists()
        )
        provider = ServiceProvider.objects.get(user=self.merchant)
        self.assertEqual(provider.status, 'pending')

    def test_resident_can_apply(self):
        """居民（任意登录用户）可以提交服务商申请"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.post('/api/v1/housekeeping/providers/apply/', {
            'name': '测试',
            'phone': '13900139000',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            ServiceProvider.objects.filter(user=self.resident, status='pending').exists()
        )

    def test_apply_requires_login(self):
        """未登录用户不能申请"""
        response = self.client.post('/api/v1/housekeeping/providers/apply/', {
            'name': '测试',
            'phone': '13900139000',
        })
        self.assertEqual(response.status_code, 401)

    def test_cannot_apply_twice(self):
        """不能重复申请"""
        self.client.force_authenticate(user=self.merchant)
        self.client.post('/api/v1/housekeeping/providers/apply/', {
            'name': '李师傅家政',
            'phone': '13900139000',
        })
        response = self.client.post('/api/v1/housekeeping/providers/apply/', {
            'name': '再次申请',
            'phone': '13900139001',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('重复', response.json()['message'])


class ServiceProviderAuditTestCase(HousekeepingBaseTestCase):
    """管理员审核测试"""

    def setUp(self):
        super().setUp()
        # 商家先提交申请
        self.provider = ServiceProvider.objects.create(
            user=self.merchant,
            name='待审核商家',
            phone='13800138000',
            status=ServiceProvider.Status.PENDING
        )

    def test_admin_can_approve(self):
        """管理员可以通过审核"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(
            f'/api/v1/housekeeping/providers/{self.provider.pk}/audit/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.status, 'approved')

    def test_approve_grants_merchant_role(self):
        """审核通过时同步授予申请者商家角色"""
        provider = ServiceProvider.objects.create(
            user=self.resident, name='居民申请服务',
            phone='13800138000', status=ServiceProvider.Status.PENDING
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(
            f'/api/v1/housekeeping/providers/{provider.pk}/audit/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.resident.refresh_from_db()
        self.assertEqual(self.resident.role, User.Role.MERCHANT)

    def test_admin_can_reject(self):
        """管理员可以拒绝申请"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(
            f'/api/v1/housekeeping/providers/{self.provider.pk}/audit/',
            {'action': 'reject'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.status, 'rejected')

    def test_non_admin_cannot_audit(self):
        """非管理员不能审核"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.put(
            f'/api/v1/housekeeping/providers/{self.provider.pk}/audit/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, 403)

    def test_cannot_audit_twice(self):
        """已审核的申请不能重复审核"""
        self.client.force_authenticate(user=self.admin_user)
        self.client.put(
            f'/api/v1/housekeeping/providers/{self.provider.pk}/audit/',
            {'action': 'approve'},
            format='json'
        )
        response = self.client.put(
            f'/api/v1/housekeeping/providers/{self.provider.pk}/audit/',
            {'action': 'reject'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)


class ServiceProviderListTestCase(HousekeepingBaseTestCase):
    """服务提供者列表测试"""

    def test_list_only_approved(self):
        """列表仅展示已通过的提供者"""
        # 创建一个已通过的和一个待审核的
        ServiceProvider.objects.create(
            user=self.merchant,
            name='已通过商家',
            phone='13800138000',
            status=ServiceProvider.Status.APPROVED
        )
        resident2 = User.objects.create_user(
            username='merchant2', password='test123456', role='merchant'
        )
        ServiceProvider.objects.create(
            user=resident2,
            name='待审核商家',
            phone='13800138001',
            status=ServiceProvider.Status.PENDING
        )

        response = self.client.get('/api/v1/housekeeping/providers/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        results = data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], '已通过商家')

    def test_filter_by_category(self):
        """按分类筛选提供者"""
        provider = self._create_approved_provider()
        ServiceItem.objects.create(
            provider=provider,
            category=self.category,
            title='保洁服务A',
            price_min=Decimal('100.00'),
            price_max=Decimal('200.00'),
        )

        response = self.client.get('/api/v1/housekeeping/providers/?category=cleaning')
        data = response.json()['data']
        self.assertEqual(len(data['results']), 1)

        response = self.client.get('/api/v1/housekeeping/providers/?category=repair')
        data = response.json()['data']
        self.assertEqual(len(data['results']), 0)

    def test_search_by_name(self):
        """按名称搜索提供者"""
        self._create_approved_provider()
        response = self.client.get('/api/v1/housekeeping/providers/?search=张师傅')
        data = response.json()['data']
        self.assertEqual(len(data['results']), 1)

        response = self.client.get('/api/v1/housekeeping/providers/?search=不存在')
        data = response.json()['data']
        self.assertEqual(len(data['results']), 0)


class BookingTestCase(HousekeepingBaseTestCase):
    """预约订单测试"""

    def setUp(self):
        super().setUp()
        self.provider = self._create_approved_provider()
        self.service_item = self._create_service_item(self.provider)

    def test_resident_can_create_booking(self):
        """居民可以创建预约"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.post('/api/v1/housekeeping/bookings/', {
            'service_item': self.service_item.pk,
            'preferred_date': str(date.today() + timedelta(days=1)),
            'preferred_time': '09:00-11:00',
            'remark': '请带清洁工具',
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertTrue(Booking.objects.filter(user=self.resident).exists())

    def test_merchant_cannot_create_booking(self):
        """商家不能创建预约"""
        self.client.force_authenticate(user=self.merchant)
        response = self.client.post('/api/v1/housekeeping/bookings/', {
            'service_item': self.service_item.pk,
            'preferred_date': str(date.today() + timedelta(days=1)),
            'preferred_time': '09:00-11:00',
        })
        self.assertEqual(response.status_code, 400)

    def test_cannot_book_unapproved_provider(self):
        """不能预约未通过审核的提供者"""
        merchant2 = User.objects.create_user(
            username='merchant2', password='test123456', role='merchant'
        )
        pending_provider = ServiceProvider.objects.create(
            user=merchant2,
            name='待审核',
            phone='13800138001',
            status=ServiceProvider.Status.PENDING
        )
        item = ServiceItem.objects.create(
            provider=pending_provider,
            category=self.category,
            title='测试服务',
            price_min=Decimal('50.00'),
            price_max=Decimal('100.00'),
        )
        self.client.force_authenticate(user=self.resident)
        response = self.client.post('/api/v1/housekeeping/bookings/', {
            'service_item': item.pk,
            'preferred_date': str(date.today() + timedelta(days=1)),
            'preferred_time': '14:00-16:00',
        })
        self.assertEqual(response.status_code, 400)

    def test_resident_sees_own_bookings(self):
        """居民只能看到自己的预约"""
        Booking.objects.create(
            user=self.resident,
            service_item=self.service_item,
            provider=self.provider,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time='09:00-11:00',
        )
        resident2 = User.objects.create_user(
            username='resident2', password='test123456', role='resident'
        )
        Booking.objects.create(
            user=resident2,
            service_item=self.service_item,
            provider=self.provider,
            preferred_date=date.today() + timedelta(days=2),
            preferred_time='14:00-16:00',
        )

        self.client.force_authenticate(user=self.resident)
        response = self.client.get('/api/v1/housekeeping/bookings/')
        data = response.json()['data']
        self.assertEqual(len(data['results']), 1)

    def test_merchant_sees_received_bookings(self):
        """商家可以看到收到的预约"""
        Booking.objects.create(
            user=self.resident,
            service_item=self.service_item,
            provider=self.provider,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time='09:00-11:00',
        )
        self.client.force_authenticate(user=self.merchant)
        response = self.client.get('/api/v1/housekeeping/bookings/')
        data = response.json()['data']
        self.assertEqual(len(data['results']), 1)


class BookingStatusTransitionTestCase(HousekeepingBaseTestCase):
    """预约订单状态流转测试"""

    def setUp(self):
        super().setUp()
        self.provider = self._create_approved_provider()
        self.service_item = self._create_service_item(self.provider)
        self.booking = Booking.objects.create(
            user=self.resident,
            service_item=self.service_item,
            provider=self.provider,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time='09:00-11:00',
            status=Booking.Status.PENDING
        )

    def test_provider_confirms_booking(self):
        """服务提供者确认预约：pending → confirmed"""
        self.client.force_authenticate(user=self.merchant)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'confirmed'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')

    def test_provider_rejects_booking(self):
        """服务提供者拒绝预约：pending → rejected"""
        self.client.force_authenticate(user=self.merchant)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'rejected'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'rejected')

    def test_provider_starts_service(self):
        """服务提供者开始服务：confirmed → in_service"""
        self.booking.status = Booking.Status.CONFIRMED
        self.booking.save()

        self.client.force_authenticate(user=self.merchant)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'in_service'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'in_service')

    def test_provider_completes_service(self):
        """服务提供者完成服务：in_service → completed"""
        self.booking.status = Booking.Status.IN_SERVICE
        self.booking.save()

        self.client.force_authenticate(user=self.merchant)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'completed')

    def test_invalid_transition_pending_to_completed(self):
        """非法流转：pending → completed"""
        self.client.force_authenticate(user=self.merchant)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'pending')

    def test_invalid_transition_pending_to_in_service(self):
        """非法流转：pending → in_service"""
        self.client.force_authenticate(user=self.merchant)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'in_service'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_resident_cannot_change_status(self):
        """居民不能变更订单状态"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'confirmed'},
            format='json'
        )
        self.assertEqual(response.status_code, 403)


class ServiceReviewTestCase(HousekeepingBaseTestCase):
    """服务评价测试"""

    def setUp(self):
        super().setUp()
        self.provider = self._create_approved_provider()
        self.service_item = self._create_service_item(self.provider)
        self.booking = Booking.objects.create(
            user=self.resident,
            service_item=self.service_item,
            provider=self.provider,
            preferred_date=date.today(),
            preferred_time='09:00-11:00',
            status=Booking.Status.COMPLETED
        )

    def test_resident_can_review_completed_booking(self):
        """居民可以评价已完成的订单"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.post(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/review/',
            {'rating': 5, 'content': '服务非常好！'},
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertTrue(ServiceReview.objects.filter(booking=self.booking).exists())

    def test_review_updates_booking_status(self):
        """评价后订单状态变为 reviewed"""
        self.client.force_authenticate(user=self.resident)
        self.client.post(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/review/',
            {'rating': 4, 'content': '不错'},
            format='json'
        )
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'reviewed')

    def test_cannot_review_non_completed_booking(self):
        """不能评价未完成的订单"""
        self.booking.status = Booking.Status.PENDING
        self.booking.save()

        self.client.force_authenticate(user=self.resident)
        response = self.client.post(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/review/',
            {'rating': 5, 'content': '好评'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_review_twice(self):
        """不能重复评价"""
        self.client.force_authenticate(user=self.resident)
        self.client.post(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/review/',
            {'rating': 5, 'content': '好评'},
            format='json'
        )
        # 第二次评价（此时状态已变为 reviewed，也会被拦截）
        response = self.client.post(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/review/',
            {'rating': 4, 'content': '再评一次'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_only_booking_user_can_review(self):
        """只有预约用户可以评价"""
        resident2 = User.objects.create_user(
            username='resident2', password='test123456', role='resident'
        )
        self.client.force_authenticate(user=resident2)
        response = self.client.post(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/review/',
            {'rating': 5, 'content': '好评'},
            format='json'
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_rating_value(self):
        """评分超出范围"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.post(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/review/',
            {'rating': 6, 'content': '超范围'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)


class RatingCalculationTestCase(HousekeepingBaseTestCase):
    """评分计算测试"""

    def setUp(self):
        super().setUp()
        self.provider = self._create_approved_provider()
        self.service_item = self._create_service_item(self.provider)

    def _create_completed_booking(self, user):
        """创建已完成的订单"""
        return Booking.objects.create(
            user=user,
            service_item=self.service_item,
            provider=self.provider,
            preferred_date=date.today(),
            preferred_time='09:00-11:00',
            status=Booking.Status.COMPLETED
        )

    def test_single_review_updates_rating(self):
        """单条评价更新平均评分"""
        booking = self._create_completed_booking(self.resident)
        self.client.force_authenticate(user=self.resident)
        self.client.post(
            f'/api/v1/housekeeping/bookings/{booking.pk}/review/',
            {'rating': 4, 'content': '不错'},
            format='json'
        )
        self.provider.refresh_from_db()
        self.assertEqual(float(self.provider.avg_rating), 4.0)
        self.assertEqual(self.provider.review_count, 1)

    def test_multiple_reviews_calculate_average(self):
        """多条评价计算平均分"""
        resident2 = User.objects.create_user(
            username='resident2', password='test123456', role='resident'
        )
        booking1 = self._create_completed_booking(self.resident)
        booking2 = self._create_completed_booking(resident2)

        self.client.force_authenticate(user=self.resident)
        self.client.post(
            f'/api/v1/housekeeping/bookings/{booking1.pk}/review/',
            {'rating': 5, 'content': '很好'},
            format='json'
        )

        self.client.force_authenticate(user=resident2)
        self.client.post(
            f'/api/v1/housekeeping/bookings/{booking2.pk}/review/',
            {'rating': 3, 'content': '一般'},
            format='json'
        )

        self.provider.refresh_from_db()
        self.assertEqual(float(self.provider.avg_rating), 4.0)
        self.assertEqual(self.provider.review_count, 2)


class PermissionTestCase(HousekeepingBaseTestCase):
    """权限检查测试"""

    def test_unauthenticated_cannot_access_bookings(self):
        """未认证用户不能访问预约接口"""
        response = self.client.get('/api/v1/housekeeping/bookings/')
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_can_view_providers(self):
        """未认证用户可以浏览服务提供者"""
        self._create_approved_provider()
        response = self.client.get('/api/v1/housekeeping/providers/')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_can_view_categories(self):
        """未认证用户可以浏览服务分类"""
        response = self.client.get('/api/v1/housekeeping/categories/')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_cannot_apply(self):
        """未认证用户不能申请"""
        response = self.client.post('/api/v1/housekeeping/providers/apply/', {
            'name': '测试',
            'phone': '13800138000',
        })
        self.assertEqual(response.status_code, 401)


class BookingUpdateRestrictionTestCase(HousekeepingBaseTestCase):
    """预约订单修改限制测试（仅待确认状态可修改）"""

    def setUp(self):
        super().setUp()
        self.provider = self._create_approved_provider()
        self.service_item = self._create_service_item(self.provider)
        self.client.force_authenticate(user=self.resident)

    def _create_booking(self, status=Booking.Status.PENDING):
        return Booking.objects.create(
            user=self.resident,
            service_item=self.service_item,
            provider=self.provider,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time='09:00-11:00',
            status=status,
        )

    def test_resident_can_update_pending_booking(self):
        """待确认订单可以修改预约信息"""
        booking = self._create_booking()
        response = self.client.patch(
            f'/api/v1/housekeeping/bookings/{booking.pk}/',
            {'remark': '改到下午', 'preferred_time': '14:00-16:00'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.preferred_time, '14:00-16:00')

    def test_cannot_update_confirmed_booking(self):
        """已确认订单不允许修改"""
        booking = self._create_booking(status=Booking.Status.CONFIRMED)
        response = self.client.patch(
            f'/api/v1/housekeeping/bookings/{booking.pk}/',
            {'preferred_time': '14:00-16:00'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        booking.refresh_from_db()
        self.assertEqual(booking.preferred_time, '09:00-11:00')

    def test_cannot_update_completed_booking(self):
        """已完成订单的履约记录不允许篡改"""
        booking = self._create_booking(status=Booking.Status.COMPLETED)
        response = self.client.patch(
            f'/api/v1/housekeeping/bookings/{booking.pk}/',
            {'preferred_date': str(date.today() + timedelta(days=30))},
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        booking.refresh_from_db()
        self.assertEqual(
            booking.preferred_date, date.today() + timedelta(days=1)
        )


class BookingCancelTestCase(HousekeepingBaseTestCase):
    """预约订单取消终态测试"""

    def setUp(self):
        super().setUp()
        self.provider = self._create_approved_provider()
        self.service_item = self._create_service_item(self.provider)
        self.booking = Booking.objects.create(
            user=self.resident,
            service_item=self.service_item,
            provider=self.provider,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time='09:00-11:00',
            status=Booking.Status.PENDING
        )

    def test_resident_can_cancel_pending_booking(self):
        """居民可取消待确认订单"""
        self.client.force_authenticate(user=self.resident)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'cancelled'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELLED)

    def test_resident_can_cancel_confirmed_booking(self):
        """已确认订单也有取消出口，不会永久僵死"""
        self.booking.status = Booking.Status.CONFIRMED
        self.booking.save(update_fields=['status'])
        self.client.force_authenticate(user=self.resident)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'cancelled'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELLED)

    def test_provider_can_reject_confirmed_booking(self):
        """服务方无法履约时可将已确认订单置为 rejected"""
        self.booking.status = Booking.Status.CONFIRMED
        self.booking.save(update_fields=['status'])
        self.client.force_authenticate(user=self.merchant)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'rejected'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.REJECTED)

    def test_other_user_cannot_cancel(self):
        """非预约用户不能取消他人订单"""
        other = User.objects.create_user(
            username='other_resident', password='test123456', role='resident'
        )
        self.booking.status = Booking.Status.CONFIRMED
        self.booking.save(update_fields=['status'])
        self.client.force_authenticate(user=other)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'cancelled'},
            format='json'
        )
        self.assertEqual(response.status_code, 403)

    def test_cannot_cancel_completed_booking(self):
        """已完成订单不允许取消"""
        self.booking.status = Booking.Status.COMPLETED
        self.booking.save(update_fields=['status'])
        self.client.force_authenticate(user=self.resident)
        response = self.client.put(
            f'/api/v1/housekeeping/bookings/{self.booking.pk}/status/',
            {'status': 'cancelled'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)


class BookingDateValidationTestCase(HousekeepingBaseTestCase):
    """预约日期校验测试"""

    def setUp(self):
        super().setUp()
        self.provider = self._create_approved_provider()
        self.service_item = self._create_service_item(self.provider)
        self.client.force_authenticate(user=self.resident)

    def test_cannot_book_past_date(self):
        """预约日期早于今天被拒绝"""
        response = self.client.post('/api/v1/housekeeping/bookings/', {
            'service_item': self.service_item.pk,
            'preferred_date': str(date.today() - timedelta(days=1)),
            'preferred_time': '09:00-11:00',
        })
        self.assertEqual(response.status_code, 400)
        # 字段级错误详情位于响应的 data 中
        self.assertIn('preferred_date', str(response.json()['data']))
