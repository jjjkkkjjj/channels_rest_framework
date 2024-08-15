# Serializers

The serializer is very useful class for handling your model in the RESTful projects. Our rest_framework_channels interface allows us to use this novel class directly.

## Example

Let's see the example.

```python
from rest_framework_channels import generics
from rest_framework_channels.consumers import AsyncAPIConsumer
from rest_framework_channels.permissions import IsAuthenticated
from rest_framework_channels.decorators import async_action

class ChildActionHandler(generics.RetrieveAPIActionHandler):
    serializer_class = TestSerializer
    queryset = TestModel.objects.all()

    @async_action()
    def your_custom_action(self, *args, **kwargs):
        action = kwargs.get('action', 'your_custom_action')
        # get_object must recieve the action unlike original rest_framework
        instance = self.get_object(action)
        serializer = self.get_serializer(instance)

        # your logic here
        ...

        return serializer.data, 200


class ParentConsumer(AsyncAPIConsumer):
    # You can define the routing inside the consumer similar with original django's urlpatterns
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
    'action': 'your_custom_action',
    'route': 'test_child_route/5/'
}
```

`your_custom_action` will be called.

```{note}
In this case, the `kwargs` will include `pk=5`. Our routing system parses the `route` like the original django's routing system . For more detai see [routing section](#Routing) 
```
