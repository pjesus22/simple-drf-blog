from unittest.mock import MagicMock

from apps.metrics.utils import (
    anonymize_ip,
    extract_referer_domain,
    get_best_client_ip,
    is_bot,
    parse_user_agent,
)


class TestIsBot:
    def test_is_bot_detects_bot_ua(self):
        result = is_bot(
            "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P)"
            " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0"
            " Mobile Safari/537.36 (compatible; Googlebot/2.1;"
            " +http://www.google.com/bot.html)"
        )
        assert result is True

    def test_is_bot_empty_string(self):
        result = is_bot("")
        assert result is True


class TestAnonymizeIp:
    def test_anonymize_ip_no_ip_return_none(self):
        result = anonymize_ip()
        assert result is None

    def test_anonymize_ip_ipv4(self):
        result = anonymize_ip("127.0.0.1")
        assert result == "127.0.0.0"

    def test_anonymize_ip_ipv6(self):
        result = anonymize_ip("2001:db8:00f2:06ee:85a3:e004:0dc8:F00A")
        assert result == "2001:db8:00f2:06ee::"

    def test_anonymize_ip_raises_exception_if_invalid_ip(self):
        result = anonymize_ip(123)
        assert result is None


class TestGetBestClientIp:
    def test_get_best_client_ip_returns_zero_placeholder_if_no_ip(self, mocker):
        mocker.patch("apps.metrics.utils.get_client_ip", return_value=(None, False))
        request = MagicMock()
        result = get_best_client_ip(request)
        assert result == "0.0.0.0"

    def test_get_best_client_ip_logs_warning_if_private_ip_not_in_debug(
        self, mocker, settings
    ):
        settings.DEBUG = False
        fake_ip = "192.168.1.100"
        mocker.patch("apps.metrics.utils.get_client_ip", return_value=(fake_ip, False))
        mock_log = mocker.patch("apps.metrics.utils.logger.warning")
        request = MagicMock()

        result = get_best_client_ip(request)

        assert result == "192.168.1.100"
        mock_log.assert_called_once()

    def test_get_best_client_ip_routable_ip(self, mocker):
        mocker.patch("apps.metrics.utils.get_client_ip", return_value=("8.8.8.8", True))
        request = MagicMock()
        result = get_best_client_ip(request)
        assert result == "8.8.8.8"


class TestParseUserAgent:
    def test_parse_user_agent_success(self):
        ua_string = (
            "Opera/9.59 (Android; Linux armv7l; HTC Desire HD A9191) "
            "Presto/2.9.172 Version/11.00"
        )
        response = parse_user_agent(ua_string)

        assert response["browser"] == "Opera"
        assert response["os"] == "Android"
        assert response["device"] == "HTC Desire HD A9191"


class TestExtractRefererDomain:
    def test_extract_referer_domain_success(self):
        result = extract_referer_domain("https://www.google.com")
        assert result == "www.google.com"

    def test_extract_referer_domain_no_domain_return_none(self):
        result = extract_referer_domain(None)
        assert result is None

    def test_extract_referer_domain_raises_exception_if_invalid_domain(self):
        result = extract_referer_domain(123)
        assert result is None
