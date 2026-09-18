"""
[PURPOSE]: Genetic Operators (Crossover & Mutation).
[DEPENDENCIES]: None.
"""

import random
from typing import Dict, Any

def mutate_parameters(params: Dict[str, Any], mutation_rate: float = 0.1) -> Dict[str, Any]:
    """
    [PURPOSE]: Apply random Gaussian/Uniform mutation to numerical parameters.
    [DEPENDENCIES]: random.
    [ARGS]: params — parameter dict; mutation_rate — probability of mutation.
    [RETURNS]: Mutated copy of parameter dict.
    [SIDE EFFECTS]: None.
    """
    mutated = params.copy()
    for k, v in mutated.items():
        if isinstance(v, (int, float)) and random.random() < mutation_rate:
            mutated[k] = v * random.uniform(0.9, 1.1)
    return mutated
