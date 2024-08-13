from __future__ import annotations

# reference: https://github.com/NilCoalescing/djangochannelsrestframework/blob/master/djangochannelsrestframework/permissions.py
from typing import TYPE_CHECKING, Any, Union

from channels.db import database_sync_to_async
from django.db.models import Model
from rest_framework.permissions import BasePermission as DRFBasePermission

from .utils import ensure_async, request_from_scope

if TYPE_CHECKING:
    from .handlers import AsyncActionHandler


class OperationHolderMixin:
    def __and__(self, other):
        return OperandHolder(AND, self, other)

    def __or__(self, other):
        return OperandHolder(OR, self, other)

    def __rand__(self, other):
        return OperandHolder(AND, other, self)

    def __ror__(self, other):
        return OperandHolder(OR, other, self)

    def __invert__(self):
        return SingleOperandHolder(NOT, self)


class SingleOperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class):
        self.operator_class = operator_class
        self.op1_class = op1_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        return self.operator_class(op1)


class OperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class, op2_class):
        self.operator_class = operator_class
        self.op1_class = op1_class
        self.op2_class = op2_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        op2 = self.op2_class(*args, **kwargs)
        return self.operator_class(op1, op2)


class AND:
    def __init__(self, op1: BasePermission, op2: BasePermission):
        self.op1 = op1
        self.op2 = op2

    def has_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, action: str, **kwargs
    ):
        return self.op1.has_permission(
            scope, handler, action, **kwargs
        ) and self.op2.has_permission(scope, handler, action, **kwargs)


class OR:
    def __init__(self, op1: BasePermission, op2: BasePermission):
        self.op1 = op1
        self.op2 = op2

    def has_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, action: str, **kwargs
    ):
        return self.op1.has_permission(
            scope, handler, action, **kwargs
        ) or self.op2.has_permission(scope, handler, action, **kwargs)


class NOT:
    def __init__(self, op1: BasePermission):
        self.op1 = op1

    def has_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, action: str, **kwargs
    ):
        return not self.op1.has_permission(scope, handler, action, **kwargs)


class BasePermissionMetaclass(OperationHolderMixin, type):
    pass


class BasePermission(metaclass=BasePermissionMetaclass):
    """Base permission class

    Notes:
        You should extend this class
        and override the `has_permission` method to create your own permission class.

    Methods:
        async has_permission (scope, handler, action, **kwargs)
    """

    async def has_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, action: str, **kwargs
    ) -> bool:
        """
        Called on every websocket message sent
        before the corresponding action handler is called.
        """
        return True

    async def has_object_permission(
        self,
        scope: dict[str, Any],
        handler: AsyncActionHandler,
        action: str,
        obj: Model,
        **kwargs,
    ) -> bool:
        """
        Called on every websocket message sent
        before the corresponding action handler is called.
        """
        return True

    async def can_connect(
        self, scope: dict[str, Any], handler: AsyncActionHandler, message=None
    ) -> bool:
        """
        Called during connection to validate
        if a given client can establish a websocket connection.

        By default, this returns True and permits all connections to be made.
        """
        return True

    async def can_connect_by_object_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, obj: Model, **kwargs
    ) -> bool:
        """
        Called during connection to validate
        if a given client can establish a websocket connection.

        By default, this returns True and permits all connections to be made.
        """
        return True


class AllowAny(BasePermission):
    """Allow any permission class"""

    async def has_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, action: str, **kwargs
    ) -> bool:
        return True

    async def has_object_permission(
        self,
        scope: dict[str, Any],
        handler: AsyncActionHandler,
        action: str,
        obj: Model,
        **kwargs,
    ):
        return True


class IsAuthenticated(BasePermission):
    """Allow authenticated users"""

    async def has_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, action: str, **kwargs
    ) -> bool:
        user = scope.get('user')
        if not user:
            return False
        return user.pk and user.is_authenticated


class IsAuthenticatedStrictly(IsAuthenticated):
    """Allow authenticated users"""

    async def can_connect(
        self, scope: dict[str, Any], handler: AsyncActionHandler, message=None
    ) -> bool:
        return await super().has_permission(scope, handler, message)


class IsOwner(BasePermission):
    """Allow object owner"""

    lookup_field = 'user'
    # actions list or '__all__'
    check_actions: Union[list[str], str] = '__all__'

    async def has_object_permission(
        self,
        scope: dict[str, Any],
        handler: AsyncActionHandler,
        action: str,
        obj: Model,
        **kwargs,
    ):
        if isinstance(self.check_actions, str):
            if self.check_actions == '__all__':
                pass
            else:
                raise ValueError("check_actions accepts '__all__' only in case of str")
        elif (
            isinstance(self.check_actions, (list, tuple))
            and action not in self.check_actions
        ):
            return True

        assert await database_sync_to_async(hasattr)(
            obj, self.lookup_field
        ), f'The object must have "{self.lookup_field}" attribute'
        user = scope.get('user')
        if not user:
            return False

        return user == await database_sync_to_async(getattr)(obj, self.lookup_field)


class WrappedDRFPermission(BasePermission):
    """
    Used to wrap an instance of DRF permissions class.
    """

    permission: DRFBasePermission

    mapped_actions = {
        'create': 'PUT',
        'update': 'PATCH',
        'list': 'GET',
        'retrieve': 'GET',
        'connect': 'HEAD',
    }

    def __init__(self, permission: DRFBasePermission):
        self.permission = permission

    async def has_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, action: str, **kwargs
    ) -> bool:
        request = request_from_scope(scope)
        request.method = self.mapped_actions.get(action, action.upper())
        return await ensure_async(self.permission.has_permission)(request, handler)

    async def can_connect_by_object_permission(
        self, scope: dict[str, Any], handler: AsyncActionHandler, obj: Model, **kwargs
    ) -> bool:
        request = request_from_scope(scope)
        request.method = self.mapped_actions.get('connect', 'CONNECT')
        return await ensure_async(self.permission.has_object_permission)(
            request, handler, obj
        )

    async def can_connect(
        self, scope: dict[str, Any], handler: AsyncActionHandler, message=None
    ) -> bool:
        request = request_from_scope(scope)
        request.method = self.mapped_actions.get('connect', 'CONNECT')
        return await ensure_async(self.permission.has_permission)(request, handler)
