from django.db import models


class TestModel(models.Model):
    """Simple model to test with."""

    title = models.CharField(max_length=255)
    content = models.CharField(max_length=1024)
