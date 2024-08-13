from __future__ import annotations

from rest_framework.serializers import ModelSerializer

from .models import TestModel, TestWithAuthorModel


class TestSerializer(ModelSerializer):
    class Meta:
        model = TestModel
        fields = '__all__'


class TestWithAuthorSerializer(ModelSerializer):
    class Meta:
        model = TestWithAuthorModel
        fields = '__all__'
