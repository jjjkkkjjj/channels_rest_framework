# Action

Action is a concept of rest_framework_channels to handle the message. Action is similar with HTTP request method, moreover you can define the original action flexibly.

The client establishes the connection to the server using websocket, first.
Once establishing the connection, you can send the messages with any actions. All actions will be handled by `ActionHandler` (detailed in next section) which is similar with `Consumer`.
Thanks to `ActionHandler`, you can handle with all actions very easily.

```{note}
Note that all `ActionHandler`s in `rest_framework_channels.handlers` and `Consumer`s in `rest_framework_channels.consumers` are inherited from `AsyncActionHandler` which is the base class of `ActionHandler`. Therefore, `Consumer` is also `ActionHandler`.
```

```{eval-rst}
.. uml::

    group channels
        Client -> Consumer: connect
        return accept
    end
    
    group rest_framework_channels
        Client -> Consumer: action

        Consumer -> ActionHandler: action
        return response

        Consumer -> Client: response
    end

    group channels
        Client -> Consumer: disconnect
        return close
    end
```

## Generics Action List

We are ready for generics `ActionHandler` (such like [rest_framework's generics view](https://www.django-rest-framework.org/api-guide/generic-views/)). Thanks to these generics, you can implement the codes handling with some actions very easily. And these generics interfaces are almost same as the rest_framework's generics view. That's why you can implement the websockets code easily!

Here is the generic action list corresponding to HTTP request method.

|     action     | HTTP request |
| :------------: | :----------: |
|    retrieve    |     GET      |
|      list      |     GET      |
|     create     |     POST     |
|     update     |     PUT      |
| partial_update |    PATCH     |
|     remove     |    DELETE    |

### Retrieve Example

We use the below model and serializer as example.

```python
class TestModel(models.Model):
    """Simple model to test with."""

    title = models.CharField(max_length=255)
    content = models.CharField(max_length=1024)

class TestSerializer(ModelSerializer):
    class Meta:
        model = TestModel
        fields = '__all__'
```

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

### Create Example

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

## Define your custom action

When you want to handle with your custom action, you can define the handler method warapped `async_action` decorator.

```python
from rest_framework_channels.handlers import AsyncAPIActionHandler
from rest_framework_channels.decorators import async_action
from rest_framework_channels.consumers import AsyncAPIConsumer

class ChildActionHandler(AsyncAPIActionHandler):

    @async_action()
    def your_custom_action(self, pk, *args, **kwargs):
        # Note: you should return the data and status code.
        return { 
            'message': 'your_custom_action will be handled',
            'model_id': pk
        }, 200

class ParentConsumer(AsyncAPIConsumer):
    routepatterns = [
        re_path(
            r'test_child_route/(?P<pk>[-\w]+)/$',
            ChildActionHandler.as_aaah(),
        ),
    ]
```

After establishing the connection and sending the below json,

```python
{
    'action': 'your_custom_action', # your method name will be action's name directly
    'route': 'test_child_route/5/'
}
```

the new model will be created and you will get the below response.

```python
{
    'errors': [],
    'action': 'your_custom_action',
    'data': {
        'message': 'your_custom_action will be handled',
        'model_id': 5
    },
    'route': 'test_child_route/5/',
    'status': 200,
}
```

```{important}
As you can guess from the decorator's name `async_action`, your decorated method will be converted into the ASYNC method. That's why when you want to call this method in sync method, you should use `async_to_sync` in [asgiref](https://asgi.readthedocs.io/en/latest/).
```

```python
from asgiref.sync import async_to_sync

class ChildActionHandler(AsyncAPIActionHandler):
    permission_classes = (IsAuthenticated,)

    ...

    def your_sync_method(self, pk):
        data, status = async_to_sync(self.your_custom_action)(pk=pk)
        ...

```
