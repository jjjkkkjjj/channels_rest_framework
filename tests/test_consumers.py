import asyncio

import pytest
from django.urls import path, re_path
from rest_framework.exceptions import Throttled

from channels_rest_framework.consumers import AsyncAPIConsumer
from channels_rest_framework.decorators import action, route
from channels_rest_framework.handlers import AsyncAPIActionHandler

from .websocket import ExtendedWebsocketCommunicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decorator_action():

    class ParentConsumer(AsyncAPIConsumer):
        @action()
        async def test_async_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

        @action()
        def test_sync_action(self, pk=None, **kwargs):
            return {'pk': pk, 'sync': True}, 200

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to({'action': 'test_async_action', 'pk': 2})

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 2},
        'action': 'test_async_action',
        'route': '',
        'response_status': 200,
    }

    await communicator.send_json_to({'action': 'test_sync_action', 'pk': 3})

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 3, 'sync': True},
        'action': 'test_sync_action',
        'route': '',
        'response_status': 200,
    }

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decorator_sync_route():

    class ChildConsumer(AsyncAPIActionHandler):
        @action()
        async def test_async_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

        @action()
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
        'response_status': 200,
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
        'response_status': 200,
    }

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decorator_async_route():

    kwargs_results = {}

    class ChildConsumer(AsyncAPIActionHandler):
        @action()
        async def test_async_action(self, pk=None, **kwargs):
            kwargs_results['test_async_action'] = self.kwargs
            return {'pk': pk}, 200

        @action()
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
        'response_status': 200,
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
        'response_status': 200,
    }
    assert kwargs_results['test_sync_action'] == dict(child_id='3')

    await communicator.disconnect()
