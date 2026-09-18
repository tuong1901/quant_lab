"""
[PURPOSE]: Experiment Artifact Saver (plots, reports, metrics CSVs).
[DEPENDENCIES]: os.
"""

import os
import json
from typing import Dict, Any

def save_experiment_artifact(artifact_dir: str, name: str, data: Dict[str, Any]) -> str:
    """
    [PURPOSE]: Save experiment JSON artifact to disk.
    [DEPENDENCIES]: json.
    [ARGS]: artifact_dir — output directory; name — artifact filename; data — dict data.
    [RETURNS]: Absolute path to written artifact.
    [SIDE EFFECTS]: Writes file to disk.
    """
    os.makedirs(artifact_dir, exist_ok=True)
    filepath = os.path.join(artifact_dir, f"{name}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return filepath
