from django.db import models

class Option(models.Model):
    name = models.CharField(max_length=32)
    value = models.TextField()

class Post(models.Model):
    title = models.CharField(max_length=200, default="")
    text = models.TextField(default="")
    post_time = models.PositiveIntegerField(default=0)
    comments_num = models.PositiveIntegerField(default=0)
    post_type = models.CharField(max_length=16, default="post")
    protected = models.BooleanField(default=False)
    password = models.CharField(max_length=32, default="")
    is_top = models.BooleanField(default=False)
    allow_comment = models.BooleanField(default=True)

class Comment(models.Model):
    author = models.CharField(max_length=200, default="")
    email = models.CharField(max_length=200, default="")
    is_admin = models.BooleanField(default=False)
    url = models.CharField(max_length=255, default="")
    text = models.TextField(default="")
    pid = models.PositiveIntegerField(default=0)
    parent = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, default="published")
    comment_time = models.PositiveIntegerField(default=0)

class Media(models.Model):
    name = models.CharField(max_length=200, default="")
    upload_time = models.PositiveIntegerField(default=0)
    path = models.CharField(max_length=200, default="")
