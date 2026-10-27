"""
自由发言模块单元测试

覆盖帖子 CRUD、评论、点赞、权限控制等核心功能。
"""
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.users.models import User
from .models import Post, Comment, PostLike


class PostAPITest(APITestCase):
    """帖子接口测试"""
    
    def setUp(self):
        """创建测试用户和帖子"""
        self.user = User.objects.create_user(
            username='poster1', password='pass123456', role='resident'
        )
        self.admin = User.objects.create_user(
            username='admin1', password='pass123456', role='admin'
        )
        self.other_user = User.objects.create_user(
            username='viewer1', password='pass123456', role='resident'
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='这是一条测试内容',
            author=self.user,
            post_type='chat',
            tags='测试,生活'
        )
        self.client = APIClient()
    
    def test_list_posts(self):
        """测试帖子列表"""
        response = self.client.get('/api/v1/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_post_authenticated(self):
        """测试已登录用户发帖"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': '新帖子',
            'content': '新帖子内容',
            'post_type': 'share',
            'tags': '分享'
        }
        response = self.client.post('/api/v1/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
    
    def test_create_post_unauthenticated(self):
        """测试未登录不能发帖"""
        data = {'title': '匿名帖', 'content': '内容', 'post_type': 'chat'}
        response = self.client.post('/api/v1/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_retrieve_post_increments_view(self):
        """测试查看详情增加浏览量"""
        initial_views = self.post.view_count
        response = self.client.get(f'/api/v1/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, initial_views + 1)
    
    def test_update_own_post(self):
        """测试作者可以编辑自己的帖子"""
        self.client.force_authenticate(user=self.user)
        data = {'title': '修改后的标题'}
        response = self.client.patch(f'/api/v1/posts/{self.post.pk}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, '修改后的标题')
    
    def test_update_others_post_forbidden(self):
        """测试不能编辑他人帖子"""
        self.client.force_authenticate(user=self.other_user)
        data = {'title': '恶意修改'}
        response = self.client.patch(f'/api/v1/posts/{self.post.pk}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_own_post(self):
        """测试作者可以删除自己的帖子"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/v1/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)
    
    def test_admin_can_delete_any_post(self):
        """测试管理员可以删除任何帖子"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/v1/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_notice_type_requires_admin(self):
        """测试普通用户不能发布公告"""
        self.client.force_authenticate(user=self.user)
        data = {'title': '假公告', 'content': '内容', 'post_type': 'notice'}
        response = self.client.post('/api/v1/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PostLikeTest(APITestCase):
    """点赞功能测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='liker1', password='pass123456', role='resident'
        )
        self.post = Post.objects.create(
            title='点赞测试', content='内容', author=self.user, post_type='chat'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_like_post(self):
        """测试点赞"""
        response = self.client.post(f'/api/v1/posts/{self.post.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['liked'])
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 1)
    
    def test_unlike_post(self):
        """测试取消点赞"""
        PostLike.objects.create(post=self.post, user=self.user)
        Post.objects.filter(pk=self.post.pk).update(like_count=1)
        
        response = self.client.post(f'/api/v1/posts/{self.post.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['data']['liked'])
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 0)
    
    def test_like_requires_auth(self):
        """测试未登录不能点赞"""
        client = APIClient()
        response = client.post(f'/api/v1/posts/{self.post.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentTest(APITestCase):
    """评论功能测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='commenter1', password='pass123456', role='resident'
        )
        self.post = Post.objects.create(
            title='评论测试', content='内容', author=self.user, post_type='chat'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_add_comment(self):
        """测试发表评论"""
        data = {'content': '说得好！'}
        response = self.client.post(f'/api/v1/posts/{self.post.pk}/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)
    
    def test_reply_to_comment(self):
        """测试楼中楼回复"""
        parent = Comment.objects.create(
            post=self.post, author=self.user, content='原评论'
        )
        data = {'content': '回复你', 'parent': parent.pk}
        response = self.client.post(f'/api/v1/posts/{self.post.pk}/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)
    
    def test_empty_comment_rejected(self):
        """测试空评论被拒绝"""
        data = {'content': ''}
        response = self.client.post(f'/api/v1/posts/{self.post.pk}/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_comments(self):
        """测试获取评论列表"""
        Comment.objects.create(post=self.post, author=self.user, content='评论1')
        Comment.objects.create(post=self.post, author=self.user, content='评论2')
        
        response = self.client.get(f'/api/v1/posts/{self.post.pk}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PostFeatureTest(APITestCase):
    """置顶/加精功能测试"""
    
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin2', password='pass123456', role='admin'
        )
        self.user = User.objects.create_user(
            username='normal2', password='pass123456', role='resident'
        )
        self.post = Post.objects.create(
            title='管理测试', content='内容', author=self.user, post_type='chat'
        )
    
    def test_admin_can_feature_post(self):
        """测试管理员可以置顶/加精"""
        self.client.force_authenticate(user=self.admin)
        data = {'is_top': True, 'is_featured': True}
        response = self.client.put(
            f'/api/v1/posts/{self.post.pk}/feature/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_top)
        self.assertTrue(self.post.is_featured)
    
    def test_normal_user_cannot_feature(self):
        """测试普通用户不能置顶"""
        self.client.force_authenticate(user=self.user)
        data = {'is_top': True}
        response = self.client.put(
            f'/api/v1/posts/{self.post.pk}/feature/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
