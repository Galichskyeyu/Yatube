import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username="user_author")
        cls.another_user = User.objects.create_user(username="another_user")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post_author = Client()
        self.post_author.force_login(self.user_author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.another_user)

    def test_valid_create_form_create_post(self):
        '''При отправке валидной формы со страницы создания поста
        создаётся новая запись.'''
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый текст поста",
            "group": self.group.pk,
            "image": uploaded,
        }
        response = self.post_author.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile", kwargs={"username": self.user_author.username}
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        latest_post = Post.objects.latest("id")
        self.assertEqual(latest_post.text, form_data["text"])
        self.assertEqual(latest_post.group.pk, form_data["group"])
        self.assertEqual(latest_post.author, self.user_author)
        self.assertEqual(latest_post.image, "posts/small.gif")

    def test_valid_edit_form_edit_post(self):
        '''При отправке валидной формы со страницы редактирования поста
        происходит изменение записи.'''
        post = Post.objects.create(
            text="Тестовый текст поста",
            author=self.user_author,
            group=self.group,
        )
        form_data = {
            "text": "Отредактированный в форме текст",
            "group": self.group.pk,
        }
        response = self.post_author.post(
            reverse("posts:post_edit", kwargs={"post_id": post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.pk}),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post.refresh_from_db()
        self.assertEqual(post.text, form_data["text"])

    def test_valid_post_detail_form_create_comment(self):
        '''Комментировать могут только авторизованные пользователи.'''
        post = Post.objects.create(
            text="Тестовый текст поста",
            author=self.user_author,
            group=self.group,
        )
        form_data = {
            "text": "Тестовый текст комментария",
        }
        response = self.authorized_user.post(
            reverse("posts:add_comment", kwargs={"post_id": post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.pk}),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        comment = Comment.objects.latest("pk")
        self.assertEqual(comment.text, form_data["text"])
        self.assertEqual(comment.post.pk, post.pk)
