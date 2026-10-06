"""Custom Fibonacci ratio set number one."""

FIBO_1_LEVELS: tuple[float, ...] = (
    0.0, 0.186, 0.322, 0.5, 0.707, 1.0, 1.47, 1.55, 1.95, 2.414,
    2.56, 2.6, 2.64, 3.13, 3.272, 3.414, 4.05, 4.236, 4.272, 4.414, 4.618,
)


def get_fibo_1_levels() -> tuple[float, ...]:
    """
    [PURPOSE]: Return the ordered immutable custom Fibonacci ratio set fibo_1.
    [DEPENDENCIES]: Used by future Fibonacci projection, zone, and strategy consumers.
    [ARGS]: None.
    [RETURNS]: Tuple of 21 custom Fibonacci ratios.
    [SIDE EFFECTS]: None.
    """
    return FIBO_1_LEVELS
