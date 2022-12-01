from django import forms
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.urls import reverse
import shutil
import tempfile
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Group, Post, User, Follow
from ..views import NUMBER_OF_POSTS


User = get_user_model()

TEMP_NUMB_FIRST_PAGE = 13
TEMP_NUMB_SECOND_PAGE = 3

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_two = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                         b'\x01\x00\x80\x00\x00\x00\x00\x00'
                         b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                         b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                         b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                         b'\x0A\x00\x3B'
                         )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

        cls.following = Follow.objects.get_or_create(
            user=cls.user,
            author=cls.post.author,
        )

        cls.form_data = {'group': cls.group.pk,
                         'text': 'Тестовый текст',
                         'image': cls.uploaded,
                         }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_two = Client()
        self.authorized_client_two.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'auth'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': '1'}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': '1'}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'),
                                              data=self.form_data
                                              )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image.name

        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'].object_list[0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_group_slug_0 = first_object.group.slug
        post_group_description_0 = first_object.group.description
        post_image_0 = first_object.image.name

        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_group_slug_0, 'test-slug')
        self.assertEqual(post_group_description_0, 'Тестовое описание')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'}))
        first_object = response.context['page_obj'].object_list[0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_group_slug_0 = first_object.group.slug
        post_group_description_0 = first_object.group.description
        post_image_0 = first_object.image.name

        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_author_0, 'auth')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_group_slug_0, 'test-slug')
        self.assertEqual(post_group_description_0, 'Тестовое описание')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id': '1'})
                                              )
        self.assertEqual(response.context.get
                         ('post').author.username, 'auth'
                         )
        self.assertEqual(response.context.get('post').text, 'Тестовый пост')
        self.assertEqual(response.context.get('post').image.name,
                         'posts/small.gif'
                         )
        self.assertEqual(response.context.get('post').group.title,
                         'Тестовая группа'
                         )

    def test_update_post_page_show_correct_context(self):
        """Шаблон update_post сформирован с правильными формами."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id': '1'})
                                              )
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.models.ModelChoiceField,
                       }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильными формами."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField,
                       }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_authorized_user_post_comment(self):
        """Добавление коммента авторизованным пользователем"""
        self.authorized_client.post(reverse('posts:add_comment',
                                    kwargs={'post_id': self.post.id}),
                                    {'text': "круто"},
                                    follow=True
                                    )
        response = self.authorized_client.get(f'/posts/{self.post.id}/')
        self.assertContains(response, 'круто')

    def test_autorized_user_followed(self):
        """Проверка подписки на пользователя."""
        self.authorized_client.post(reverse('posts:profile_follow',
                                            kwargs={'username': 'auth'})
                                    )
        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=self.post.author,
                                                  ).exists())

    def test_autorized_user_unfollowed(self):
        """Проверка отписки от пользователя."""
        self.authorized_client.post(reverse('posts:profile_unfollow',
                                            kwargs={'username': 'auth'}
                                            )
                                    )
        self.assertFalse(Follow.objects.filter(user=self.user,
                                               author=self.post.author,
                                               ).exists())

    def test_autorized_user_see_followed_posts(self):
        """Проверка отображения постов при подписки и после отписки"""
        non_followed_post = Follow.objects.count()
        self.authorized_client.post(reverse('posts:profile_follow',
                                            kwargs={'username': 'auth'},
                                            )
                                    )
        self.assertEqual(Follow.objects.count(), non_followed_post)
        self.authorized_client.post(reverse('posts:profile_unfollow',
                                            kwargs={'username': 'auth'})
                                    )
        self.assertEqual(Follow.objects.count(), non_followed_post - 1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_client = Client()
        cls.author = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(title='test_title',
                                         description='test_description',
                                         slug='test-slug'
                                         )

    def setUp(self):
        cache.clear()
        for post_temp in range(TEMP_NUMB_FIRST_PAGE):
            Post.objects.create(text=f'text{post_temp}',
                                author=self.author, group=self.group
                                )

    def test_first_page_contains_ten_records(self):
        """Проверка паджинатора на первой странице
        для index, group_list, profile.
        """
        templates_pages_names = {'posts/index.html': reverse('posts:index'),
                                 'posts/group_list.html': reverse
                                 ('posts:group_list',
                                  kwargs={'slug': self.group.slug}
                                  ), 'posts/profile.html': reverse
                                 ('posts:profile',
                                  kwargs={'username': self.author}
                                  ),
                                 }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), NUMBER_OF_POSTS
                )

    def test_second_page_contains_three_records(self):
        """Проверка паджинатора на второй странице для
        index, group_list, profile.
        """
        templates_pages_names = {'posts/index.html':
                                 reverse('posts:index')
                                 + '?page=2',
                                 'posts/group_list.html':
                                 reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug}
                                         ) + '?page=2',
                                 'posts/profile.html':
                                 reverse('posts:profile',
                                         kwargs={'username': self.author}
                                         )
                                 + '?page=2',
                                 }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 TEMP_NUMB_SECOND_PAGE
                                 )
