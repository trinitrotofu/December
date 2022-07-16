# Generated by Django 3.1.14 on 2022-01-17 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0013_auto_20220114_0832'),
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=260)),
                ('upload_time', models.PositiveIntegerField(default=0)),
                ('md5', models.CharField(default='', max_length=32)),
            ],
        ),
    ]