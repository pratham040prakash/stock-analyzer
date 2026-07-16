"""Personal desktop broker connection — startup bootstrap and session state."""

from ui.broker.bootstrap import broker_bootstrap, is_broker_configured
from ui.broker.state import BrokerSnapshot, load_broker_snapshot, save_broker_snapshot

__all__ = [
    "BrokerSnapshot",
    "broker_bootstrap",
    "is_broker_configured",
    "load_broker_snapshot",
    "save_broker_snapshot",
]
