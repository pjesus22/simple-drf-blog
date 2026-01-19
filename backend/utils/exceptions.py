from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework_json_api.exceptions import (
    exception_handler as jsonapi_exception_handler,
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def custom_exception_handler(exc, context):
    """
    Routes authentication-related exceptions through DRF's default exception
    handler to avoid duplicate JSON:API errors caused by SimpleJWT, while
    delegating all other exceptions to the JSON:API exception handler.
    """
    if isinstance(
        exc,
        (
            AuthenticationFailed,
            NotAuthenticated,
            InvalidToken,
            TokenError,
        ),
    ):
        return drf_exception_handler(exc, context)
    return jsonapi_exception_handler(exc, context)
