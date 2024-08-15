# Introduction

```{toctree}
:maxdepth: 2
:caption: Contents

./00_action
./01_action_handler.md
./02_routing
```

rest_framework_channels is the enhanced modules for REST WebSockets using django [channels](https://channels.readthedocs.io/en/latest/).

You can use `serializers` and `queryset` in [rest_framework](https://www.django-rest-framework.org/) in rest_framework_channels. Also, we are ready for similar `permissions` and `generics` too.

```{note}
We use the below model and serializer as example here.
```

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
