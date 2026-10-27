"""
经验问答模块单元测试
"""
from unittest.mock import patch

from django.db import IntegrityError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.users.models import User
from common.utils import toggle_like
from .models import Question, Answer, QuestionTag, QuestionLike, AnswerLike


class QuestionAPITest(APITestCase):
    """问题接口测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='asker1', password='pass123456', role='resident'
        )
        self.other = User.objects.create_user(
            username='answerer1', password='pass123456', role='resident'
        )
        self.tag = QuestionTag.objects.create(name='装修', slug='zhuangxiu')
        self.question = Question.objects.create(
            title='如何选地板？', content='家里装修想选木地板', author=self.user
        )
        self.question.tags.add(self.tag)
        self.client = APIClient()

    def test_create_question(self):
        """测试提问"""
        self.client.force_authenticate(user=self.user)
        data = {'title': '新问题', 'content': '问题描述', 'tags': ['育儿']}
        response = self.client.post('/api/v1/questions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(QuestionTag.objects.filter(name='育儿').exists())

    def test_list_questions(self):
        """测试问题列表"""
        response = self.client.get('/api/v1/questions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_increments_view(self):
        """测试浏览量递增"""
        response = self.client.get(f'/api/v1/questions/{self.question.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertEqual(self.question.view_count, 1)

    def test_add_answer(self):
        """测试回答问题"""
        self.client.force_authenticate(user=self.other)
        data = {'content': '建议选实木复合地板'}
        response = self.client.post(
            f'/api/v1/questions/{self.question.pk}/answer/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.question.refresh_from_db()
        self.assertEqual(self.question.answer_count, 1)

    def test_accept_answer(self):
        """测试采纳回答"""
        answer = Answer.objects.create(
            question=self.question, author=self.other, content='好回答'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            f'/api/v1/questions/{self.question.pk}/accept/',
            {'answer_id': answer.pk}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        answer.refresh_from_db()
        self.question.refresh_from_db()
        self.assertTrue(answer.is_accepted)
        self.assertTrue(self.question.is_solved)

    def test_accept_by_non_author_forbidden(self):
        """测试非提问者不能采纳"""
        answer = Answer.objects.create(
            question=self.question, author=self.other, content='回答'
        )
        self.client.force_authenticate(user=self.other)
        response = self.client.put(
            f'/api/v1/questions/{self.question.pk}/accept/',
            {'answer_id': answer.pk}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_like_question(self):
        """测试点赞问题"""
        self.client.force_authenticate(user=self.other)
        response = self.client.post(f'/api/v1/questions/{self.question.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertEqual(self.question.like_count, 1)

    def test_like_answer(self):
        """测试点赞回答：记录创建、计数 +1、返回 liked=True"""
        answer = Answer.objects.create(
            question=self.question, author=self.other, content='好回答'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/v1/questions/{self.question.pk}/answers/{answer.pk}/like/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['liked'])
        self.assertEqual(response.data['data']['like_count'], 1)
        answer.refresh_from_db()
        self.assertEqual(answer.like_count, 1)
        self.assertTrue(
            AnswerLike.objects.filter(answer=answer, user=self.user).exists()
        )

    def test_unlike_answer(self):
        """测试取消回答点赞：记录删除、计数归 0、返回 liked=False"""
        answer = Answer.objects.create(
            question=self.question, author=self.other, content='好回答'
        )
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/questions/{self.question.pk}/answers/{answer.pk}/like/'
        self.client.post(url)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['data']['liked'])
        self.assertEqual(response.data['data']['like_count'], 0)
        answer.refresh_from_db()
        self.assertEqual(answer.like_count, 0)
        self.assertFalse(
            AnswerLike.objects.filter(answer=answer, user=self.user).exists()
        )

    def test_like_answer_of_other_question_404(self):
        """测试不能跨问题点赞回答"""
        answer = Answer.objects.create(
            question=self.question, author=self.other, content='好回答'
        )
        other_question = Question.objects.create(
            title='另一个问题', content='其他内容', author=self.user
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/v1/questions/{other_question.pk}/answers/{answer.pk}/like/'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(AnswerLike.objects.count(), 0)

    def test_answer_like_requires_auth(self):
        """测试回答点赞需要登录"""
        answer = Answer.objects.create(
            question=self.question, author=self.other, content='好回答'
        )
        response = self.client.post(
            f'/api/v1/questions/{self.question.pk}/answers/{answer.pk}/like/'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_toggle_like_concurrent_first_like_idempotent(self):
        """测试并发首赞唯一约束冲突时幂等返回已赞、不重复计数也不误删"""
        answer = Answer.objects.create(
            question=self.question, author=self.other, content='好回答'
        )
        # 模拟并发：查询时无记录（DB 确实无记录），create 时被唯一约束拦截
        with patch.object(
            AnswerLike.objects, 'create', side_effect=IntegrityError('unique')
        ):
            liked, like_count = toggle_like(AnswerLike, answer, self.user, 'answer')
        self.assertTrue(liked)
        self.assertEqual(like_count, 0)
        answer.refresh_from_db()
        self.assertEqual(answer.like_count, 0)
        self.assertEqual(AnswerLike.objects.count(), 0)

    def test_delete_own_question(self):
        """测试删除自己的问题"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/v1/questions/{self.question.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_others_forbidden(self):
        """测试不能删除他人问题"""
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f'/api/v1/questions/{self.question.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create(self):
        """测试未登录不能提问"""
        data = {'title': '匿名问题', 'content': '内容'}
        response = self.client.post('/api/v1/questions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
