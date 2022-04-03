from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_title = 'Test Group'
        group_slug = 'testslug'
        group_description = 'Test'
        post_text = 'Test Text'
        user_name = 'HasNoName'
        cls.user = User.objects.create_user(username=user_name)
        cls.group = Group.objects.create(
            title=group_title,
            slug=group_slug,
            description=group_description,
        )
        Post.objects.create(
            text=post_text,
            author=cls.user,
            group=cls.group,
        )

        cls.template_urls_anonimus = {
            HTTPStatus.OK: [
                '/', '/group/testslug/', '/profile/HasNoName/', '/posts/1/'
            ],
            HTTPStatus.NOT_FOUND: ['/anypage'],
        }

        cls.template_urls_auth = {
            HTTPStatus.OK: ['/create/', '/posts/1/edit/'],
            HTTPStatus.NOT_FOUND: ['/anypage'],
        }

        cls.template_urls = {
            '/auth/login/?next=/posts/1/edit/': '/posts/1/edit/',
            '/auth/login/?next=/create/': '/create/',
            '/auth/login/?next=/posts/1/comment/': '/posts/1/comment/',
        }

        cls.template_urls_names = {
            '/': 'posts/index.html',
            '/group/testslug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_anonymous_get_page(self):
        """Страницы доступные гостю сайта"""
        for template, address in self.template_urls_anonimus.items():
            for addres in address:
                with self.subTest(addres=addres):
                    response = self.guest_client.get(addres)
                    self.assertEqual(response.status_code, template)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /edit/ и /create/ перенаправит анонимного
        пользователя на страницу логина."""
        for template, address in self.template_urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, template)

    def test_authorized_client_url(self):
        """Страницы доступные авторизованному пользователю"""
        for template, address in self.template_urls_auth.items():
            for addres in address:
                with self.subTest(addres=addres):
                    response = self.authorized_client.get(addres)
                    self.assertEqual(response.status_code, template)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.template_urls_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
