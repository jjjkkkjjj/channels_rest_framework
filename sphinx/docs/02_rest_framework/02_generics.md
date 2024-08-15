# Generics

Let's see the generic action list corresponding to HTTP request method again.

|     action     | HTTP request |
| :------------: | :----------: |
|    retrieve    |     GET      |
|      list      |     GET      |
|     create     |     POST     |
|     update     |     PUT      |
| partial_update |    PATCH     |
|     remove     |    DELETE    |

Since the action is corresponding to the HTTP request, we can implement generics `ActionHandler`s and `Consumer`s almost same as [rest_framework's generics](https://www.django-rest-framework.org/api-guide/generic-views/).
If you have already understood the rest_framework's generics, there will be no need to explain.

|            Action Handler             |             Consumer             |  rest_framework's Generics   |                action                 |
| :-----------------------------------: | :------------------------------: | :--------------------------: | :-----------------------------------: |
|     GenericAsyncAPIActionHandler      |     GenericAsyncAPIConsumer      |        GenericAPIView        |                  n/a                  |
|        CreateAPIActionHandler         |        CreateAPIConsumer         |        CreateAPIView         |                create                 |
|         ListAPIActionHandler          |         ListAPIConsumer          |         ListAPIView          |                 list                  |
|       RetrieveAPIActionHandler        |       RetrieveAPIConsumer        |       RetrieveAPIView        |               retrieve                |
|        UpdateAPIActionHandler         |        UpdateAPIConsumer         |        UpdateAPIView         |         update/partial_update         |
|        DestroyAPIActionHandler        |        DestroyAPIConsumer        |        DestroyAPIView        |                remove                 |
|      ListCreateAPIActionHandler       |      ListCreateAPIConsumer       |      ListCreateAPIView       |              list/create              |
|    RetrieveUpdateAPIActionHandler     |    RetrieveUpdateAPIConsumer     |    RetrieveUpdateAPIView     |    retrieve/update/partial_update     |
|    RetrieveDestroyAPIActionHandler    |    RetrieveDestroyAPIConsumer    |    RetrieveDestroyAPIView    |            retrieve/remove            |
| RetrieveUpdateDestroyAPIActionHandler | RetrieveUpdateDestroyAPIConsumer | RetrieveUpdateDestroyAPIView | retrieve/update/partial_update/remove |

## Create Example

As mentioned before, `Consumer`s in the rest_framework_channels is also `ActionHandler`.
When you give your consumer inherit with `generics.CreateAPIConsumer` and write down the serializer and queryset, you are all set to create a model!

```python
from rest_framework_channels import generics

class ParentConsumer(generics.CreateAPIConsumer):
    serializer_class = TestSerializer
    queryset = TestModel.objects.all()
```

After establishing the connection and sending the below json,

```python
{
    'action': 'create',
    'data': {
        'title': 'Title',
        'content': 'Content'
        # route: '' # you don't need specify the route because of handled by Consumer
    },
}
```

the new model will be created and you will get the below response.

```python
{
    'errors': [],
    'action': 'create',
    'data': {
        'id': 1,
        'title': 'Title',
        'content': 'Content'
    }
    'route': '',
    'status': 201,
}
```

## Retrieve Example

Let's see the `retrieve` example. You should inherit `RetrieveAPIActionHandler` to your `ActionHandler` like this;

```python
from rest_framework_channels import generics
from rest_framework_channels.consumers import AsyncAPIConsumer
from rest_framework_channels.permissions import IsAuthenticated

class ChildActionHandler(generics.RetrieveAPIActionHandler):
    serializer_class = TestSerializer
    queryset = TestModel.objects.all()
    permission_classes = (IsAuthenticated,)

class ParentConsumer(AsyncAPIConsumer):
    # You can define the routing inside the consumer similar with original django's urlpatterns
    routepatterns = [
        re_path(
            r'test_child_route/(?P<pk>[-\w]+)/$',
            ChildActionHandler.as_aaah(),
        ),
    ]
```

When you send the below json after establishing the connection,

```python
{
    'action': 'retrieve', # Similar with GET method of HTTP request
    'route': 'test_child_route/1/',
}
```

you will get the below response. This mechanism is very similar with original rest_framework!

```python
{
    'errors': [],
    'data': {
        'id': 1,
        'title': 'title',
        'content': 'content'
    },
    'action': 'retrieve',
    'route': 'test_child_route/1/',
    'status': 200,
}
```

## List Example

Let's see the `list` example. We show the example of `Consumer` here. You should inherit `ListAPIConsumer` to your `Consumer` like this;

```python
from rest_framework_channels import generics
from rest_framework_channels.permissions import IsAuthenticated

class ParentConsumer(generics.ListAPIConsumer):
    serializer_class = TestSerializer
    queryset = TestModel.objects.all()
    permission_classes = (IsAuthenticated,)
```

When you send the below json after establishing the connection,

```python
{
    'action': 'list'
}
```

you will get the below response. This mechanism is very similar with original rest_framework!

```python
{
    'errors': [],
    'data': [
        {
            'id': 1,
            'title': 'title',
            'content': 'content'
        },
        {
            'id': 2,
            'title': 'title2',
            'content': 'content2'
        },
    ],
    'action': 'list',
    'route': '',
    'status': 200,
}
```
