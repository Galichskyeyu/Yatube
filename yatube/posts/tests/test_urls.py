from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='TestAuthor')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            pk='50',
        )

    def test_url_exists_at_desired_location_for_anonymous(self):
        """Запрос страниц, доступных всем пользователям, работает правильно."""
        response_list = {
            reverse('posts:index'): 200,
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): 200,
            reverse('posts:profile', kwargs={'username': 'TestAuthor'}): 200,
            reverse('posts:post_detail', kwargs={'post_id': '50'}): 200,
            '/unexisting_page/': 404,
        }
        for address, code in response_list.items():
            with self.subTest(address=address):
                response = PostURLTests.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_url_exists_at_desired_location_for_auth_user(self):
        """Страница /create доступна авторизованному пользователю."""
        response = PostURLTests.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertEqual(response.status_code, 200)

    def test_url_exists_at_desired_location_for_author(self):
        """Страница /posts/post.pk/edit доступна автору поста."""
        response = PostURLTests.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '50'})
        )
        self.assertEqual(response.status_code, 200)

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница /create перенаправляет неавторизованного пользователя
        на страницу авторизации.
        """
        reverse_page = reverse('posts:post_create')
        response = self.client.get(reverse_page, follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=' + reverse_page
        )

    def test_task_detail_url_redirect_anonymous_on_admin_login(self):
        """Страница /posts/post.pk/edit перенаправляет
        неавторизованного пользователя на страницу авторизации.
        """
        reverse_page = reverse(
            'posts:post_edit', kwargs={'post_id': '50'}
        )
        response = self.guest_client.get(reverse_page, follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=' + reverse_page
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = int(PostURLTests.post.pk)
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': PostURLTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': PostURLTests.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': post}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': post}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернет ошибку 404
           и при этом будет использован кастомный шаблон."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, self.template_404)
