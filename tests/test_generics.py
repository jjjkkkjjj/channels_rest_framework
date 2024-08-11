import pytest
from channels.db import database_sync_to_async
from django.forms.models import model_to_dict
from django.urls import path, re_path

from channels_rest_framework import generics
from channels_rest_framework.consumers import AsyncAPIConsumer
from channels_rest_framework.decorators import action
from channels_rest_framework.handlers import AsyncAPIActionHandler
from channels_rest_framework.permissions import IsAuthenticated

from .models import TestModel
from .serializers import TestSerializer
from .websocket import AuthCommunicator, ExtendedWebsocketCommunicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_api_action_handler():

    class ChildActionHandler(generics.CreateAPIActionHandler):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    class ParentConsumer(AsyncAPIConsumer):

        routepatterns = [
            path('test_async_child_route/', ChildActionHandler.as_aaah()),
            path('test_sync_child_route/', ChildActionHandler.as_aaah()),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    ### async path
    data = dict(id=1, title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
            'route': 'test_async_child_route/create/',
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': data,
        'action': 'create',
        'route': 'test_async_child_route/create/',
        'response_status': 201,
    }
    instance = await database_sync_to_async(TestModel.objects.get)(pk=data['id'])
    assert data == model_to_dict(instance)

    ### sync path
    data = dict(id=2, title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
            'route': 'test_sync_child_route/create/',
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': data,
        'action': 'create',
        'route': 'test_sync_child_route/create/',
        'response_status': 201,
    }
    instance = await database_sync_to_async(TestModel.objects.get)(pk=data['id'])
    assert data == model_to_dict(instance)

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_api_consumer():

    class ParentConsumer(generics.CreateAPIConsumer):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    ### async path
    data = dict(id=3, title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': data,
        'action': 'create',
        'route': '',
        'response_status': 201,
    }
    instance = await database_sync_to_async(TestModel.objects.get)(pk=data['id'])
    assert data == model_to_dict(instance)

    ### sync path
    data = dict(id=4, title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': data,
        'action': 'create',
        'route': '',
        'response_status': 201,
    }
    instance = await database_sync_to_async(TestModel.objects.get)(pk=data['id'])
    assert data == model_to_dict(instance)

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_api_action_handler():

    class ChildActionHandler(generics.ListAPIActionHandler):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    class ParentConsumer(AsyncAPIConsumer):

        routepatterns = [
            path('test_async_child_route/', ChildActionHandler.as_aaah()),
            path('test_sync_child_route/', ChildActionHandler.as_aaah()),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    # Create 2 TestModel
    answers = [
        dict(id=1, title='Title', content='Content'),
        dict(id=2, title='Title2', content='Content2'),
    ]
    for ans in answers:
        await database_sync_to_async(TestModel.objects.get_or_create)(**ans)

    connected, _ = await communicator.connect()

    assert connected

    ### async path
    await communicator.send_json_to(
        {
            'action': 'list',
            'route': 'test_async_child_route/list/',
        }
    )

    response = await communicator.receive_json_from()
    data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': 'test_async_child_route/list/',
        'response_status': 200,
    }
    assert len(data) == 2
    for response_data, ans in zip(data, answers):
        assert response_data == ans

    ### sync path
    await communicator.send_json_to(
        {
            'action': 'list',
            'route': 'test_sync_child_route/list/',
        }
    )

    response = await communicator.receive_json_from()
    data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': 'test_sync_child_route/list/',
        'response_status': 200,
    }
    assert len(data) == 2
    for response_data, ans in zip(data, answers):
        assert response_data == ans

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_api_consumer():

    class ParentConsumer(generics.ListAPIConsumer):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    # Create 2 TestModel
    answers = [
        dict(id=1, title='Title', content='Content'),
        dict(id=2, title='Title2', content='Content2'),
    ]
    for ans in answers:
        await database_sync_to_async(TestModel.objects.get_or_create)(**ans)

    connected, _ = await communicator.connect()

    assert connected

    ### async path
    await communicator.send_json_to(
        {
            'action': 'list',
        }
    )

    response = await communicator.receive_json_from()
    data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': '',
        'response_status': 200,
    }
    assert len(data) == 2
    for response_data, ans in zip(data, answers):
        assert response_data == ans

    ### sync path
    await communicator.send_json_to(
        {
            'action': 'list',
        }
    )

    response = await communicator.receive_json_from()
    data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': '',
        'response_status': 200,
    }
    assert len(data) == 2
    for response_data, ans in zip(data, answers):
        assert response_data == ans

    await communicator.disconnect()
