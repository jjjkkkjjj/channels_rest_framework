from __future__ import annotations

# reference: https://github.com/NilCoalescing/djangochannelsrestframework/blob/master/djangochannelsrestframework/decorators.py
import asyncio
from functools import wraps

from channels.db import database_sync_to_async


def async_action(**kwargs):
    """Set the method as async action.
    Note that use `async_to_sync`
    if you call the method decorated by this decorator in sync method

    Parameters
    ----------
    mode : str
        The available modes are ['response', 'broadcast', 'none']
        'response': Send the response to the user sending this action
        'broadcast': Broadcast the response to the users in the specific group
        'none': Do nothing at all
    broadcast_type : str
        The type for broadcasting. If you specify this variable,
        use '_general.broadcast'
    send_response_in_broadcast : bool
        Whether to send the response in broadcast mode, default to True
    """
    mode = kwargs.get('mode', 'response')
    if mode not in ['response', 'broadcast', 'none']:
        raise ValueError(
            f"The {mode} is invalid. Set mode in {['response', 'broadcast', 'none']}"
        )

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
