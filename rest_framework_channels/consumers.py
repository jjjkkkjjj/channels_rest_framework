from __future__ import annotations

import logging
from typing import Callable

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework.exceptions import APIException, MethodNotAllowed, PermissionDenied

from .handlers import AsyncAPIActionHandler
from .utils import ensure_async

# Get an instance of a logger
logger = logging.getLogger(__name__)


class AsyncAPIConsumerBase(AsyncJsonWebsocketConsumer, AsyncAPIActionHandler):

    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        """
        Dispatches incoming messages to type-based handlers asynchronously.
        """
        self.action = None
        # store recieve function (`send` and `scope` will be saved by parent __init__)
        if self._sync:
            self.base_receive = async_to_sync(receive)
        else:
            self.base_receive = receive
        self.args = ()
        self.kwargs = dict()
        if 'url_route' in scope:
            if 'args' in scope['url_route']:
                self.args = scope['url_route']['args']
            if 'kwargs' in scope['url_route']:
                self.kwargs = scope['url_route']['kwargs']
        await super().__call__(scope, receive, send)

    async def receive_json(self, content, **kwargs):
        # call AsyncAPIActionHandler's receive_json
        # instead of AsyncJsonWebsocketConsumer
        return await AsyncAPIActionHandler.receive_json(self, content, **kwargs)


class AsyncAPIConsumer(AsyncAPIConsumerBase):

    async def websocket_connect(self, message):
        """
        Called when a WebSocket connection is opened.
        """
        try:
            for permission in await self.get_permissions():
                if not await ensure_async(permission.can_connect)(
                    scope=self.scope, handler=self, message=message
                ):
                    raise PermissionDenied()
            await super().websocket_connect(message)
        except PermissionDenied:
            await self.close()

    async def websocket_disconnect(self, message):
        # TODO: detached tasks
        # for task in self.detached_tasks:
        #     task.cancel()
        #     await self.handle_detached_task_completion(task)
        await super().websocket_disconnect(message)
