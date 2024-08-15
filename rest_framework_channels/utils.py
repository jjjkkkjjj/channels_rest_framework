from __future__ import annotations

# reference: https://github.com/NilCoalescing/djangochannelsrestframework/blob/master/djangochannelsrestframework/scope_utils.py
import asyncio
from typing import Any, Callable

from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, QueryDict
from rest_framework.request import Request


def ensure_async(method: Callable):
    """
    Ensure method is async if not wrap it in database_sync_to_async.
    """
    if asyncio.iscoroutinefunction(method):
        return method
    return database_sync_to_async(method)


def request_from_scope(scope: dict[str, Any]) -> Request:

    request = HttpRequest()
    request.path = scope.get('path')
    request.session = scope.get('session')
    request.user = scope.get('user', AnonymousUser())

    request.META['HTTP_CONTENT_TYPE'] = 'application/json'
    request.META['HTTP_ACCEPT'] = 'application/json'

    for header_name, value in scope.get('headers', []):
        request.META[header_name.decode('utf-8')] = value.decode('utf-8')

    path_remaining = scope.get('path_remaining')
    if path_remaining:
        if path_remaining[0] == '?':
            path_remaining = path_remaining[1:]
        request.META['QUERY_STRING'] = path_remaining
        request.GET = QueryDict(path_remaining, mutable=True)

    connection_type = scope.get('type')
    if connection_type == 'websocket':
        # construct dummy host
        # TODO: Add actual host
        allowed_host = settings.ALLOWED_HOSTS
        if isinstance(allowed_host, (list, tuple)):
            allowed_host = allowed_host[0]
        if allowed_host == '*':
            allowed_host = '127.0.0.1'
        request.META['SERVER_NAME'] = allowed_host
        request.META['SERVER_PORT'] = 443 if request.is_secure() else 80

    if scope.get('cookies'):
        request.COOKIES = scope.get('cookies')

    request = Request(request)
    return request
