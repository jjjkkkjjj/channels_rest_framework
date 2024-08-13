from __future__ import annotations

import pytest

from rest_framework_channels.consumers import AsyncAPIConsumer
from rest_framework_channels.decorators import async_action

from .websocket import ExtendedWebsocketCommunicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decorator_action():

    class ParentConsumer(AsyncAPIConsumer):
        @async_action()
        async def test_action(self, pk=None, **kwargs):
            return {'pk': pk}, 200

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to({'action': 'test_action', 'pk': 2})

    response = await communicator.receive_json_from()

    assert response == {
        'errors': [],
        'data': {'pk': 2},
        'action': 'test_action',
        'route': '',
        'status': 200,
    }

    await communicator.disconnect()
