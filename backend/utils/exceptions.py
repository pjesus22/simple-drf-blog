from apps.uploads.exceptions import UploadError
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework_json_api.exceptions import (
    exception_handler as jsonapi_exception_handler,
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def custom_exception_handler(exc, context):
    """
    Central exception router.

    Responsibilities:
    - Translate domain-level UploadErrors into DRF ValidationErrors
    - Route authentication/JWT errors through DRF's default handler
    - Delegate all other errors to JSON:API exception handler
    """
    if isinstance(exc, UploadError):
        exc = DRFValidationError({"detail": str(exc)})

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
