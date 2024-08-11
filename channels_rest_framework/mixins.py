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


class ListModelMixin:
    """
    List a queryset.
    """

    @action()
    def list(self, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return serializer.data, status.HTTP_200_OK
