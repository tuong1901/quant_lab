"""
[PURPOSE]: Selection Operators (Tournament & Roulette Wheel Selection).
[DEPENDENCIES]: None.
"""

from typing import List, Any
import random

def tournament_selection(population: List[Any], fitnesses: List[float], tournament_size: int = 3) -> Any:
    """
    [PURPOSE]: Perform Tournament Selection to select fittest parent strategy.
    [DEPENDENCIES]: random.
    """
    selected_indices = random.sample(range(len(population)), tournament_size)
    best_idx = max(selected_indices, key=lambda idx: fitnesses[idx])
    return population[best_idx]
