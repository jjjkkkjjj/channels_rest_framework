# Installation

You can install rest_framework_channels via pip.

```bash
pip install rest_framework_channels
```

## Setting

After installing it, you should insert `'rest_framework_channels'` in the `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    # Websocket
    'daphne',
    'channels',
    'rest_framework_channels', # add
    ...
```

You can configure the default classes and so on in `settings.py`.

```python
REST_FRAMEWORK_CHANNELS = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework_channels.permissions.AllowAny'
    ],
    # Generic action handler behavior
    'DEFAULT_PAGINATION_CLASS': None,
    'DEFAULT_FILTER_BACKENDS': [],
    # Pagination
    'PAGE_SIZE': None,
}
```

```{important}
The configuration for all settings except `DEFAULT_PERMISSION_CLASSES` is same as original rest_framework.
See [docs](https://www.django-rest-framework.org/api-guide/settings/) for more details.
```
