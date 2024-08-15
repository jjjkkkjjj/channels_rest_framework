from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from django.urls import URLPattern
from django.urls.exceptions import Resolver404
from rest_framework.exceptions import NotFound

if TYPE_CHECKING:
    from .handlers import AsyncActionHandler


class RoutingManager:
    def __init__(self):
        self.routes: list[URLPattern] = []

    def append(self, pattern: URLPattern) -> None:
        """Add new route to be managed

        Parameters
        ----------
        pattern: URLPattern
            The URLPattern instance
        """
        self.routes.append(pattern)

    # Any is intended for avoiding vscode's testing error due to circular import
    async def resolve(
        self, route: str, scope: dict, receive: Callable, send: Callable, **kwargs
    ) -> AsyncActionHandler:
        """Resolve a given route

        Parameters
        ----------
        route : str
            The route path to be resolved
        scope : dict
            The scope dict
        receive : Callable
            The recieve function to be passed into a matched action handler
        send : Callable
            The send function to be passed into a matched action handler

        Returns
        -------
        AsyncActionHandler
            The matched action handler
        """

        for routing in self.routes:
            try:
                match = routing.pattern.match(route)
                if match:
                    new_path, args, kwargs = match

                    # Add args or kwargs into the scope
                    outer = scope.get('url_route', {})
                    handler = routing.callback
                    return await handler(
                        dict(
                            scope,
                            path_remaining=new_path,
                            url_route={
                                'args': outer.get('args', ()) + args,
                                'kwargs': {**outer.get('kwargs', {}), **kwargs},
                            },
                            route=route
                        ),
                        receive,
                        send,
                    )
            except Resolver404:
                pass

        raise NotFound(f'No route found: {route}')
