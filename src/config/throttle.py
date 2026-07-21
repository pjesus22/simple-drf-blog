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
