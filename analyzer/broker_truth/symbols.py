"""Shared symbol normalization for broker truth."""

from __future__ import annotations


def normalize_equity_symbol(symbol: str) -> str:
    """NSE tradingsymbol or Yahoo-style → base symbol (e.g. RELIANCE)."""
    sym = symbol.upper().strip()
    for suffix in (".NS", ".BO"):
        if sym.endswith(suffix):
            sym = sym[: -len(suffix)]
    for suffix in ("-EQ", "-BE", "-BL", "-BZ"):
        if sym.endswith(suffix):
            sym = sym[: -len(suffix)]
    return sym
