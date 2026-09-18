"""
[PURPOSE]: Abstract Gateway interface for live broker integration.
[DEPENDENCIES]: None.
"""

from typing import Protocol, Any

class BrokerGateway(Protocol):
    """Abstract interface for live brokers."""
    def send_order(self, order: Any) -> Any:
        ...
