"""Explicit, immutable input-column contracts for market datasets."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping
import logging

import numpy as np
import pandas as pd

from src.data.exceptions import DataValidationError, InvalidDatasetError

logger = logging.getLogger(__name__)
CANONICAL_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class FeatureColumn:
    """One explicitly declared numeric feature; float64 is the supported runtime type."""

    source: str
    type: str

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Require an exact source name and supported feature type.
        [DEPENDENCIES]: ColumnPolicy.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises InvalidDatasetError for invalid declarations.
        """
        if not isinstance(self.source, str) or not self.source.strip() or self.type != "float64":
            raise InvalidDatasetError("Feature requires non-empty source and type: float64.")


@dataclass(frozen=True)
class ColumnPolicy:
    """Canonical-only defaults for Python callers; YAML must explicitly declare a policy."""

    mapping: Mapping[str, str] = field(default_factory=lambda: {name: name for name in CANONICAL_COLUMNS})
    ignore: tuple[str, ...] = ()
    features: Mapping[str, FeatureColumn] = field(default_factory=dict)
    unknown: str = "reject"

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Freeze and validate mappings without guessing aliases or dropping columns.
        [DEPENDENCIES]: FeatureColumn and Dataset.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Freezes copies; raises InvalidDatasetError for ambiguous schema.
        """
        if not isinstance(self.mapping, Mapping) or set(self.mapping) != set(CANONICAL_COLUMNS):
            raise InvalidDatasetError("columns.mapping must declare exactly the six canonical OHLCV names.")
        if not isinstance(self.features, Mapping) or not isinstance(self.ignore, (tuple, list)):
            raise InvalidDatasetError("columns.features must be a mapping and columns.ignore a list.")
        if self.unknown != "reject":
            raise InvalidDatasetError("columns.unknown must be reject.")
        for name, feature in self.features.items():
            if (not isinstance(name, str) or not name.strip() or name != name.strip()
                    or name.lower() in CANONICAL_COLUMNS or not isinstance(feature, FeatureColumn)):
                raise InvalidDatasetError(f"Invalid feature declaration: {name!r}.")
        sources = list(self.mapping.values()) + list(self.ignore) + [f.source for f in self.features.values()]
        if any(not isinstance(name, str) or not name.strip() for name in sources):
            raise InvalidDatasetError("Source column names must be non-empty strings.")
        if len(sources) != len(set(sources)):
            raise InvalidDatasetError("A source column cannot be mapped, ignored or used as a feature more than once.")
        object.__setattr__(self, "mapping", MappingProxyType(dict(self.mapping)))
        object.__setattr__(self, "ignore", tuple(self.ignore))
        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))

    @classmethod
    def from_dict(cls, value: object) -> "ColumnPolicy":
        """
        [PURPOSE]: Parse a required explicit YAML column contract.
        [DEPENDENCIES]: Dataset.from_yaml.
        [ARGS]: value — decoded columns section.
        [RETURNS]: Immutable ColumnPolicy.
        [SIDE EFFECTS]: Raises InvalidDatasetError for missing or invalid keys.
        """
        keys = {"mapping", "ignore", "features", "unknown"}
        if not isinstance(value, dict) or set(value) != keys or not isinstance(value["features"], dict):
            raise InvalidDatasetError("columns requires exactly mapping, ignore, features and unknown.")
        features = {}
        for name, spec in value["features"].items():
            if not isinstance(spec, dict) or set(spec) != {"source", "type"}:
                raise InvalidDatasetError(f"Feature {name!r} requires exactly source and type.")
            features[name] = FeatureColumn(**spec)
        return cls(value["mapping"], value["ignore"], features, value["unknown"])

    def to_dict(self) -> dict:
        """
        [PURPOSE]: Serialize the complete policy for YAML round trips.
        [DEPENDENCIES]: Dataset.to_yaml.
        [ARGS]: None.
        [RETURNS]: Plain dictionary.
        [SIDE EFFECTS]: None.
        """
        return {"mapping": dict(self.mapping), "ignore": list(self.ignore),
                "features": {name: {"source": spec.source, "type": spec.type}
                             for name, spec in sorted(self.features.items())}, "unknown": self.unknown}

    def select(self, frame: pd.DataFrame, dataset_identity: str) -> pd.DataFrame:
        """
        [PURPOSE]: Select only declared columns and validate numeric feature values.
        [DEPENDENCIES]: canonicalize_ohlcv, pandas and numpy.
        [ARGS]: frame — raw input; dataset_identity — diagnostic label.
        [RETURNS]: Copy containing canonical columns and declared numeric features.
        [SIDE EFFECTS]: Logs discarded columns; raises DataValidationError on schema/value errors.
        """
        if frame.empty or frame.columns.has_duplicates:
            raise DataValidationError("Input must be non-empty and contain unique column names.")
        required = set(self.mapping.values()) | {f.source for f in self.features.values()}
        missing = required - set(frame.columns)
        unknown = set(frame.columns) - required - set(self.ignore)
        if missing or unknown:
            raise DataValidationError(f"Column policy mismatch: missing={sorted(map(str, missing))}, unknown={sorted(map(str, unknown))}.")
        ignored = [name for name in self.ignore if name in frame.columns]
        if ignored:
            logger.info("Columns ignored dataset=%s columns=%s", dataset_identity, ignored)
        # Select by position into a fresh index: duplicate source row labels must
        # never multiply candles when continuity repair addresses subsequent rows.
        result = pd.DataFrame({name: frame[self.mapping[name]].to_numpy(copy=True) for name in CANONICAL_COLUMNS})
        for name, spec in sorted(self.features.items()):
            try:
                values = pd.to_numeric(frame[spec.source], errors="raise").to_numpy(dtype=float)
            except (ValueError, TypeError, OverflowError) as error:
                raise DataValidationError(f"Feature {name!r} must contain float64 values.") from error
            if not np.isfinite(values).all():
                raise DataValidationError(f"Feature {name!r} must be finite and non-null.")
            result[name] = values
        return result
