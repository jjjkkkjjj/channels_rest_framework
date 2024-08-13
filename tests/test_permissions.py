from __future__ import annotations

import pytest
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.urls import path, re_path

from rest_framework_channels.consumers import AsyncAPIConsumer
from rest_framework_channels.decorators import async_action
from rest_framework_channels.generics import (
    RetrieveAPIActionHandler,
    RetrieveAPIConsumer,
)
from rest_framework_channels.handlers import AsyncAPIActionHandler
from rest_framework_channels.permissions import IsAuthenticated, IsOwner

from .models import TestWithAuthorModel
from .serializers import TestWithAuthorSerializer
from .websocket import AuthCommunicator, ExtendedWebsocketCommunicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_parent_is_authenticated(user):

    class ChildActionHandler(AsyncAPIActionHandler):
        @async_action()
        async def test_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

    class ParentConsumer(AsyncAPIConsumer):
        permission_classes = (IsAuthenticated,)
        routepatterns = [
            path('test_child_route/', ChildActionHandler.as_aaah()),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to(
        {
            'action': 'test_action',
            'pk': 2,
            'route': 'test_child_route/',
        }
    )

    response = await communicator.receive_json_from()
    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'test_action',
        'route': 'test_child_route/',
        'status': 403,
    }
    assert len(errors) > 0

    await communicator.disconnect()

    # login

    communicator = AuthCommunicator(user, ParentConsumer(), '/testws/')

    await communicator.send_json_to(
        {
            'action': 'test_action',
            'pk': 3,
            'route': 'test_child_route/',
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 3},
        'action': 'test_action',
        'route': 'test_child_route/',
        'status': 200,
    }

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_child_is_authenticated(user):

    class ChildActionHandler(AsyncAPIActionHandler):
        permission_classes = (IsAuthenticated,)

        @async_action()
        async def test_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

    class ParentConsumer(AsyncAPIConsumer):

        routepatterns = [
            path('test_child_route/', ChildActionHandler.as_aaah()),
        ]

        @async_action()
        async def test_parent_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    ### Parent Action ###
    await communicator.send_json_to(
        {
            'action': 'test_parent_action',
            'pk': 2,
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 2},
        'action': 'test_parent_action',
        'route': '',
        'status': 200,
    }

    ### Child Action ###
    # Permission Denied
    await communicator.send_json_to(
        {
            'action': 'test_action',
            'pk': 3,
            'route': 'test_child_route/',
        }
    )

    response = await communicator.receive_json_from()

    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'test_action',
        'route': 'test_child_route/',
        'status': 403,
    }
    assert len(errors) > 0

    await communicator.disconnect()

    # login

    communicator = AuthCommunicator(user, ParentConsumer(), '/testws/')

    await communicator.send_json_to(
        {
            'action': 'test_action',
            'pk': 3,
            'route': 'test_child_route/',
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 3},
        'action': 'test_action',
        'route': 'test_child_route/',
        'status': 200,
    }

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_parent_is_owner(user):

    user2 = await database_sync_to_async(get_user_model().objects.create_user)(
        username='test2', password='password'
    )

    class IsAuthor(IsOwner):
        lookup_field = 'author'

    class ParentConsumer(RetrieveAPIConsumer):
        queryset = TestWithAuthorModel.objects.all()
        serializer_class = TestWithAuthorSerializer
        permission_classes = (IsAuthor,)

    data = dict(id=1, title='Title', content='Content', author=user)
    await database_sync_to_async(TestWithAuthorModel.objects.get_or_create)(**data)

    # Test a normal connection
    # url is mocked by this kwargs
    communicator = ExtendedWebsocketCommunicator(
        ParentConsumer(), '/testws/1/', kwargs=dict(pk=1)
    )

    connected, _ = await communicator.connect()

    assert connected

    # No authenticated user
    await communicator.send_json_to(
        {
            'action': 'retrieve',
        }
    )

    response = await communicator.receive_json_from()
    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'retrieve',
        'route': '',
        'status': 403,
    }
    assert len(errors) > 0

    await communicator.disconnect()

    # login as not owner
    communicator = AuthCommunicator(
        user2, ParentConsumer(), '/testws/', kwargs=dict(pk=1)
    )

    await communicator.send_json_to(
        {
            'action': 'retrieve',
        }
    )

    response = await communicator.receive_json_from()
    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'retrieve',
        'route': '',
        'status': 403,
    }
    assert len(errors) > 0

    await communicator.disconnect()

    # login as owner
    communicator = AuthCommunicator(
        user, ParentConsumer(), '/testws/', kwargs=dict(pk=1)
    )

    await communicator.send_json_to(
        {
            'action': 'retrieve',
        }
    )

    response = await communicator.receive_json_from()
    data['author'] = user.pk
    assert response == {
        'errors': [],
        'data': data,
        'action': 'retrieve',
        'route': '',
        'status': 200,
    }

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_child_is_owner(user):

    user2 = await database_sync_to_async(get_user_model().objects.create_user)(
        username='test2', password='password'
    )

    class IsAuthor(IsOwner):
        lookup_field = 'author'

    class ChildActionHandler(RetrieveAPIActionHandler):
        queryset = TestWithAuthorModel.objects.all()
        serializer_class = TestWithAuthorSerializer
        permission_classes = (IsAuthor,)

    class ParentConsumer(AsyncAPIConsumer):
        routepatterns = [
            re_path(
                r'test_child_route/(?P<pk>[-\w]+)/$',
                ChildActionHandler.as_aaah(),
            ),
        ]

    data = dict(id=1, title='Title', content='Content', author=user)
    await database_sync_to_async(TestWithAuthorModel.objects.get_or_create)(**data)

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    # No authenticated user
    await communicator.send_json_to(
        {'action': 'retrieve', 'route': 'test_child_route/1/'}
    )

    response = await communicator.receive_json_from()
    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'retrieve',
        'route': 'test_child_route/1/',
        'status': 403,
    }
    assert len(errors) > 0

    await communicator.disconnect()

    # login as not owner
    communicator = AuthCommunicator(user2, ParentConsumer(), '/testws/')

    await communicator.send_json_to(
        {'action': 'retrieve', 'route': 'test_child_route/1/'}
    )

    response = await communicator.receive_json_from()
    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'retrieve',
        'route': 'test_child_route/1/',
        'status': 403,
    }
    assert len(errors) > 0

    await communicator.disconnect()

    # login as owner
    communicator = AuthCommunicator(user, ParentConsumer(), '/testws/')

    await communicator.send_json_to(
        {'action': 'retrieve', 'route': 'test_child_route/1/'}
    )

    response = await communicator.receive_json_from()
    data['author'] = user.pk
    assert response == {
        'errors': [],
        'data': data,
        'action': 'retrieve',
        'route': 'test_child_route/1/',
        'status': 200,
    }

    await communicator.disconnect()
