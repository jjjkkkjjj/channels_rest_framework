# reference: https://github.com/NilCoalescing/djangochannelsrestframework/blob/master/djangochannelsrestframework/decorators.py
import asyncio
from functools import wraps

from channels.db import database_sync_to_async


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
