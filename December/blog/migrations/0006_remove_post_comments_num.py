# Generated by Django 3.1.14 on 2022-01-10 03:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_remove_post_post_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='comments_num',
        ),
    ]