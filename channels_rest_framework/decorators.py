import asyncio
from functools import wraps

from channels.db import database_sync_to_async

from .consumers import AsyncAPIConsumerBase


def action(**kwargs):
    def action_wrapper(func):
        func.is_action = True
        func.kwargs = kwargs

        if asyncio.iscoroutinefunction(func):
            return func

        # convert sync to async function
        @wraps(func)
        async def async_function(self, *args, **kwargs):
            response = await database_sync_to_async(func)(self, *args, **kwargs)
            return response

        async_function.is_action = True
        async_function.kwargs = kwargs

        return async_function

    return action_wrapper


def route(cls: type[AsyncAPIConsumerBase], route: str, **initkwargs):
    def route_wrapper(func):
        func.consumer_cls = cls
        func.kwargs = initkwargs
        func.is_route = True
        func.route = route

        # @wraps(func)
        # async def app(scope, recieve, send):
        #     # TODO: parse route and set args, kwargs!!
        #     consumer = cls(**initkwargs)
        #     return await consumer(scope, recieve, send)

        # app.consumer_cls = cls
        # app.kwargs = initkwargs
        # app.is_route = True
        # app.route = route

        return func

    return route_wrapper
