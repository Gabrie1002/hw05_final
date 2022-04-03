import shutil
import tempfile

from ..models import Post, User, Comment
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_text = 'Test Text PostForm'
        cls.user_name = 'PostForm'
        cls.user = User.objects.create_user(username=cls.user_name)
        cls.first_post = Post.objects.create(
            text=cls.post_text,
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Проверка формы создания поста"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        posts_count = Post.objects.count()

        Comment.objects.create(
            post=self.first_post,
            author=self.user,
            text='test text com'
        )

        form_post = {
            'text': 'TEXT',
            'author': self.user,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_post,
            follow=True
        )

        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user_name
        }))

        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(text='TEXT', image='posts/small.gif').exists()
        )

        self.assertTrue(
            Comment.objects.filter(text='test text com').exists()
        )

    def test_edit_post(self):
        """Проверка формы редактирования поста"""
        form_data = {
            'text': 'test_text',
            'author': self.user
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ))
        self.assertTrue(Post.objects.filter(text='test_text'))
