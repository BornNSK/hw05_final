from django.contrib.auth import get_user_model
from django.core.cache import cache
import shutil
import tempfile
from django.conf import settings
from posts.forms import Post
from posts.models import Post
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from ..models import Group, Post, Comment
from http import HTTPStatus

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='nonauth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
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
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()

        form_data = {'group': self.group.pk,
                     'text': 'Тестовый текст',
                     'image': self.uploaded,
                     }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user})
                             )
        self.assertTrue(Post.objects.filter(group=form_data['group'],
                                            text=form_data['text'],
                                            image='posts/small.gif',
                                            ).exists())
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_edit_post(self):
        """Валидная форма редактирования запись в Post."""
        post_count = Post.objects.count()
        form_data = {'group': self.group.pk,
                     'text': self.post.text + '1',
                     }
        response = self.authorized_client.post(reverse('posts:post_edit',
                                               kwargs={'post_id':
                                                       self.post.id
                                                       }),
                                               data=form_data,
                                               follow=True
                                               )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       self.post.id
                                                       })
                             )
        self.assertEqual(Post.objects.count(), post_count)
        upd_post = Post.objects.get(id=self.post.id)
        self.assertEqual(upd_post.text, self.post.text + '1')
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_guest_user_edit_post(self):
        """Проверка гостевого пользователя
        на то, что он не может редактировать пост.
        """
        post_count = Post.objects.count()
        form_data = {'group': self.group.pk,
                     'text': 'Тестовый текст',
                     }
        response = self.client.post(reverse
                                    ('posts:post_edit',
                                     kwargs={'post_id':
                                             self.post.id
                                             },
                                     ), data=form_data,
                                    follow=True
                                    )
        self.assertRedirects(response, reverse('users:login')
                             + "?next=" + reverse('posts:post_edit',
                             kwargs={'post_id': self.post.id})
                             )
        self.assertEqual(Post.objects.count(), post_count)
        upd_post = Post.objects.get(id=self.post.id)
        self.assertEqual(upd_post.text, self.post.text)
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_non_author_user_edit_post(self):
        """Проверка другого пользователя
        на то, что он не может редактировать не свой пост.
        """
        post_count = Post.objects.count()
        form_data = {'group': self.group.pk,
                     'text': 'Тестовый текст',
                     }
        response = self.authorized_client1.post(reverse('posts:post_edit',
                                                        kwargs={'post_id':
                                                                self.post.id
                                                                },
                                                        ), data=form_data,
                                                follow=True
                                                )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       self.post.id
                                                       }
                                               )
                             )
        self.assertEqual(Post.objects.count(), post_count)
        upd_post = Post.objects.get(id=self.post.id)
        self.assertEqual(upd_post.text, self.post.text)
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_guest_user_create_post(self):
        """Проверка гостевого пользователя
        что он не может создать пост.
        """
        post_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст123', }
        response = self.guest.post(reverse('posts:post_create'),
                                   data=form_data,
                                   follow=True
                                   )
        self.assertRedirects(response, reverse('users:login')
                             + "?next=" + reverse('posts:post_create')
                             )
        self.assertEqual(Post.objects.count(), post_count)

    def test_authorized_user_add_comment(self):
        """Авторизованный пользователь создаёт комментарий."""
        aut_comment_count = Comment.objects.count()
        form_data = {'text': 'Комментарии'}
        response = self.authorized_client.post(reverse('posts:add_comment',
                                                       kwargs={'post_id':
                                                               self.post.id
                                                               },
                                                       ),
                                               data=form_data,
                                               follow=True
                                               )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       self.post.id
                                                       }))
        self.assertEqual(Comment.objects.count(), aut_comment_count+1)
        self.assertTrue(Comment.objects.filter(text=form_data['text'],
                                               author=self.user,
                                               post=self.post,).exists())

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response_one = self.authorized_client.get(reverse('posts:index'))
        posts = response_one.content
        Post.objects.create(
            text='test_new_post',
            author=self.post.author,
        )
        response_two = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_two.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_three = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_three.content
        self.assertNotEqual(old_posts, new_posts)
