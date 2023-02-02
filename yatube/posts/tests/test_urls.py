from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class StaticURLTests(TestCase):
    def setUp(self):
        self.unauthorized_user = Client()

    def test_unexisting_page(self):
        response = self.unauthorized_user.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.user_author = User.objects.create_user(username="user_author")
        cls.another_user = User.objects.create_user(username="another_user")
        cls.post = Post.objects.create(
            text="Тестовый текст, тестовый текст",
            author=cls.user_author,
            group=cls.group,
        )

    def setUp(self):
        self.unauthorized_user = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user_author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.another_user)
        cache.clear()

    def test_anonymous_user(self):
        """Запрос страниц, доступных неавторизованным пользователям,
        работает правильно."""
        urls = [
            "/",
            "/group/test-slug/",
            "/profile/user_author/",
            f"/posts/{self.post.pk}/",
        ]
        for address in urls:
            with self.subTest(address=address):
                response = self.unauthorized_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_user(self):
        """Запрос страниц, доступных авторизованным пользователям,
        работает правильно."""
        urls = [
            "/",
            "/create/",
            "/group/test-slug/",
            "/profile/user_author/",
            f"/posts/{self.post.pk}/",
        ]
        for address in urls:
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_exists_at_desired_location_for_auth_user(self):
        """Страница создания поста доступна авторизованному пользователю."""
        response = self.authorized_user.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_exists_at_desired_location_for_author(self):
        """Страница редактирования поста доступна автору поста."""
        response = self.post_author.get(f"/posts/{self.post.pk}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_redirect_anonymous_on_auth_login(self):
        """Страница создания поста перенаправляет
        неавторизованного пользователя на страницу авторизации."""
        response = self.unauthorized_user.get(
            "/create/", follow=True
        )
        self.assertRedirects(
            response, "/auth/login/?next=/create/"
        )

    def test_post_edit_redirects_anonymous_on_auth_login(self):
        """Страница редактирования поста перенаправляет
        неавторизованного пользователя на страницу авторизации."""
        response = self.unauthorized_user.get(
            f"/posts/{self.post.pk}/edit/", follow=True
        )
        self.assertRedirects(
            response, f"/auth/login/?next=/posts/{self.post.pk}/edit/"
        )

    def test_post_comment_redirects_anonymous_on_auth_login(self):
        """Страница добавления комментария к посту перенаправляет
        неавторизованного пользователя на страницу авторизации."""
        response = self.unauthorized_user.get(
            f"/posts/{self.post.pk}/comment/", follow=True
        )
        self.assertRedirects(
            response, f"/auth/login/?next=/posts/{self.post.pk}/comment/"
        )

    def test_post_comment_redirects_auth_user_on_post_detail(self):
        """Страница добавления комментария к посту перенаправляет
        авторизованного пользователя на страницу информации о посте."""
        response = self.authorized_user.post(
            f"/posts/{self.post.pk}/comment/"
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            "/group/test-slug/": "posts/group_list.html",
            "/profile/user_author/": "posts/profile.html",
            "/create/": "posts/create_post.html",
            f"/posts/{self.post.pk}/": "posts/post_detail.html",
            f"/posts/{self.post.pk}/edit/": "posts/create_post.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertTemplateUsed(response, template)
