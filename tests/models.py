from django.contrib.auth import get_user_model
from django.db import models


class TestModel(models.Model):
    """Simple model to test with."""

    title = models.CharField(max_length=255)
    content = models.CharField(max_length=1024)


class TestWithAuthorModel(models.Model):
    """Simple model with user to test with."""

    title = models.CharField(max_length=255)
    content = models.CharField(max_length=1024)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
