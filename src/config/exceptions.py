"""
Custom exceptions for the Config Layer (`src/config/exceptions.py`).
"""


class ConfigError(Exception):
    """
    [PURPOSE]: Base exception class for all config layer errors.
    [DEPENDENCIES]: Inherits from Python Exception.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class ConfigFileNotFoundError(ConfigError):
    """
    [PURPOSE]: Raised when a required configuration YAML file cannot be located on disk.
    [DEPENDENCIES]: Inherits from ConfigError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class ConfigParseError(ConfigError):
    """
    [PURPOSE]: Raised when a YAML configuration file is malformed or has invalid syntax.
    [DEPENDENCIES]: Inherits from ConfigError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class ConfigValidationError(ConfigError):
    """
    [PURPOSE]: Raised when a configuration value fails type, boundary, or schema validation.
    [DEPENDENCIES]: Inherits from ConfigError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class ConfigReferenceError(ConfigError):
    """
    [PURPOSE]: Raised when a reference to another configuration preset cannot be resolved.
    [DEPENDENCIES]: Inherits from ConfigError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class ConfigCompatibilityError(ConfigError):
    """
    [PURPOSE]: Raised when cross-config compatibility checks fail (e.g., strategy vs execution dataset mismatch).
    [DEPENDENCIES]: Inherits from ConfigError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass
