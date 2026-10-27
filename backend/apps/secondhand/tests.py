"""
二手市场模块测试

覆盖商品创建、列表筛选、状态变更、评论、权限控制、分类列表等功能。
"""
import atexit
import io
import shutil
import tempfile
from decimal import Decimal

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.users.models import User
from .models import Product, ProductCategory, ProductImage, ProductComment

# 跨平台测试媒体目录：'/tmp/test_media/' 在 Windows 会落到当前盘根目录（D:\tmp），
# 受沙箱/权限限制无法写入；改用系统临时目录，进程退出时自动清理
TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix='oc_test_media_')
atexit.register(shutil.rmtree, TEST_MEDIA_ROOT, ignore_errors=True)


def create_test_image():
    """创建测试用图片文件"""
    image = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    img_io.seek(0)
    img_io.name = 'test.jpg'
    return img_io


def create_uploaded_image():
    """创建可直接赋给 ImageField 的上传文件对象（每次全新字节流）"""
    image = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    return SimpleUploadedFile('test.jpg', img_io.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductCategoryTest(TestCase):
    """商品分类测试"""

    def setUp(self):
        self.client = APIClient()
        self.category1 = ProductCategory.objects.create(name='电子产品', slug='electronics', sort_order=1)
        self.category2 = ProductCategory.objects.create(name='家具', slug='furniture', sort_order=2)

    def test_list_categories(self):
        """测试获取分类列表（无需认证）"""
        response = self.client.get('/api/v1/product-categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['code'], 0)
        # 9 条预设分类 + 2 条测试分类
        self.assertEqual(len(data['data']), 11)
        # 验证测试创建的分类存在
        slugs = [item['slug'] for item in data['data']]
        self.assertIn('electronics', slugs)
        self.assertIn('furniture', slugs)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductCreateTest(TestCase):
    """商品创建测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='seller1', password='testpass123', role='resident'
        )
        self.category = ProductCategory.objects.create(name='电子产品', slug='electronics')
        self.client.force_authenticate(user=self.user)

    def test_create_product_without_images(self):
        """测试创建不带图片的商品"""
        data = {
            'title': '二手iPhone 13',
            'description': '使用一年，成色良好',
            'price': '3500.00',
            'condition': 'like_new',
            'category': self.category.id,
        }
        response = self.client.post('/api/v1/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['message'], '发布成功')
        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.first()
        self.assertEqual(product.seller, self.user)
        self.assertEqual(product.status, 'on_sale')

    def test_create_product_with_images(self):
        """测试创建带图片的商品"""
        img1 = create_test_image()
        img2 = create_test_image()
        data = {
            'title': '二手书桌',
            'description': '实木书桌，九成新',
            'price': '200.00',
            'condition': 'like_new',
            'category': self.category.id,
            'images': [img1, img2],
        }
        response = self.client.post('/api/v1/products/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.first()
        self.assertEqual(product.images.count(), 2)

    def test_create_product_invalid_price(self):
        """测试价格为0时创建失败"""
        data = {
            'title': '免费商品',
            'price': '0',
            'condition': 'fair',
        }
        response = self.client.post('/api/v1/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_negative_price(self):
        """测试负价格创建失败"""
        data = {
            'title': '负价格商品',
            'price': '-10.00',
            'condition': 'fair',
        }
        response = self.client.post('/api/v1/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_unauthenticated(self):
        """测试未认证用户不能创建商品"""
        self.client.force_authenticate(user=None)
        data = {
            'title': '未认证商品',
            'price': '100.00',
            'condition': 'good',
        }
        response = self.client.post('/api/v1/products/', data, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductListFilterTest(TestCase):
    """商品列表和筛选测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='seller1', password='testpass123', role='resident'
        )
        self.category1 = ProductCategory.objects.create(name='电子产品', slug='electronics')
        self.category2 = ProductCategory.objects.create(name='家具', slug='furniture')

        self.product1 = Product.objects.create(
            title='iPhone 13', description='苹果手机', price=Decimal('3500.00'),
            condition='like_new', status='on_sale', seller=self.user, category=self.category1
        )
        self.product2 = Product.objects.create(
            title='实木书桌', description='家具', price=Decimal('200.00'),
            condition='good', status='on_sale', seller=self.user, category=self.category2
        )
        self.product3 = Product.objects.create(
            title='已售出的耳机', description='蓝牙耳机', price=Decimal('50.00'),
            condition='fair', status='sold', seller=self.user, category=self.category1
        )

    def test_list_products(self):
        """测试获取商品列表（无需认证）"""
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['code'], 0)

    def test_filter_by_category(self):
        """测试按分类筛选"""
        response = self.client.get(f'/api/v1/products/?category={self.category1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['data']['results']
        self.assertEqual(len(results), 2)

    def test_filter_by_status(self):
        """测试按状态筛选"""
        response = self.client.get('/api/v1/products/?status=on_sale')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['data']['results']
        self.assertEqual(len(results), 2)

    def test_filter_by_condition(self):
        """测试按成色筛选"""
        response = self.client.get('/api/v1/products/?condition=like_new')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'iPhone 13')

    def test_search_products(self):
        """测试搜索功能"""
        response = self.client.get('/api/v1/products/?search=iPhone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['data']['results']
        self.assertEqual(len(results), 1)

    def test_order_by_price(self):
        """测试按价格排序"""
        response = self.client.get('/api/v1/products/?ordering=price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['data']['results']
        prices = [Decimal(r['price']) for r in results]
        self.assertEqual(prices, sorted(prices))

    def test_filter_mine(self):
        """测试 ?mine=1 仅返回当前用户发布的商品"""
        other = User.objects.create_user(username='seller2', password='testpass123', role='resident')
        Product.objects.create(
            title='别人的商品', description='其他卖家', price=Decimal('10.00'),
            condition='good', status='on_sale', seller=other, category=self.category1
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/products/?mine=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['data']['results']
        self.assertEqual(len(results), 3)
        for item in results:
            self.assertEqual(item['seller_info']['id'], self.user.id)

    def test_filter_mine_unauthenticated_returns_empty(self):
        """测试未登录带 ?mine=1 返回空列表（不泄漏全量商品）"""
        response = self.client.get('/api/v1/products/?mine=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['data']['results']
        self.assertEqual(results, [])


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductStatusTransitionTest(TestCase):
    """商品状态变更测试"""

    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1', password='testpass123', role='resident'
        )
        self.product = Product.objects.create(
            title='测试商品', price=Decimal('100.00'),
            condition='good', status='on_sale', seller=self.seller
        )
        self.client.force_authenticate(user=self.seller)

    def test_on_sale_to_reserved(self):
        """测试在售→已预订（合法）"""
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'reserved'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'reserved')

    def test_on_sale_to_sold(self):
        """测试在售→已售出（合法）"""
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'sold'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'sold')

    def test_on_sale_to_off_shelf(self):
        """测试在售→已下架（合法）"""
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'off_shelf'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'off_shelf')

    def test_reserved_to_on_sale(self):
        """测试已预订→在售（合法）"""
        self.product.status = 'reserved'
        self.product.save()
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'on_sale'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'on_sale')

    def test_reserved_to_sold(self):
        """测试已预订→已售出（合法）"""
        self.product.status = 'reserved'
        self.product.save()
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'sold'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'sold')

    def test_sold_cannot_change(self):
        """测试已售出不能变更状态（非法）"""
        self.product.status = 'sold'
        self.product.save()
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'on_sale'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reserved_to_off_shelf_invalid(self):
        """测试已预订→已下架（非法）"""
        self.product.status = 'reserved'
        self.product.save()
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'off_shelf'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_off_shelf_to_on_sale(self):
        """测试已下架→在售（合法）"""
        self.product.status = 'off_shelf'
        self.product.save()
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'on_sale'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'on_sale')

    def test_invalid_status_value(self):
        """测试无效状态值"""
        response = self.client.put(
            f'/api/v1/products/{self.product.id}/status/',
            {'status': 'invalid_status'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductCommentTest(TestCase):
    """商品评论测试"""

    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1', password='testpass123', role='resident'
        )
        self.buyer = User.objects.create_user(
            username='buyer1', password='testpass123', role='resident'
        )
        self.product = Product.objects.create(
            title='测试商品', price=Decimal('100.00'),
            condition='good', status='on_sale', seller=self.seller
        )

    def test_post_comment(self):
        """测试发表评论"""
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            f'/api/v1/products/{self.product.id}/comments/',
            {'content': '这个还在吗？'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['data']['content'], '这个还在吗？')
        self.assertEqual(ProductComment.objects.count(), 1)

    def test_get_comments(self):
        """测试获取评论列表"""
        ProductComment.objects.create(
            product=self.product, author=self.buyer, content='评论1'
        )
        ProductComment.objects.create(
            product=self.product, author=self.seller, content='评论2'
        )
        response = self.client.get(f'/api/v1/products/{self.product.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['code'], 0)

    def test_post_empty_comment(self):
        """测试发表空评论失败"""
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(
            f'/api/v1/products/{self.product.id}/comments/',
            {'content': ''}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_comment_unauthenticated(self):
        """测试未认证用户不能评论"""
        response = self.client.post(
            f'/api/v1/products/{self.product.id}/comments/',
            {'content': '未认证评论'}, format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductPermissionTest(TestCase):
    """商品权限测试"""

    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1', password='testpass123', role='resident'
        )
        self.other_user = User.objects.create_user(
            username='other1', password='testpass123', role='resident'
        )
        self.admin_user = User.objects.create_user(
            username='admin1', password='testpass123', role='admin'
        )
        self.product = Product.objects.create(
            title='测试商品', price=Decimal('100.00'),
            condition='good', status='on_sale', seller=self.seller
        )

    def test_seller_can_update(self):
        """测试卖家可以编辑自己的商品"""
        self.client.force_authenticate(user=self.seller)
        response = self.client.patch(
            f'/api/v1/products/{self.product.id}/',
            {'title': '更新后的标题'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, '更新后的标题')

    def test_other_user_cannot_update(self):
        """测试其他用户不能编辑商品"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            f'/api/v1/products/{self.product.id}/',
            {'title': '恶意修改'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_user_cannot_delete(self):
        """测试其他用户不能删除商品"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(f'/api/v1/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_seller_can_delete(self):
        """测试卖家可以删除自己的商品"""
        self.client.force_authenticate(user=self.seller)
        response = self.client.delete(f'/api/v1/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)

    def test_admin_can_update(self):
        """测试管理员可以编辑商品"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            f'/api/v1/products/{self.product.id}/',
            {'title': '管理员修改'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_update(self):
        """测试未认证用户不能编辑商品"""
        response = self.client.patch(
            f'/api/v1/products/{self.product.id}/',
            {'title': '未认证修改'}, format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductRetrieveTest(TestCase):
    """商品详情测试"""

    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1', password='testpass123', role='resident'
        )
        self.product = Product.objects.create(
            title='测试商品', description='商品描述', price=Decimal('100.00'),
            condition='good', status='on_sale', seller=self.seller
        )

    def test_retrieve_increments_view_count(self):
        """测试查看详情增加浏览量"""
        self.assertEqual(self.product.view_count, 0)
        response = self.client.get(f'/api/v1/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.view_count, 1)

        # 再次访问
        self.client.get(f'/api/v1/products/{self.product.id}/')
        self.product.refresh_from_db()
        self.assertEqual(self.product.view_count, 2)

    def test_retrieve_contains_seller_info(self):
        """测试详情包含卖家信息"""
        response = self.client.get(f'/api/v1/products/{self.product.id}/')
        data = response.json()
        self.assertIn('seller_info', data['data'])
        self.assertEqual(data['data']['seller_info']['username'], 'seller1')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductImageReplaceTest(TestCase):
    """商品图片全量替换语义测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='seller_img', password='testpass123', role='resident'
        )
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(
            title='带图商品', price=Decimal('10.00'), seller=self.user
        )
        ProductImage.objects.create(product=self.product, image=create_uploaded_image())
        ProductImage.objects.create(product=self.product, image=create_uploaded_image())

    def test_update_with_images_replaces_old(self):
        """更新时传入 images 为全量替换：旧图删除、新图生效"""
        response = self.client.put(
            f'/api/v1/products/{self.product.pk}/',
            {
                'title': '带图商品（改）',
                'price': '12.00',
                'images': [create_uploaded_image(), create_uploaded_image(), create_uploaded_image()],
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.product.images.count(), 3)

    def test_update_without_images_keeps_old(self):
        """更新时不传 images 字段则保留原有图片"""
        response = self.client.patch(
            f'/api/v1/products/{self.product.pk}/',
            {'title': '只改标题'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.product.images.count(), 2)

    def test_repeated_update_cannot_exceed_nine_images(self):
        """反复追加不再可能：每次替换后总数不超过 9 张"""
        for _ in range(3):
            response = self.client.patch(
                f'/api/v1/products/{self.product.pk}/',
                {'images': [create_uploaded_image() for _ in range(9)]},
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.product.images.count(), 9)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProductCommentLengthTest(TestCase):
    """商品评论长度校验测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='commenter', password='testpass123', role='resident'
        )
        self.product = Product.objects.create(
            title='评论用商品', price=Decimal('5.00'), seller=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_comment_over_500_chars_rejected(self):
        """超过 500 字的评论被拒绝"""
        response = self.client.post(
            f'/api/v1/products/{self.product.pk}/comments/',
            {'content': '好' * 501},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ProductComment.objects.count(), 0)

    def test_comment_at_500_chars_accepted(self):
        """恰好 500 字的评论正常提交"""
        response = self.client.post(
            f'/api/v1/products/{self.product.pk}/comments/',
            {'content': '好' * 500},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductComment.objects.count(), 1)
