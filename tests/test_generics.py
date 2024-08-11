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
    data = dict(title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
            'route': 'test_async_child_route/',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'create',
        'route': 'test_async_child_route/',
        'response_status': 201,
    }
    instance = await database_sync_to_async(TestModel.objects.get)(
        pk=response_data['id']
    )
    assert response_data == model_to_dict(instance)
    response_data.pop('id')
    assert response_data == data

    ### sync path
    data = dict(title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
            'route': 'test_sync_child_route/',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'create',
        'route': 'test_sync_child_route/',
        'response_status': 201,
    }
    instance = await database_sync_to_async(TestModel.objects.get)(
        pk=response_data['id']
    )
    assert response_data == model_to_dict(instance)
    response_data.pop('id')
    assert response_data == data

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
    data = dict(title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'create',
        'route': '',
        'response_status': 201,
    }
    instance = await database_sync_to_async(TestModel.objects.get)(
        pk=response_data['id']
    )

    assert response_data == model_to_dict(instance)
    response_data.pop('id')
    assert response_data == data

    ### sync path
    data = dict(title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'create',
        'route': '',
        'response_status': 201,
    }
    instance = await database_sync_to_async(TestModel.objects.get)(
        pk=response_data['id']
    )

    assert response_data == model_to_dict(instance)
    response_data.pop('id')
    assert response_data == data

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
        dict(title='Title', content='Content'),
        dict(title='Title2', content='Content2'),
    ]
    for ans in answers:
        await database_sync_to_async(TestModel.objects.get_or_create)(**ans)

    connected, _ = await communicator.connect()

    assert connected

    ### async path
    await communicator.send_json_to(
        {
            'action': 'list',
            'route': 'test_async_child_route/',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': 'test_async_child_route/',
        'response_status': 200,
    }
    assert len(response_data) == 2
    for data, ans in zip(response_data, answers):
        data.pop('id')
        assert data == ans

    ### sync path
    await communicator.send_json_to(
        {
            'action': 'list',
            'route': 'test_sync_child_route/',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': 'test_sync_child_route/',
        'response_status': 200,
    }
    assert len(response_data) == 2
    for data, ans in zip(response_data, answers):
        data.pop('id')
        assert data == ans

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
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': '',
        'response_status': 200,
    }
    assert len(response_data) == 2
    for data, ans in zip(response_data, answers):
        assert data == ans

    ### sync path
    await communicator.send_json_to(
        {
            'action': 'list',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': '',
        'response_status': 200,
    }
    assert len(response_data) == 2
    for data, ans in zip(response_data, answers):
        assert data == ans

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retrieve_api_action_handler():

    class ChildActionHandler(generics.RetrieveAPIActionHandler):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    class ParentConsumer(AsyncAPIConsumer):

        routepatterns = [
            re_path(
                r'test_async_child_route/(?P<pk>[-\w]+)/$',
                ChildActionHandler.as_aaah(),
            ),
            re_path(
                r'test_sync_child_route/(?P<pk>[-\w]+)/$', ChildActionHandler.as_aaah()
            ),
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
            'action': 'retrieve',
            'route': f'test_async_child_route/{answers[0]["id"]}/',
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': answers[0],
        'action': 'retrieve',
        'route': f'test_async_child_route/{answers[0]["id"]}/',
        'response_status': 200,
    }

    ### sync path
    await communicator.send_json_to(
        {
            'action': 'retrieve',
            'route': f'test_sync_child_route/{answers[1]["id"]}/',
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': answers[1],
        'action': 'retrieve',
        'route': f'test_sync_child_route/{answers[1]["id"]}/',
        'response_status': 200,
    }

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_retrieve_api_consumer():

    class ParentConsumer(generics.RetrieveAPIConsumer):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    # Test a normal connection
    # url is mocked by this kwargs
    communicator = ExtendedWebsocketCommunicator(
        ParentConsumer(), '/testws/1/', kwargs=dict(pk=1)
    )

    # Create TestModel
    data = dict(id=1, title='Title', content='Content')
    await database_sync_to_async(TestModel.objects.get_or_create)(**data)

    connected, _ = await communicator.connect()

    assert connected

    ### async path
    await communicator.send_json_to({'action': 'retrieve'})

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': data,
        'action': 'retrieve',
        'route': '',
        'response_status': 200,
    }

    await communicator.disconnect()
