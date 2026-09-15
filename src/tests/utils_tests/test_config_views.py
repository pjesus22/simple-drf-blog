from django.http import Http404
import pytest

from config.views import APIRootView, dev_media_serve


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


class TestDevMediaServe:
    def test_blocks_private_paths(self, rf, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        request = rf.get("/media/private/avatar/x.txt")

        with pytest.raises(Http404):
            dev_media_serve(request, "private/avatar/x.txt")

    def test_serves_public_file(self, rf, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        target = tmp_path / "avatar" / "x.txt"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"hello")

        request = rf.get("/media/avatar/x.txt")
        response = dev_media_serve(request, "avatar/x.txt")

        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"hello"

    def test_blocks_lookalike_prefix(self, rf, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        target = tmp_path / "privatex" / "x.txt"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"ok")

        request = rf.get("/media/privatex/x.txt")
        response = dev_media_serve(request, "privatex/x.txt")

        assert response.status_code == 200
