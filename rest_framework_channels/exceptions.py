from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException, MethodNotAllowed


class ActionMissingException(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _('Unable to find action in message body.')
    default_code = 'method_not_allowed'


class RouteMissingException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('Unable to find route in message body.')
    default_code = 'method_not_allowed'
