from rest_framework.throttling import (
    AnonRateThrottle,
    UserRateThrottle,
)


class AnonReadThrottle(AnonRateThrottle):
    scope = "anon_read"


class UserReadThrottle(UserRateThrottle):
    scope = "user_read"


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class TokenThrottle(UserRateThrottle):
    scope = "token"


class WriteThrottle(UserRateThrottle):
    scope = "write"


class UploadHourThrottle(UserRateThrottle):
    scope = "upload_hour"


class UploadBurstThrottle(UserRateThrottle):
    scope = "upload_burst"


class PasswordChangeThrottle(UserRateThrottle):
    scope = "password_change"


class ReadWriteThrottleMixin:
    read_actions = ("list", "retrieve")
    upload_actions = ()

    def get_throttles(self):
        request = self.request
        method = self.request.method

        if method in ("OPTIONS", "HEAD"):
            return []
        if method == "POST" and self.action in self.upload_actions:
            return [UploadHourThrottle(), UploadBurstThrottle()]
        if method == "GET" and self.action in self.read_actions:
            if request.user and request.user.is_authenticated:
                return [UserReadThrottle()]
            return [AnonReadThrottle()]
        return [WriteThrottle()]
