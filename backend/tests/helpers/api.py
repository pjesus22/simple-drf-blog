from rest_framework.response import Response


def assert_jsonapi_error_response(
    response: Response,
    *,
    status_code: int,
    pointer: str | None = None,
    code: str | None = None,
    detail_contains: str | None = None,
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


def assert_drf_error_response(
    response: Response,
    *,
    status_code: int,
    detail_contains: str | None = None,
    code: str | None = None,
):
    """
    Asserts a standard DRF error response. Handles potential wrapping by
    the JSON:API renderer.
    """
    assert response.status_code == status_code

    body = response.json()

    errors = body.get("errors", body) if isinstance(body.get("errors"), dict) else body

    if detail_contains is not None:
        assert "detail" in errors
        assert detail_contains.lower() in errors["detail"].lower()

    if code is not None:
        assert "code" in errors
        assert code.lower() == errors["code"].lower()
