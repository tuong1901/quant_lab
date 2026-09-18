"""
[PURPOSE]: Configuration parser for YAML / JSON settings files.
[DEPENDENCIES]: None.
"""

import yaml
from typing import Dict, Any

def load_yaml_config(filepath: str) -> Dict[str, Any]:
    """
    [PURPOSE]: Load and parse YAML configuration file safely.
    [DEPENDENCIES]: PyYAML.
    [ARGS]: filepath — path to YAML file.
    [RETURNS]: Dictionary of parsed configuration keys.
    [SIDE EFFECTS]: None (pure file read).
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
