# rest_framework_channels

The enhanced modules for REST WebSockets using django channels.

## Installation

```bash
pip install rest_framework_channels
```

## Introduction

rest_framework_channels is the enhanced modules for REST WebSockets using django [channels](https://channels.readthedocs.io/en/latest/).

You can use `serializers` and `queryset` in [rest_framework](https://www.django-rest-framework.org/) in rest_framework_channels. Also, we are ready for similar `permissions` and `generics` too.

### Example

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

As you can see `permission_classes`, you will be rejected when you send that json without login.

```python
{
    'errors': ['Some Error Messages']
    'data': None,
    'action': 'retrieve',
    'route': 'test_child_route/1/',
    'status': 403,
}
```

## Details

For more details, see [docs](https://jjjkkkjjj.github.io/rest_framework_channels/).

## Development

### code

```bash
pip install -e .
pip install twine
```

### documentation

```bash
cd sphinx
sudo apt-get -y install plantuml
pip install -r requirements.txt
```

- generate rst files and html files

```bash
cd sphinx
bash build.sh
```

## Reference

This project is VERY inspired by [djangochannelsrestframework](https://github.com/NilCoalescing/djangochannelsrestframework).
