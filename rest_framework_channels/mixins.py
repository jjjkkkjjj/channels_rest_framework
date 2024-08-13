from __future__ import annotations

from asgiref.sync import async_to_sync
from rest_framework import status

from .decorators import async_action


class CreateModelMixin:
    """
    Create a model instance.
    """

    @async_action()
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

    @async_action()
    def list(self, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return serializer.data, status.HTTP_200_OK


class RetrieveModelMixin:
    """
    Retrieve a model instance.
    """

    @async_action()
    def retrieve(self, *args, **kwargs):
        action = kwargs.get('action', 'retrieve')
        instance = self.get_object(action)
        serializer = self.get_serializer(instance)
        return serializer.data, status.HTTP_200_OK


class UpdateModelMixin:
    """
    Update a model instance.
    """

    @async_action()
    def update(self, data, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        action = kwargs.get('action', 'update')
        instance = self.get_object(action)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return serializer.data, status.HTTP_200_OK

    def perform_update(self, serializer):
        serializer.save()

    @async_action()
    def partial_update(self, data, *args, **kwargs):
        kwargs['partial'] = True
        return async_to_sync(self.update)(data, *args, **kwargs)


class DestroyModelMixin:
    """
    Destroy a model instance.
    """

    @async_action()
    def destroy(self, *args, **kwargs):
        action = kwargs.get('action', 'destory')
        instance = self.get_object(action)
        self.perform_destroy(instance)
        return None, status.HTTP_204_NO_CONTENT

    def perform_destroy(self, instance):
        instance.delete()
