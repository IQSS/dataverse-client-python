class DataverseError(Exception):
    """Base exception class for Dataverse-related error."""
    pass


class UnauthorizedError(DataverseError):
    """Raised if a user provides invalid credentials."""
    pass


class InsufficientMetadataError(DataverseError):
    """Raised if more metadata is required."""
    pass


class MethodNotAllowedError(DataverseError):
    """Raised if the attempted method is not allowed"""
    pass


class NoContainerError(DataverseError):
    """Raised if a dataset attempts to access the server before it is added to a Dataverse"""
    pass


class ConnectionError(DataverseError):
    """Raised when connection fails for an unknown reason"""
    pass


class OperationFailedError(DataverseError):
    """Raised when an operation fails for an unknown reason"""
    pass


class MetadataNotFoundError(DataverseError):
    """Raised when metadata cannot be found for an unknown reason"""
    pass


class UnpublishedDataverseError(DataverseError):
    """Raised when a request requires that a Dataverse first be published"""
    pass


class UnpublishedDatasetError(DataverseError):
    """Raised when a request requires that a dataset first be published"""
    pass