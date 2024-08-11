import pytest
from django.urls import path, re_path

from channels_rest_framework.consumers import AsyncAPIConsumer
from channels_rest_framework.decorators import action
from channels_rest_framework.handlers import AsyncAPIActionHandler
from channels_rest_framework.permissions import IsAuthenticated

from .websocket import AuthCommunicator, ExtendedWebsocketCommunicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_parent_is_authenticated(user):

    class ChildConsumer(AsyncAPIActionHandler):
        @action()
        async def test_async_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

        @action()
        def test_sync_action(self, pk=None, **kwargs):
            return {'pk': pk, 'sync': True}, 200

    class ParentConsumer(AsyncAPIConsumer):
        permission_classes = (IsAuthenticated,)
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
    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'test_async_action',
        'route': 'test_async_child_route/test_async_action/',
        'response_status': 403,
    }
    assert len(errors) > 0

    await communicator.disconnect()

    # login

    communicator = AuthCommunicator(user, ParentConsumer(), '/testws/')

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
async def test_child_is_authenticated(user):

    class ChildConsumer(AsyncAPIActionHandler):
        permission_classes = (IsAuthenticated,)

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

        @action()
        async def test_parent_async_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

        @action()
        def test_parent_sync_action(self, pk=None, **kwargs):
            return {'pk': pk, 'sync': True}, 200

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    ### Parent Action ###
    # Permission Denied
    await communicator.send_json_to(
        {
            'action': 'test_parent_sync_action',
            'pk': 3,
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 3, 'sync': True},
        'action': 'test_parent_sync_action',
        'route': '',
        'response_status': 200,
    }

    await communicator.send_json_to(
        {
            'action': 'test_parent_async_action',
            'pk': 2,
        }
    )

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 2},
        'action': 'test_parent_async_action',
        'route': '',
        'response_status': 200,
    }

    ### Child Action ###
    # Permission Denied
    await communicator.send_json_to(
        {
            'action': 'test_sync_action',
            'pk': 3,
            'route': 'test_sync_child_route/test_sync_action/',
        }
    )

    response = await communicator.receive_json_from()

    errors = response.pop('errors')
    assert response == {
        'data': None,
        'action': 'test_sync_action',
        'route': 'test_sync_child_route/test_sync_action/',
        'response_status': 403,
    }
    assert len(errors) > 0

    await communicator.disconnect()

    # login

    communicator = AuthCommunicator(user, ParentConsumer(), '/testws/')

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
