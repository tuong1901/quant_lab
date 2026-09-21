"""
Exceptions for the Environment Subsystem.
"""

from src.core.exceptions import QuantSystemError


class EnvironmentError(QuantSystemError):
    """
    [PURPOSE]: Base exception for all environment subsystem errors.
    [DEPENDENCIES]: Inherits from src.core.errors.QuantSystemError.
    [ARGS]: Standard exception args (message, etc.).
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass


class EnvironmentConstructionError(EnvironmentError):
    """
    [PURPOSE]: Raised when an Environment or Registry instance fails to be constructed (e.g. null args, duplicate registry keys).
    [DEPENDENCIES]: Inherits from EnvironmentError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass


class MissingDependencyError(EnvironmentError):
    """
    [PURPOSE]: Raised when a required key or component dependency is missing from the environment or registry.
    [DEPENDENCIES]: Inherits from EnvironmentError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass


class EnvironmentValidationError(EnvironmentError):
    """
    [PURPOSE]: Raised when validation on an Environment state or runtime composition fails.
    [DEPENDENCIES]: Inherits from EnvironmentError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass
