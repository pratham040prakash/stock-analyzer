"""Broker session boundary — OAuth, credentials, and connection lifecycle.

Future commits will wire ``BrokerSessionService`` as the single session authority
for the Experience layer (``app.py``, broker wizards, connect gates). See
``ETS-002.1`` and ``APEX-005`` §31 (Broker Abstraction).
"""

from analyzer.broker.session import BrokerSessionService

__all__ = ["BrokerSessionService"]
