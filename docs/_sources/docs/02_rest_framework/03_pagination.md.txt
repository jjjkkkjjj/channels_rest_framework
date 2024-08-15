# Pagination

The pagination is also useful when you have a large model in your project. You can use [Paginator](https://www.django-rest-framework.org/api-guide/pagination/) in rest_framework_channels too.

## Example

Let's see the example.

```python
from rest_framework.pagination import PageNumberPagination
from rest_framework_channels import generics
from rest_framework_channels.consumers import AsyncAPIConsumer

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
```

As you can see the above example, all you have to do is add the `pagination_class` only. This is same as original one.

When you send the below json after establishing the connection,

```python
{
    'action': 'list', # pagination will be used in list action at the almost cases
    'route': 'test_child_route/?page=4',
}
```

The response will be the below. It's awesome!

```python
{
    'errors': [],
    'action': 'list',
    'route': 'test_child_route/?page=4',
    'status': 200,
    'data': {
        'count': 100,
        'next': 'test_child_route/?page=5',
        'previous': 'test_child_route/?page=3',
        'results': [
            {
                'id': 31,
                'title': 'Title31',
                'content': 'Content31',
            },
            {
                'id': 32,
                'title': 'Title32',
                'content': 'Content32',
            },
            ...

            {
                'id': 40,
                'title': 'Title40',
                'content': 'Content40',
            },
        ]
    }
}
```

```{note}
`next`in response specifies the next **route** not url. `previous` is as well.
```
