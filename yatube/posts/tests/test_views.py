import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile


from ..models import Group, Post, User, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_title = 'Test Group'
        cls.group_slug = 'testslug'
        cls.group_description = 'Test'
        cls.post_text = 'Test Text'
        cls.user_name = 'HasNoName'
        cls.user = User.objects.create_user(username=cls.user_name)
        cls.group = Group.objects.create(
            title=cls.group_title,
            slug=cls.group_slug,
            description=cls.group_description,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        Post.objects.create(
            text=cls.post_text,
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

        cls.template_pages_names = {
            'posts/index.html': [reverse('posts:index')],
            'posts/group_list.html': [reverse(
                'posts:group_list', kwargs={'slug': cls.group_slug}
            )],
            'posts/profile.html': [reverse(
                'posts:profile', kwargs={'username': cls.user_name}
            )],
            'posts/post_detail.html': [reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            )],
            'posts/post_create.html': [reverse('posts:post_create'), reverse(
                'posts:post_edit', kwargs={'post_id': '1'}
            )],
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_names in self.template_pages_names.items():
            for reverse_name in reverse_names:
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        get = response.context['page_obj'].object_list[0].text

        response_group = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_slug}
        ))
        get_group = response_group.context['post'].group.title

        response_profile = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user_name}
        ))
        get_profile = response_profile.context['user'].username

        response_post_detail = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'}
        ))
        get_post_detail = response_post_detail.context['post'].text

        context = {
            get: self.post_text,
            get_group: self.group_title,
            get_profile: self.user_name,
            get_post_detail: self.post_text,
        }
        for gets, expect in context.items():
            with self.subTest(gets=gets):
                self.assertEqual(gets, expect)

    def test_post_create_show_correct_context(self):
        """/create/ выводит правильный context"""
        response_post_create = self.authorized_client.get(reverse(
            'posts:post_create'
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_post_create.context.get(
                    'form'
                ).fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """/post_edit/ выводит правильный context"""
        response_post_edit = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': '1'}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_post_edit.context.get(
                    'form'
                ).fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue('is_edit')

    def test_equal_index_profile_group(self):
        response_index = self.client.get(reverse('posts:index'))
        index = list(response_index.context.get('page_obj').object_list)

        response_group = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_slug}
        ))
        group = response_group.context.get('page_obj').object_list

        response_profile = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user_name}
        ))
        profile = response_profile.context.get('page_obj').object_list
        self.assertEqual(index, group)
        self.assertEqual(index, profile)
        self.assertEqual(profile, group)

    def test_image_pages(self):
        address = {
            'posts:index': '',
            'posts:group_list': {'slug': self.group_slug},
            'posts:profile': {'username': self.user_name},
        }
        for key, value in address.items():
            with self.subTest(key=key):
                response = self.authorized_client.get(reverse(
                    key, kwargs=value
                ))
                form_field = response.context['page_obj'][0].image
                self.assertEqual(form_field, 'posts/small.gif')

    def test_image_post_detail(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'}
        ))
        form_field = response.context['post'].image.name
        self.assertEqual(form_field, 'posts/small.gif')


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_title = 'Test Group'
        cls.group_slug = 'testslug'
        cls.group_description = 'Test'
        cls.post_text = 'Test Text'
        cls.user_name = 'PaginatorName'
        cls.user = User.objects.create_user(username=cls.user_name)
        cls.group = Group.objects.create(
            title=cls.group_title,
            slug=cls.group_slug,
            description=cls.group_description,
        )
        cls.FIRST_PAGE = 10
        cls.SECOND_PAGE = 5
        for post in range(15):
            Post.objects.create(
                text=cls.post_text + str(post),
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_contains_ten_records(self):
        """Проверка верной пагинации на index"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), self.FIRST_PAGE)

    def test_index_page_contains_five_records(self):
        """Проверка верной пагинации на index"""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), self.SECOND_PAGE)

    def test_group_page_contains_ten_records(self):
        """Проверка верной пагинации на group_list"""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_slug}
        ))
        self.assertEqual(len(response.context['page_obj']), self.FIRST_PAGE)

    def test_group_page_contains_five_records(self):
        """Проверка верной пагинации на group_list"""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_slug}
        ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), self.SECOND_PAGE)

    def test_profile_page_contains_ten_records(self):
        """Проверка верной пагинации на profile"""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user_name}
        ))
        self.assertEqual(len(response.context['page_obj']), self.FIRST_PAGE)

    def test_profile_page_contains_five_records(self):
        """Проверка верной пагинации на profile"""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user_name}
        ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), self.SECOND_PAGE)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_title = 'Test Group'
        cls.group_slug = 'testslug'
        cls.group_description = 'Test'
        cls.post_text = 'Test Text'
        cls.user_name = 'CacheName'
        cls.user = User.objects.create_user(username=cls.user_name)
        Post.objects.create(
            text=cls.post_text,
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        post_obj = Post.objects.create(
            text='simple text',
            author=self.user,
        )
        response = self.client.get(reverse('posts:index')).content
        post_obj.delete()
        new = self.client.get(reverse('posts:index')).content
        self.assertEqual(response, new)
        cache.clear()
        self.assertNotEqual(
            response,
            self.client.get(reverse('posts:index')).content
        )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_title = 'Test Group'
        cls.group_slug = 'testslug'
        cls.group_description = 'Test'
        cls.post_text = 'Test Text'
        cls.user_name = 'FollowName'
        cls.user = User.objects.create_user(username=cls.user_name)
        cls.another = User.objects.create_user(username='another')
        Post.objects.create(
            text=cls.post_text,
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_user_can_follow(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.another}
        ))
        self.assertTrue(Follow.objects.filter(author=self.another).exists())

    def test_user_can_unfollow(self):
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.another}
        ))
        self.assertFalse(Follow.objects.filter(author=self.another).exists())

    def test_follow_index_show_context(self):
        Post.objects.create(
            text='test',
            author=self.another
        )
        Follow.objects.create(
            author=self.another,
            user=self.user
        )
        response = self.authorized_client.get(reverse(
            'posts:follow_index'
        ))
        get = response.context['post'].text
        self.assertEqual(get, 'test')

    def test_follow_index_context(self):
        Follow.objects.filter(
            author=self.another,
            user=self.user
        ).delete()
        response = self.authorized_client.get(reverse(
            'posts:follow_index'
        ))
        response_another = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user_name}
        ))
        get = response.context['page_obj'].object_list
        posts_another = response_another.context['page_obj'].object_list
        self.assertNotEqual(get, posts_another)
