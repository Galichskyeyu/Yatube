from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, больше пятнадцати символов',
        )

    def test_models_have_correct_object_names(self):
        """Значение поля __str__ в объектах моделей
        Post и Group отображается правильно.
        """
        self.assertEqual(PostModelTest.post.text[:15], str(PostModelTest.post))
        self.assertEqual(PostModelTest.group.title, str(PostModelTest.group))

    def test_model_post_have_correct_verbose_names(self):
        """Атрибут verbose_name работает правильно."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected)

    def test_model_post_have_correct_help_text(self):
        """Атрибут help_text работает правильно."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected)
