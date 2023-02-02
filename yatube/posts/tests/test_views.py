import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.user_author = User.objects.create_user(username="user_author")
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            text="Тестовый текст поста",
            author=cls.user_author,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post_author = Client()
        self.post_author.force_login(self.user_author)
        cache.clear()

    def test_home_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.post_author.get(reverse("posts:index"))
        self.assertEqual(
            response.context.get("page_obj")[0].text, self.post.text
        )
        self.assertEqual(
            response.context.get("page_obj")[0].author, self.post.author
        )
        self.assertEqual(
            response.context.get("page_obj")[0].group, self.post.group
        )
        self.assertEqual(
            response.context.get("page_obj")[0].pub_date, self.post.pub_date
        )
        self.assertEqual(
            response.context.get("page_obj")[0].image, self.post.image
        )

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        self.assertEqual(response.context.get("group").title, self.group.title)
        self.assertEqual(
            response.context.get("group").description, self.group.description
        )
        self.assertEqual(
            response.context.get("page_obj")[0].author, self.post.author
        )
        self.assertEqual(
            response.context.get("page_obj")[0].pub_date, self.post.pub_date
        )
        self.assertEqual(
            response.context.get("page_obj")[0].text, self.post.text
        )
        self.assertEqual(
            response.context.get("page_obj")[0].image, self.post.image
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse(
                "posts:profile", kwargs={"username": self.user_author.username}
            )
        )
        self.assertEqual(response.context.get("author"), self.post.author)
        self.assertEqual(
            response.context.get("page_obj")[0].author, self.post.author
        )
        self.assertEqual(
            response.context.get("page_obj")[0].pub_date, self.post.pub_date
        )
        self.assertEqual(
            response.context.get("page_obj")[0].text, self.post.text
        )
        self.assertEqual(
            response.context.get("page_obj")[0].image, self.post.image
        )

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk})
        )
        self.assertEqual(response.context.get("post").author, self.post.author)
        self.assertEqual(
            response.context.get("post").pub_date, self.post.pub_date
        )
        self.assertEqual(response.context.get("post").text, self.post.text)
        self.assertEqual(response.context.get("post").group, self.post.group)
        self.assertEqual(response.context.get("post").image, self.post.image)

    def test_create_post_show_correct_context(self):
        """Шаблон создания записи create_post.html сформирован
        с правильным контекстом."""
        response = self.post_author.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_edit_show_correct_context(self):
        """Шаблон редактирования записи create_post.html сформирован
        с правильным контекстом."""
        response = self.post_author.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_home_group_list_profile_pages(self):
        """При создании пост появляется на главной странице сайта,
        на странице указанной группы и в профайле пользователя."""
        another_post = Post.objects.create(
            author=self.user_author,
            text="Тестовый текст поста",
            group=self.group,
        )
        pages = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse(
                "posts:profile", kwargs={"username": self.user_author.username}
            ),
        ]
        for rev in pages:
            with self.subTest(rev=rev):
                response = self.post_author.get(rev)
                self.assertIn(another_post, response.context["page_obj"])

    def test_post_not_another_group(self):
        """Созданный пост не попал в группу,
        для которой не был предназначен."""
        self.another_group = Group.objects.create(
            title="Дополнительная тестовая группа",
            slug="test-another-slug",
            description="Тестовое описание дополнительной тестовой группы",
        )
        another_post = Post.objects.create(
            author=self.user_author,
            text="Тестовый текст поста дополнительной тестовой группы",
            group=self.group,
        )
        response = self.post_author.get(
            reverse(
                "posts:group_list", kwargs={"slug": self.another_group.slug}
            )
        )
        self.assertNotIn(another_post, response.context["page_obj"])

    def test_comment_post_appearance(self):
        """При создании комментарий появляется на странице поста."""
        comment = Comment.objects.create(
            author=self.post.author,
            text="Тестовый текст комментария",
            post=self.post,
        )
        response = self.post_author.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk})
        )
        self.assertIn(comment, response.context["comments"])

    def test_index_page_cache(self):
        """Тест для проверки кеширования главной страницы."""
        post = Post.objects.create(
            text="Тестовый текст", author=self.post.author, group=self.group
        )
        post_on_index = self.post_author.get(
            reverse("posts:index")
        ).content
        post.delete()
        post_on_index_delete = self.post_author.get(
            reverse("posts:index")
        ).content
        self.assertEqual(post_on_index, post_on_index_delete)
        cache.clear()
        post_on_index_delete_cache = self.post_author.get(
            reverse("posts:index")
        ).content
        self.assertNotEqual(post_on_index_delete, post_on_index_delete_cache)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='auth',
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        for i in range(13):
            Post.objects.create(
                text=f'Пост #{i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.unauthorized_client = Client()
        cache.clear()

    def test_paginator_on_pages(self):
        """Проверка работы Paginator на страницах."""
        posts_on_first_page = 10
        posts_on_second_page = 3
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for pages in url_pages:
            with self.subTest(pages=pages):
                self.assertEqual(len(self.unauthorized_client.get(
                    pages).context.get('page_obj')),
                    posts_on_first_page
                )
                self.assertEqual(len(self.unauthorized_client.get(
                    pages + '?page=2').context.get('page_obj')),
                    posts_on_second_page
                )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="author")
        cls.another_user = User.objects.create(username="another_user")
        cls.post = Post.objects.create(text="Тестовый текст", author=cls.user)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)
        self.another_auth_user = Client()
        self.another_auth_user.force_login(self.another_user)

    def test_authorized_user_follow(self):
        """Авторизованный пользователь может подписаться на автора поста."""
        self.another_auth_user.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.post.author.username},
            )
        )
        follow_obj = Follow.objects.latest("pk")
        self.assertEqual(follow_obj.author_id, self.user.pk)
        self.assertEqual(follow_obj.user_id, self.another_user.pk)

    def test_authorized_user_unfollow(self):
        """Авторизованный пользователь может отписаться от автора поста."""
        Follow.objects.create(author=self.user, user=self.another_user)
        follows_count = Follow.objects.count()
        self.another_auth_user.get(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": self.post.author.username},
            )
        )
        self.assertEqual(Follow.objects.count(), follows_count - 1)

    def test_follow_post_on_follow_page(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        Follow.objects.create(author=self.user, user=self.another_user)
        follow_list = (
            self.another_auth_user.get(reverse("posts:follow_index"))
            .context["page_obj"]
            .object_list
        )
        self.assertIn(self.post, follow_list)

    def test_follow_post_on_unfollow_page(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто не подписан."""
        Follow.objects.create(author=self.user, user=self.another_user)
        follow_list = (
            self.authorized_author.get(reverse("posts:follow_index"))
            .context["page_obj"]
            .object_list
        )
        self.assertNotIn(self.post, follow_list)
