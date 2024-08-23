from __future__ import annotations

from urllib.parse import unquote, urlparse

from channels.db import database_sync_to_async
from channels.testing.websocket import WebsocketCommunicator
from django.contrib.auth import get_user_model


class ExtendedWebsocketCommunicator(WebsocketCommunicator):
    def __init__(
        self,
        application,
        path,
        headers=None,
        subprotocols=None,
        spec_version=None,
        args=tuple(),
        kwargs=dict(),  # noqa: B006
    ):
        if not isinstance(path, str):
            raise TypeError(f'Expected str, got {type(path)}')
        parsed = urlparse(path)
        self.scope = {
            'type': 'websocket',
            'path': unquote(parsed.path),
            'query_string': parsed.query.encode('utf-8'),
            'headers': headers or [],
            'subprotocols': subprotocols or [],
            'url_route': {'args': args, 'kwargs': kwargs},
        }
        if spec_version:
            self.scope['spec_version'] = spec_version
        super(WebsocketCommunicator, self).__init__(application, self.scope)
        self.response_headers = None


class AuthCommunicator(ExtendedWebsocketCommunicator):
    def __init__(
        self,
        user,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        # https://github.com/django/channels/issues/903#issuecomment-368412478
        # Scope should be set already from WebsocketCommunicator or HttpCommunicator
        self.scope.update({'user': user})
