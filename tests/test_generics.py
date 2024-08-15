from __future__ import annotations

import pytest
from channels.db import database_sync_to_async
from django.forms.models import model_to_dict
from django.urls import path, re_path
from rest_framework.pagination import PageNumberPagination

from rest_framework_channels import generics
from rest_framework_channels.consumers import AsyncAPIConsumer

from .models import TestModel
from .serializers import TestSerializer
from .websocket import ExtendedWebsocketCommunicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_api_action_handler():

    class ChildActionHandler(generics.CreateAPIActionHandler):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    class ParentConsumer(AsyncAPIConsumer):

        routepatterns = [
            path('test_child_route/', ChildActionHandler.as_aaah()),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    connected, _ = await communicator.connect()

    assert connected

    data = dict(title='Title', content='Content')
    await communicator.send_json_to(
        {
            'action': 'create',
            'data': data,
            'route': 'test_child_route/',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'create',
        'route': 'test_child_route/',
        'status': 201,
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
        'status': 201,
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
            path('test_child_route/', ChildActionHandler.as_aaah()),
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

    await communicator.send_json_to(
        {
            'action': 'list',
            'route': 'test_child_route/',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': 'test_child_route/',
        'status': 200,
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
        'status': 200,
    }
    assert len(response_data) == 2
    for data, ans in zip(response_data, answers):
        assert data == ans

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_pagenated_list_api_action_handler():

    class TestPagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'
        max_page_size = 100

    class ChildActionHandler(generics.ListAPIActionHandler):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()
        pagination_class = TestPagination

    class ParentConsumer(AsyncAPIConsumer):

        routepatterns = [
            path('test_child_route/', ChildActionHandler.as_aaah()),
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(
        ParentConsumer(), 'ws://127.0.0.1/testws/'
    )

    # Create 2 TestModel
    answers = [dict(title=f'Title{i+1}', content=f'Content{i+1}') for i in range(100)]
    for ans in answers:
        await database_sync_to_async(TestModel.objects.get_or_create)(**ans)

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to(
        {
            'action': 'list',
            'route': 'test_child_route/?page=4',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': 'test_child_route/?page=4',
        'status': 200,
    }
    assert len(response_data['results']) == 10
    assert response_data['count'] == 100
    assert response_data['next'] == 'test_child_route/?page=5'
    assert response_data['previous'] == 'test_child_route/?page=3'

    for data, ans in zip(response_data['results'], answers[30:40]):
        data.pop('id')
        assert data == ans

    await communicator.send_json_to(
        {
            'action': 'list',
            'route': 'test_child_route/?page=10',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': 'test_child_route/?page=10',
        'status': 200,
    }
    assert len(response_data['results']) == 10
    assert response_data['count'] == 100
    assert response_data['next'] is None
    assert response_data['previous'] == 'test_child_route/?page=9'

    for data, ans in zip(response_data['results'], answers[90:100]):
        data.pop('id')
        assert data == ans

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_pagenated_list_api_consumer():

    class TestPagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'
        max_page_size = 100

    class ParentConsumer(generics.ListAPIConsumer):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()
        pagination_class = TestPagination

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(
        ParentConsumer(), 'ws://127.0.0.1/testws/'
    )

    # Create 2 TestModel
    answers = [dict(title=f'Title{i+1}', content=f'Content{i+1}') for i in range(100)]
    for ans in answers:
        await database_sync_to_async(TestModel.objects.get_or_create)(**ans)

    connected, _ = await communicator.connect()

    assert connected

    await communicator.send_json_to(
        {
            'action': 'list',
            'route': '?page=4',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': '?page=4',
        'status': 200,
    }
    assert len(response_data['results']) == 10
    assert response_data['count'] == 100
    assert response_data['next'] == '?page=5'
    assert response_data['previous'] == '?page=3'

    for data, ans in zip(response_data['results'], answers[30:40]):
        data.pop('id')
        assert data == ans

    await communicator.send_json_to(
        {
            'action': 'list',
            'route': '?page=10',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'list',
        'route': '?page=10',
        'status': 200,
    }
    assert len(response_data['results']) == 10
    assert response_data['count'] == 100
    assert response_data['next'] is None
    assert response_data['previous'] == '?page=9'

    for data, ans in zip(response_data['results'], answers[90:100]):
        data.pop('id')
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
                r'test_child_route/(?P<pk>[-\w]+)/$',
                ChildActionHandler.as_aaah(),
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

    await communicator.send_json_to(
        {
            'action': 'retrieve',
            'route': f'test_child_route/{answers[0]["id"]}/',
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': answers[0],
        'action': 'retrieve',
        'route': f'test_child_route/{answers[0]["id"]}/',
        'status': 200,
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
        'status': 200,
    }

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_api_action_handler():

    class ChildActionHandler(generics.UpdateAPIActionHandler):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    class ParentConsumer(AsyncAPIConsumer):

        routepatterns = [
            re_path(
                r'test_child_route/(?P<pk>[-\w]+)/$',
                ChildActionHandler.as_aaah(),
            )
        ]

    # Test a normal connection
    communicator = ExtendedWebsocketCommunicator(ParentConsumer(), '/testws/')

    # Create 2 TestModel
    original_answers = [
        dict(id=1, title='Title', content='Content'),
        dict(id=2, title='Title2', content='Content2'),
    ]
    for ans in original_answers:
        await database_sync_to_async(TestModel.objects.get_or_create)(**ans)

    connected, _ = await communicator.connect()

    assert connected

    ##### partial_update #####
    await communicator.send_json_to(
        {
            'action': 'partial_update',
            'data': {'title': 'titletitle'},
            'route': f'test_child_route/{original_answers[0]["id"]}/',
        }
    )

    response = await communicator.receive_json_from()
    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'partial_update',
        'route': f'test_child_route/{original_answers[0]["id"]}/',
        'status': 200,
    }
    assert response_data != original_answers[0]
    assert response_data['title'] == 'titletitle'

    instance = await database_sync_to_async(TestModel.objects.get)(
        pk=response_data['id']
    )
    assert response_data == model_to_dict(instance)

    ##### update #####
    # failure
    await communicator.send_json_to(
        {
            'action': 'update',
            'data': {'title': 'titletitle'},
            'route': f'test_child_route/{original_answers[0]["id"]}/',
        }
    )

    response = await communicator.receive_json_from()

    response['status'] = 400

    # success
    await communicator.send_json_to(
        {
            'action': 'update',
            'data': {
                'id': original_answers[0]['id'],
                'title': 'titletitle',
                'content': 'contentcontent',
            },
            'route': f'test_child_route/{original_answers[0]["id"]}/',
        }
    )

    response = await communicator.receive_json_from()

    response_data = response.pop('data')
    assert response == {
        'errors': [],
        'action': 'update',
        'route': f'test_child_route/{original_answers[0]["id"]}/',
        'status': 200,
    }
    assert response_data != original_answers[0]
    assert response_data['title'] == 'titletitle'
    assert response_data['content'] == 'contentcontent'

    instance = await database_sync_to_async(TestModel.objects.get)(
        pk=response_data['id']
    )
    assert response_data == model_to_dict(instance)

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_destroy_api_action_handler():

    class ChildActionHandler(generics.DestroyAPIActionHandler):
        serializer_class = TestSerializer
        queryset = TestModel.objects.all()

    class ParentConsumer(AsyncAPIConsumer):

        routepatterns = [
            re_path(
                r'test_child_route/(?P<pk>[-\w]+)/$',
                ChildActionHandler.as_aaah(),
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

    # exists
    await database_sync_to_async(TestModel.objects.get)(pk=answers[0]['id'])

    await communicator.send_json_to(
        {
            'action': 'destroy',
            'route': f'test_child_route/{answers[0]["id"]}/',
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': None,
        'action': 'destroy',
        'route': f'test_child_route/{answers[0]["id"]}/',
        'status': 204,
    }

    with pytest.raises(TestModel.DoesNotExist):
        await database_sync_to_async(TestModel.objects.get)(pk=answers[0]['id'])

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_destroy_api_consumer():

    class ParentConsumer(generics.DestroyAPIConsumer):
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

    # exists
    await database_sync_to_async(TestModel.objects.get)(pk=data['id'])

    await communicator.send_json_to(
        {
            'action': 'destroy',
            'route': f'test_child_route/{data["id"]}/',
        }
    )

    response = await communicator.receive_json_from()
    assert response == {
        'errors': [],
        'data': None,
        'action': 'destroy',
        'route': f'test_child_route/{data["id"]}/',
        'status': 204,
    }

    with pytest.raises(TestModel.DoesNotExist):
        await database_sync_to_async(TestModel.objects.get)(pk=data['id'])

    await communicator.disconnect()
