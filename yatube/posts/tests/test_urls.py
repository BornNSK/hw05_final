from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Group, Post, User


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template_for_every_users(self):
        """URL-адрес использует соответствующий
        шаблон для всех пользователей.
        """
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': f'/profile/{self.post.author}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_uses_correct_template_for_authorized_users(self):
        """URL-адрес использует соответствующий шаблон для
        зарегестрированных пользователей.
        """
        templates_url_names = {f'/posts/{self.post.id}/edit/':
                               'posts/create_post.html',
                               '/create/': 'posts/create_post.html'
                               }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def error_404_test(self):
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
