import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug="test_slug",
            description="Тестовое описание группы",
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
            text="Тестовый текст, тестовый текст",
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

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile",
                kwargs={"username": self.user_author.username},
            ): "posts/profile.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.id}
            ): "posts/create_post.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ): "posts/post_detail.html",
        }

        for reverse_name, template in templates_pages_names.items():  # Act
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.post_author.get(reverse("posts:index"))  # Act

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

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.post_author.get(  # Act
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

    def test_profile_shows_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.post_author.get(  # Act
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

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.post_author.get(  # Act
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )

        self.assertEqual(response.context.get("post").author, self.post.author)
        self.assertEqual(
            response.context.get("post").pub_date, self.post.pub_date
        )
        self.assertEqual(response.context.get("post").text, self.post.text)
        self.assertEqual(response.context.get("post").group, self.post.group)
        self.assertEqual(response.context.get("post").image, self.post.image)

    def test_post_create_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.post_author.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():  # Act
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом
        в режиме редактирования.
        """
        response = self.post_author.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():  # Act
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_another_post_appearance(self):
        """При создании пост появляется на главной странице сайта,
        на странице указанной группы и в профайле пользователя.
        """
        another_post = Post.objects.create(
            author=self.user_author,
            text="Тестовый текст другого поста",
            group=self.group,
        )
        pages = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse(
                "posts:profile", kwargs={"username": self.user_author.username}
            ),
        ]

        for rev in pages:  # Act
            with self.subTest(rev=rev):
                response = self.post_author.get(rev)
                self.assertIn(another_post, response.context["page_obj"])

    def test_another_post_not_in_wrong_group(self):
        """При создании пост не попал в группу,
        для которой не был предназначен.
        """
        self.another_group = Group.objects.create(
            title="Тестовое название другой группы",
            slug="another_test_slug",
            description="Тестовое описание другой группы",
        )
        another_post = Post.objects.create(
            author=self.user_author,
            text="Тестовый текст другого поста",
            group=self.group,
        )

        response = self.post_author.get(  # Act
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

        response = self.post_author.get(  # Act
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )

        self.assertIn(comment, response.context["comments"])

    def test_index_page_cache(self):
        """Проверка работы кеша главной страницы."""
        post = Post.objects.create(
            text="Тестовый текст", author=self.post.author, group=self.group
        )

        post_on_index = self.post_author.get(  # Act
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
            username="auth",
        )
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug="test_slug",
            description="Тестовое описание группы",
        )
        Post.objects.bulk_create(
            [
                Post(text="Тестовый текст", author=cls.user, group=cls.group)
                for i in range(13)
            ]
        )

    def setUp(self):
        self.unauthorized_client = Client()
        cache.clear()

    def test_first_index_page_contains_ten_records(self):
        response = self.client.get(reverse("posts:index"))  # Act

        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_index_page_contains_three_records(self):
        response = self.client.get(reverse("posts:index") + "?page=2")  # Act

        self.assertEqual(len(response.context["page_obj"]), 3)

    def test_first_group_list_page_contains_ten_records(self):
        response = self.client.get(  # Act
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )

        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_group_list_contains_three_records(self):
        response = self.client.get(  # Act
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
            + "?page=2"
        )

        self.assertEqual(len(response.context["page_obj"]), 3)

    def test_first_profile_page_contains_ten_records(self):
        response = self.client.get(  # Act
            reverse(
                "posts:profile",
                kwargs={"username": self.user.username},
            )
        )

        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_profile_contains_three_records(self):
        response = self.client.get(  # Act
            reverse(
                "posts:profile",
                kwargs={"username": self.user.username},
            )
            + "?page=2"
        )

        self.assertEqual(len(response.context["page_obj"]), 3)


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
        self.another_auth_user.get(  # Act
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.post.author.username},
            )
        )

        follow_obj = Follow.objects.latest("id")
        self.assertEqual(follow_obj.author_id, self.user.id)
        self.assertEqual(follow_obj.user_id, self.another_user.id)

    def test_authorized_user_unfollow(self):
        """Авторизованный пользователь может отписаться на автора поста."""
        Follow.objects.create(author=self.user, user=self.another_user)
        follows_count = Follow.objects.count()

        self.another_auth_user.get(  # Act
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": self.post.author.username},
            )
        )

        self.assertEqual(Follow.objects.count(), follows_count - 1)

    def test_follow_post_on_follow_page(self):
        """После подписки пост попадает на страницу подписок."""
        Follow.objects.create(author=self.user, user=self.another_user)

        follow_list = (  # Act
            self.another_auth_user.get(reverse("posts:follow_index"))
            .context["page_obj"]
            .object_list
        )

        self.assertIn(self.post, follow_list)

    def test_follow_post_not_in_wrong_page(self):
        """После подписки пост не попал на ненужную страницу."""
        Follow.objects.create(author=self.user, user=self.another_user)

        follow_list = (  # Act
            self.authorized_author.get(reverse("posts:follow_index"))
            .context["page_obj"]
            .object_list
        )
        self.assertNotIn(self.post, follow_list)
