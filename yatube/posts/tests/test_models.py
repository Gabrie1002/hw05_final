from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_title = 'Test group!'
        group_slug = 'Test slug!'
        group_description = 'Test description!'
        post_text = 'Test text for post'
        user_name = 'auth'
        cls.user = User.objects.create_user(username=user_name)
        cls.group = Group.objects.create(
            title=group_title,
            slug=group_slug,
            description=group_description,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=post_text,
        )

    def test_models_have_correct_name(self):
        """Проверка заголовка группы"""
        group = PostModelTest.group
        expected_title = group.title
        self.assertEqual(expected_title, str(group), 'Выводит не так group')

    def test_models_use_correct_name(self):
        """Проверка текста, описывающего группу"""
        post = PostModelTest.post
        expected_text = post.text[:15]
        self.assertEqual(expected_text, str(post), 'Выводит не так text')
