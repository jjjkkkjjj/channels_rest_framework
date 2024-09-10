from __future__ import annotations

import pytest
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from rest_framework_channels.exceptions import (
    debug_exception_handlers,
    production_exception_handlers,
)
from rest_framework_channels.handlers import AsyncActionHandler


@database_sync_to_async
def create_user():
    return get_user_model().objects.create_user(username='test', password='password')


@pytest.fixture
def user():
    return async_to_sync(create_user)()


@pytest.fixture
def debug_exception_handler():
    # I couldn't override the settings by `from django.test import override_settings`
    # Workaround is here
    AsyncActionHandler.exception_handler = debug_exception_handlers
    yield
    # revert
    AsyncActionHandler.exception_handler = production_exception_handlers
