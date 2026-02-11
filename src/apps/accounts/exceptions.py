class AccountDomainError(Exception):
    """Base exception for account domain errors"""

    default_message = "Account Domain Error"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)


class CannotDemoteLastAdmin(AccountDomainError):
    default_message = "You cannot demote yourself if you are the last administrator."


class InvalidPassword(AccountDomainError):
    default_message = "The provided password is incorrect"
