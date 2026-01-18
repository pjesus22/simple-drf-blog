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
        response: The DRF object response to assert.
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


def assert_jsonapi_error_pointers(
    response: Response, *, status_code: int, expected_pointers: set[str]
):
    """
    Asserts that a response is a JSON:API error response containing exactly the
    expected set of error source pointers.

    Args:
        response: The DRF response object to assert.
        status_code: The expected status code.
        expected_pointers: A set of expected field names corresponding to the
            JSON:API error `source.pointer` values.

    Raises:
        AssertionError: If the response is not a JSON:API error response.
    """
    assert response.status_code == status_code

    body = response.json()

    assert "errors" in body
    assert isinstance(body["errors"], list)
    assert body["errors"]

    pointers = {
        e["source"]["pointer"].split("/")[-1]
        for e in body["errors"]
        if "source" in e and "pointer" in e["source"]
    }

    assert pointers == expected_pointers
