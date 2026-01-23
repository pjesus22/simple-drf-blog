class UploadError(Exception):
    """Base exception for upload domain errors"""


class InvalidFileError(UploadError):
    pass


class FileTooLargeError(UploadError):
    pass


class InvalidPurposeError(UploadError):
    pass


class UnsupportedMimeTypeError(UploadError):
    pass
