"""
[PURPOSE]: Exception definitions for the evaluation and basic metrics subsystem.
[DEPENDENCIES]: Inherits from src.core.exceptions.QuantSystemError.
"""

from src.core.exceptions import QuantSystemError


class EvaluationError(QuantSystemError):
    """
    [PURPOSE]: Base exception for all evaluation domain errors.
    [DEPENDENCIES]: Subclass of QuantSystemError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class InvalidEvaluationError(EvaluationError):
    """
    [PURPOSE]: Raised when evaluation inputs or parameters are invalid (e.g., initial capital <= 0).
    [DEPENDENCIES]: Subclass of EvaluationError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass
