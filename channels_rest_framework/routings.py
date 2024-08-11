from typing import Any

from django.urls import URLPattern
from django.urls.exceptions import Resolver404
from rest_framework.exceptions import NotFound


class RoutingManager:
    def __init__(self):
        self.routes: list[URLPattern] = []

    def append(self, pattern) -> None:
        """Add new route to be managed

        Parameters
        ----------
        pattern: URLPattern
            The URLPattern instance
        """
        self.routes.append(pattern)

    # Any is intended for avoiding vscode's testing error due to circular import
    async def resolve(self, route: str, scope: dict, receive, send, **kwargs) -> Any:

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
                        ),
                        receive,
                        send,
                    )
            except Resolver404:
                pass

        raise NotFound(f'No route found: {route}')
