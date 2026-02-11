import pytest

from config.views import APIRootView

pytestmark = pytest.mark.django_db


class TestAPIRootView:
    def test_get_view_name_returns_api_root(self):
        view = APIRootView()
        assert view.get_view_name() == "API Root"

    def test_get_returns_all_endpoints(self, rf):
        request = rf.get("/")
        view = APIRootView.as_view()

        response = view(request)

        assert response.status_code == 200
        assert "admin" in response.data
        assert "api_v1" in response.data
        assert "health" in response.data
        assert "token_obtain_pair" in response.data
        assert "token_refresh" in response.data
        assert "token_verify" in response.data

    def test_get_returns_proper_urls(self, rf):
        request = rf.get("/")
        view = APIRootView.as_view()

        response = view(request)
        for value in response.data.values():
            assert isinstance(value, str)
            assert value.startswith(("http://", "/"))
