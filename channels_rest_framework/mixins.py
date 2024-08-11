from rest_framework import status

from .decorators import action


class CreateModelMixin:
    """
    Create a model instance.
    """

    @action()
    def create(self, data, *args, **kwargs):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return serializer.data, status.HTTP_201_CREATED

    def perform_create(self, serializer):
        serializer.save()
