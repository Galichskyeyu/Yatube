from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_and_tech(self):
        """Запрос страниц, доступных всем пользователям,
        работает правильно.
        """
        urls = (
            '/about/author/',
            '/about/tech/',
        )
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_static_url_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_static_urls = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

        for url_address, template in templates_static_urls.items():
            with self.subTest(address=url_address):
                response = self.guest_client.get(url_address)
                self.assertTemplateUsed(response, template)
