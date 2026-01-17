from typing import Optional

from rest_framework.response import Response


def assert_jsonapi_error_response(
    response: Response,
    *,
    status_code: int,
    pointer: Optional[str] = None,
    code: Optional[str] = None,
    detail_contains: Optional[str] = None,
    index: int = 0,
):
    """
    Asserts that a response is a JSON:API error response.

    Args:
        response: The response to assert.
        status_code: The expected status code.
        pointer: The expected JSON:API pointer.
        code: The expected error code.
        detail_contains: The expected error detail.
        index: The index of the error to assert.

    Raises:
        AssertionError: If the response is not a JSON:API error response.
    """
    assert response.status_code == status_code

    body = response.json()

    assert "errors" in body
    assert isinstance(body["errors"], list)
    assert body["errors"], "'errors' is empty"

    error = body["errors"][index]

    assert error["status"] == str(status_code)

    if pointer is not None:
        assert "source" in error
        assert error["source"]["pointer"] == pointer

    if code is not None:
        assert error.get("code") == code

    if detail_contains is not None:
        assert "detail" in error
        assert detail_contains.lower() in error["detail"].lower()
