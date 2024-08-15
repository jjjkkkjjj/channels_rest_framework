from __future__ import annotations

# reference: https://github.com/NilCoalescing/djangochannelsrestframework/blob/master/djangochannelsrestframework/consumers.py
import json
import logging
from functools import partial, update_wrapper
from typing import Callable, Optional
from urllib.parse import parse_qs, urlencode, urlparse

from asgiref.sync import async_to_sync
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.http.response import Http404
from django.urls.resolvers import RegexPattern, RoutePattern, URLPattern, URLResolver
from rest_framework.exceptions import (
    APIException,
    MethodNotAllowed,
    NotFound,
    PermissionDenied,
)
from rest_framework.permissions import AND, NOT, OR
from rest_framework.permissions import BasePermission as DRFBasePermission
from typing_extensions import Self

from .exceptions import ActionMissingException
from .permissions import BasePermission, WrappedDRFPermission
from .routings import RoutingManager
from .settings import api_settings
from .utils import ensure_async

# Get an instance of a logger
logger = logging.getLogger(__name__)


class APIActionHandlerMetaclass(type):
    """
    Metaclass that records action and route methods
    """

    def __new__(mcs, name, bases, body):
        cls = type.__new__(mcs, name, bases, body)

        cls.available_actions = {}
        cls.routing = RoutingManager()
        for method_name in dir(cls):
            attr = getattr(cls, method_name)
            is_action = getattr(attr, 'is_action', False)
            if is_action:
                kwargs = getattr(attr, 'kwargs', {})
                name = kwargs.get('name', method_name)
                cls.available_actions[name] = method_name

        for route in getattr(cls, 'routepatterns', []):

            pattern = route.pattern
            if isinstance(pattern, RegexPattern):
                arg = pattern._regex
            elif isinstance(pattern, RoutePattern):
                arg = pattern._route
            else:
                raise ValueError(f'Unsupported pattern type: {type(pattern)}')
            route.pattern = pattern.__class__(arg, pattern.name, is_endpoint=False)

            if not route.callback and isinstance(route, URLResolver):
                raise ImproperlyConfigured(f'{route}: include() is not supported.')

            assert isinstance(route, URLPattern)
            cls.routing.append(route)

        return cls


class AsyncActionHandler(metaclass=APIActionHandlerMetaclass):
    """
    Action Handler class

    Note: This class is "Action Handler" NOT Consumer
    When you want to use this as consumer, use consumers.AsyncAPIConsumer instead
    """

    # key: action name, value: method name
    available_actions: dict[str, str]

    _sync = False

    # manage routes
    routing: RoutingManager
    routepatterns = []

    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        """
        Dispatches incoming messages to type-based handlers asynchronously.
        """
        self.action = None
        self.scope = scope
        if self._sync:
            self.base_receive = async_to_sync(receive)
            self.base_send = async_to_sync(send)
        else:
            self.base_receive = receive
            self.base_send = send
        self.args = ()
        self.kwargs = dict()
        if 'url_route' in scope:
            if 'args' in scope['url_route']:
                self.args = scope['url_route']['args']
            if 'kwargs' in scope['url_route']:
                self.kwargs = scope['url_route']['kwargs']
        return self

    async def send(self, text_data=None, bytes_data=None, close=False):
        """
        Sends a reply back down the WebSocket
        """
        if text_data is not None:
            await self.base_send({'type': 'websocket.send', 'text': text_data})
        elif bytes_data is not None:
            await self.base_send({'type': 'websocket.send', 'bytes': bytes_data})
        else:
            raise ValueError('You must pass one of bytes_data or text_data')
        if close:
            await self.close(close)

    async def close(self, code=None, reason=None):
        """
        Closes the WebSocket from the server end
        """
        message = {'type': 'websocket.close'}
        if code is not None and code is not True:
            message['code'] = code
        if reason:
            message['reason'] = reason
        await self.base_send(message)

    async def send_json(self, content, close=False):
        """
        Encode the given content as JSON and send it to the client.
        """
        await self.send(text_data=await self.encode_json(content), close=close)

    @classmethod
    async def decode_json(cls, text_data):
        return json.loads(text_data)

    @classmethod
    async def encode_json(cls, content) -> str:
        return json.dumps(content)

    @classmethod
    def as_aaah(cls, **initkwargs) -> Self:
        """
        Return an Async API Action Handler (not scream) single callable that
        instantiates a action handler instance per scope.
        Similar in purpose to Django's as_view().

        initkwargs will be used to instantiate the action handler instance.
        """

        async def app(scope, receive, send):
            handler = cls(**initkwargs)
            return await handler(scope, receive, send)

        app.handler_class = cls
        app.handler_initkwargs = initkwargs

        # take name and docstring from class
        update_wrapper(app, cls, updated=())
        return app


class AsyncAPIActionHandler(AsyncActionHandler):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    async def get_permissions(self, **kwargs) -> list[BasePermission]:
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_instances = []
        for permission_class in self.permission_classes:
            instance = permission_class()

            # If the permission is an DRF permission instance
            if isinstance(instance, (DRFBasePermission, OR, AND, NOT)):
                instance = WrappedDRFPermission(instance)
            permission_instances.append(instance)

        return permission_instances

    async def check_permissions(self, action: str, **kwargs) -> None:
        """
        Check if the action should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in await self.get_permissions(**kwargs):

            if not await ensure_async(permission.has_permission)(
                scope=self.scope, handler=self, action=action, **kwargs
            ):
                raise PermissionDenied()

    async def check_object_permissions(self, action: str, obj: Model, **kwargs) -> None:
        """
        Check if the action should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in await self.get_permissions(**kwargs):

            if not await ensure_async(permission.has_object_permission)(
                scope=self.scope, handler=self, action=action, obj=obj, **kwargs
            ):
                raise PermissionDenied()

    async def handle_exception(self, exc: Exception, action: Optional[str], route: str):
        """
        Handle any exception that occurs, by sending an appropriate message
        """
        if isinstance(exc, APIException):
            await self.reply(
                action=action,
                errors=self._format_errors(exc.detail),
                status=exc.status_code,
                route=route,
            )
        elif exc == Http404 or isinstance(exc, Http404):
            await self.reply(
                action=action,
                errors=self._format_errors('Not found'),
                status=404,
                route=route,
            )
        else:
            logger.error(
                f'Error when handling request: {action}',
                exc_info=exc,
            )
            raise exc

    def _format_errors(self, errors):
        if isinstance(errors, list):
            return errors
        elif isinstance(errors, (str, dict)):
            return [errors]

    async def handle_action(self, action: str, route: Optional[str], **kwargs):
        """
        Handle a call for a given action.

        This method checks permissions and handles exceptions sending
        them back over the ws connection to the client.

        If there is no action listed on the consumer for this action name
        a `MethodNotAllowed` error is sent back over the ws connection.
        """
        try:
            await self.check_permissions(action, **kwargs)

            try:
                # resolve route
                handler: AsyncActionHandler = await self.routing.resolve(
                    route, self.scope, self.base_receive, self.base_send
                )
                response = await handler.handle_action(action, route, **kwargs)
            except NotFound:
                # the action will be processed this class

                if action not in self.available_actions:
                    raise MethodNotAllowed(method=action) from None

                method_name = self.available_actions[action]
                method = getattr(self, method_name)

                reply = partial(self.reply, action=action)

                # the @action decorator will wrap non-async action into async ones.
                # append query params to path_reamining if it exists
                query_dict = {}
                if route:
                    query_dict.update(parse_qs(urlparse(route).query))

                path_remaining = self.scope.get('path_remaining')
                if path_remaining:
                    query_dict.update(parse_qs(urlparse(path_remaining).query))

                query = urlencode(query_dict, doseq=True)
                if query:
                    self.scope.update(dict(path_remaining=query))

                response = await method(action=action, **kwargs)

            if isinstance(response, tuple):
                data, status = response
                await reply(data=data, status=status, route=route)

        except Exception as exc:
            await self.handle_exception(exc, action=action, route=route)

    async def receive_json(self, content: dict, **kwargs):
        if 'action' not in content:
            await self.handle_exception(ActionMissingException(), action=None)
            return
        action = content.pop('action')
        # None means apply action in this consumer
        route = content.pop('route', '')

        await self.handle_action(action, route, **content)

    async def reply(
        self,
        action: Optional[str],
        route: str,
        data=None,
        errors=None,
        status=200,
    ):
        """
        Send a json response back to the client.

        """

        if errors is None:
            errors = []

        payload = {
            'errors': errors,
            'data': data,
            'action': action,
            'route': route,
            'status': status,
        }

        await self.send_json(payload)
