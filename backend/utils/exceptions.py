from apps.accounts.exceptions import AccountDomainError
from apps.uploads.exceptions import UploadDomainError
from rest_framework.exceptions import (
    AuthenticationFailed,
    ErrorDetail,
    NotAuthenticated,
)
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework_json_api.exceptions import (
    exception_handler as jsonapi_exception_handler,
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def _normalize_error_detail(value):
    if isinstance(value, ErrorDetail):
        return str(value)
    if isinstance(value, list):
        return [_normalize_error_detail(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize_error_detail(v) for k, v in value.items()}
    return value


def custom_exception_handler(exc, context):
    """
    Central exception router.

    Responsibilities:
    - Translate domain-level errors into DRF ValidationErrors
    - Route authentication/JWT errors through DRF's default handler
    - Delegate all other errors to JSON:API exception handler
    """
    DOMAIN_ERRORS = (UploadDomainError, AccountDomainError)

    if isinstance(exc, DOMAIN_ERRORS):
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

    response = jsonapi_exception_handler(exc, context)

    if response is not None and response.data is not None:
        response.data = _normalize_error_detail(response.data)

    return response


# Auth/JWT errors intentionally bypass JSON:API formatting
# to keep compatibility with DRF and common clients
