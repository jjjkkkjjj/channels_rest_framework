from __future__ import annotations

import pytest
from django.urls import path, re_path

from rest_framework_channels.consumers import AsyncAPIConsumer
from rest_framework_channels.decorators import async_action
from rest_framework_channels.handlers import AsyncAPIActionHandler
from rest_framework_channels.permissions import IsAuthenticated
from rest_framework_channels.testing.websocket import (
    AuthCommunicator,
    ExtendedWebsocketCommunicator,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_exception_debug(debug_exception_handler):

    class ChildConsumer(AsyncAPIActionHandler):
        @async_action()
        async def test_exception(self, **kwargs):
            raise ValueError('Error')

    class ParentConsumer(AsyncAPIConsumer):
        routepatterns = [
            path('test_async_child_route/', ChildConsumer.as_aaah()),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to(
        {
            'action': 'test_exception',
            'route': 'test_async_child_route/',
        }
    )

    with pytest.raises(ValueError):
        response = await communicator.receive_json_from()
        await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_exception_production():

    class ChildConsumer(AsyncAPIActionHandler):
        @async_action()
        async def test_exception(self, **kwargs):
            raise ValueError('Error')

    class ParentConsumer(AsyncAPIConsumer):
        routepatterns = [
            path('test_async_child_route/', ChildConsumer.as_aaah()),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to(
        {
            'action': 'test_exception',
            'route': 'test_async_child_route/',
        }
    )

    response = await communicator.receive_json_from()
    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'test_exception',
        'route': 'test_async_child_route/',
        'status': 500,
    }
    assert len(errors) > 0

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decorator_sync_route():

    class ChildConsumer(AsyncAPIActionHandler):
        @async_action()
        async def test_async_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

        @async_action()
        def test_sync_action(self, pk=None, **kwargs):
            return {'pk': pk, 'sync': True}, 200

    class ParentConsumer(AsyncAPIConsumer):
        routepatterns = [
            path('test_async_child_route/', ChildConsumer.as_aaah()),
            path('test_sync_child_route/', ChildConsumer.as_aaah()),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to(
        {
            'action': 'test_async_action',
            'pk': 2,
            'route': 'test_async_child_route/test_async_action/',
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 2},
        'action': 'test_async_action',
        'route': 'test_async_child_route/test_async_action/',
        'status': 200,
    }

    await communicator.send_json_to(
        {
            'action': 'test_sync_action',
            'pk': 3,
            'route': 'test_sync_child_route/test_sync_action/',
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 3, 'sync': True},
        'action': 'test_sync_action',
        'route': 'test_sync_child_route/test_sync_action/',
        'status': 200,
    }

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decorator_async_route():

    kwargs_results = {}

    class ChildConsumer(AsyncAPIActionHandler):
        @async_action()
        async def test_async_action(self, pk=None, **kwargs):
            kwargs_results['test_async_action'] = self.kwargs
            return {'pk': pk}, 200

        @async_action()
        def test_sync_action(self, pk=None, **kwargs):
            kwargs_results['test_sync_action'] = self.kwargs
            return {'pk': pk, 'sync': True}, 200

    class ParentConsumer(AsyncAPIConsumer):
        routepatterns = [
            re_path(
                r'test_async_child_route/(?P<child_id>[-\w]+)/$',
                ChildConsumer.as_aaah(),
            ),
            re_path(
                r'test_sync_child_route/(?P<child_id>[-\w]+)/$',
                ChildConsumer.as_aaah(),
            ),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to(
        {
            'action': 'test_async_action',
            'pk': 2,
            'route': 'test_async_child_route/2/',
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 2},
        'action': 'test_async_action',
        'route': 'test_async_child_route/2/',
        'status': 200,
    }
    assert kwargs_results['test_async_action'] == dict(child_id='2')

    await communicator.send_json_to(
        {
            'action': 'test_sync_action',
            'pk': 3,
            'route': 'test_sync_child_route/3/',
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 3, 'sync': True},
        'action': 'test_sync_action',
        'route': 'test_sync_child_route/3/',
        'status': 200,
    }
    assert kwargs_results['test_sync_action'] == dict(child_id='3')

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_broadcast(user):
    kwargs_results = {}

    class ChildConsumer(AsyncAPIActionHandler):
        permission_classes = (IsAuthenticated,)

        @async_action(
            mode='broadcast',
            broadcast_type='test.called',
        )
        async def test_async_action(self, **kwargs):
            return {'test': 'content'}, 200

    class ParentConsumer(AsyncAPIConsumer):
        group_send_lookup_kwargs = 'group_id'

        routepatterns = [
            path(
                'test_async_child_route/',
                ChildConsumer.as_aaah(),
            ),
        ]

        async def test_called(self, event):
            kwargs_results['is_called'] = True
            await self.send_json(event)

    # Test a normal connection
    auth_communicator = AuthCommunicator(
        user, ParentConsumer(), '/testws/1234-5678/', kwargs=dict(group_id='1234-5678')
    )
    connected, _ = await auth_communicator.connect()

    assert connected

    unauth_communicator = ExtendedWebsocketCommunicator(
        ParentConsumer(), '/testws/1234-5678/', kwargs=dict(group_id='1234-5678')
    )
    connected, _ = await unauth_communicator.connect()

    assert connected

    ## unauth user send
    await unauth_communicator.send_json_to(
        {
            'action': 'test_async_action',
            'route': 'test_async_child_route/',
        }
    )

    response = await unauth_communicator.receive_json_from()

    # error due to permission
    assert response['status'] == 403
    assert len(response['errors']) > 0

    ## auth user send
    await auth_communicator.send_json_to(
        {
            'action': 'test_async_action',
            'route': 'test_async_child_route/',
        }
    )

    response = await auth_communicator.receive_json_from()

    assert response == {
        'data': {'test': 'content'},
        'status': 200,
        'action': 'test_async_action',
        'errors': [],
        'route': 'test_async_child_route/',
    }

    response = await unauth_communicator.receive_json_from()

    assert response == {
        'type': 'test.called',
        'data': {'test': 'content'},
        'status': 200,
    }
    assert kwargs_results['is_called']

    await auth_communicator.disconnect()
    await unauth_communicator.disconnect()
