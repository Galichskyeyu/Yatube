# Generated by Django 2.2.16 on 2023-01-31 20:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20230131_2305'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='follow',
            options={},
        ),
        migrations.RemoveConstraint(
            model_name='follow',
            name='unique_relationships',
        ),
        migrations.RemoveConstraint(
            model_name='follow',
            name='prevent_self_follow',
        ),
        migrations.AlterField(
            model_name='follow',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='follow',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower', to=settings.AUTH_USER_MODEL),
        ),
    ]
