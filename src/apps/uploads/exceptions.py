class UploadDomainError(Exception):
    """Base exception for upload domain errors"""

    default_message = "Upload Domain Error"

    def __init__(self, message=None):
        super().__init__(message or self.default_message)


class InvalidFileError(UploadDomainError):
    default_message = "Invalid file provided."


class FileTooLargeError(UploadDomainError):
    default_message = "File size exceeds the limit."


class InvalidPurposeError(UploadDomainError):
    default_message = "Invalid upload purpose."


class UnsupportedMimeTypeError(UploadDomainError):
    default_message = "Unsupported MIME type."


class InvalidVisibilityError(UploadDomainError):
    default_message = "Invalid visibility setting."
