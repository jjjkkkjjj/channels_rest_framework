import pytest
from django.urls import path, re_path

from channels_rest_framework.consumers import AsyncAPIConsumer
from channels_rest_framework.decorators import async_action
from channels_rest_framework.handlers import AsyncAPIActionHandler
from channels_rest_framework.permissions import IsAuthenticated

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
