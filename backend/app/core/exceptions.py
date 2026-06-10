class LibraryError(Exception):
    """Base error for library domain."""


class NotFoundError(LibraryError):
    pass


class ConflictError(LibraryError):
    pass


class ValidationError(LibraryError):
    pass
