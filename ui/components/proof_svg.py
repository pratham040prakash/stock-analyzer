"""SVG annotation renderer for Proof Canvas."""

from __future__ import annotations

import html

from ui.components.proof_models import StructureProof, ZoneAnnotation

_W = 358
_H = 280

_ZONE_FILL = {
    "danger": "rgba(255,107,107,0.28)",
    "supply": "rgba(255,107,107,0.18)",
    "demand": "rgba(0,230,118,0.08)",
    "reward": "rgba(0,230,118,0.12)",
    "risk": "rgba(255,138,128,0.15)",
    "uncertainty": "rgba(255,193,7,0.22)",
    "invalidation": "rgba(255,138,128,0.1)",
    "fossil_seen": "rgba(255,193,7,0.18)",
    "fossil_outcome": "rgba(255,107,107,0.12)",
    "fossil_learn": "rgba(100,181,246,0.1)",
}

_ZONE_TEXT = {
    "danger": "rgba(255,107,107,0.95)",
    "supply": "rgba(255,107,107,0.9)",
    "demand": "rgba(0,230,118,0.85)",
    "reward": "rgba(0,230,118,0.95)",
    "risk": "rgba(255,138,128,0.85)",
    "uncertainty": "rgba(255,193,7,0.95)",
    "invalidation": "rgba(255,138,128,0.85)",
    "fossil_seen": "rgba(255,193,7,0.9)",
    "fossil_outcome": "rgba(255,107,107,0.75)",
    "fossil_learn": "rgba(100,181,246,0.9)",
}


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _y(price: float, proof: StructureProof) -> float:
    span = max(proof.price_max - proof.price_min, 1e-6)
    return (_H - 24) * (proof.price_max - price) / span + 12


def _candle_svg(proof: StructureProof) -> str:
    if not proof.candles or proof.chart_opacity < 0.2:
        return ""
    n = len(proof.candles)
    if n < 2:
        return ""
    bar_w = max(2, min(6, (_W - 40) / n))
    parts: list[str] = []
    opacity = 0.35 if proof.blur_candles else 0.55
    filt = ' filter="url(#pc-blur)"' if proof.blur_candles else ""
    for i, bar in enumerate(proof.candles):
        x = 20 + i * ((_W - 40) / max(n - 1, 1))
        y_high = _y(bar.high, proof)
        y_low = _y(bar.low, proof)
        y_open = _y(bar.open, proof)
        y_close = _y(bar.close, proof)
        top = min(y_open, y_close)
        h = max(abs(y_close - y_open), 1)
        color = "#888" if bar.close >= bar.open else "#666"
        parts.append(
            f'<line x1="{x:.1f}" y1="{y_high:.1f}" x2="{x:.1f}" y2="{y_low:.1f}" '
            f'stroke="{color}" stroke-width="1" opacity="{opacity}"/>'
        )
        parts.append(
            f'<rect x="{x - bar_w/2:.1f}" y="{top:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
            f'fill="{color}" opacity="{opacity}"/>'
        )
    return f"<g{filt}>{''.join(parts)}</g>"


def _zone_svg(zone: ZoneAnnotation, proof: StructureProof) -> str:
    y1 = _y(zone.price_top, proof)
    y2 = _y(zone.price_bottom, proof)
    top = min(y1, y2)
    height = max(abs(y2 - y1), 4)
    fill = _ZONE_FILL.get(zone.kind, "rgba(161,161,166,0.1)")
    color = _ZONE_TEXT.get(zone.kind, "rgba(245,245,247,0.7)")
    label = _esc(zone.human_label[:72])
    return (
        f'<rect x="0" y="{top:.1f}" width="{_W}" height="{height:.1f}" fill="{fill}"/>'
        f'<text x="16" y="{top + min(20, height * 0.45):.1f}" fill="{color}" '
        f'font-family="Inter,sans-serif" font-size="11" font-weight="500">{label}</text>'
    )


def _path_svg(proof: StructureProof) -> str:
    if not proof.paths:
        return ""
    parts: list[str] = []
    for path in proof.paths:
        if len(path.points) < 2:
            continue
        coords = []
        n = max(len(proof.candles), 10)
        for price, frac in path.points:
            x = 20 + frac * (_W - 40)
            y = _y(price, proof)
            coords.append(f"{x:.1f},{y:.1f}")
        stroke = "#00E676" if path.kind == "expected" else "rgba(255,107,107,0.5)"
        dash = "" if path.kind == "expected" else ' stroke-dasharray="5 4"'
        parts.append(
            f'<polyline points="{" ".join(coords)}" fill="none" stroke="{stroke}" '
            f'stroke-width="2.5" stroke-opacity="0.75"{dash}/>'
        )
    return "".join(parts)


def _markers_svg(proof: StructureProof) -> str:
    m = proof.markers
    parts: list[str] = []
    items: list[tuple[str, float | None, str, str]] = [
        ("Entry", m.entry, "#00E676", "▲"),
        ("Stop", m.stop, "#FF8A80", "■"),
        ("Target", m.target, "#00E676", "◆"),
    ]
    x_label = 16
    for name, price, color, glyph in items:
        if price is None or price <= 0:
            continue
        y = _y(price, proof)
        parts.append(
            f'<line x1="0" y1="{y:.1f}" x2="{_W}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-width="1" opacity="0.45"/>'
        )
        parts.append(
            f'<text x="{x_label}" y="{y - 4:.1f}" fill="{color}" font-family="Inter,sans-serif" '
            f'font-size="10" font-weight="600">{glyph} {name} ₹{price:,.0f}</text>'
        )
        x_label += 100
    if m.current and m.current > 0:
        y = _y(m.current, proof)
        x = _W * 0.72
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#F5F5F7"/>')
        parts.append(
            f'<text x="{x + 8:.1f}" y="{y + 4:.1f}" fill="#F5F5F7" font-family="Inter,sans-serif" '
            f'font-size="10" font-weight="600">● Now ₹{m.current:,.0f}</text>'
        )
    return "".join(parts)


def render_proof_svg(proof: StructureProof) -> str:
    """Return HTML snippet: proof frame + inline SVG annotations."""
    opacity = proof.chart_opacity
    zones_html = "".join(_zone_svg(z, proof) for z in proof.zones[:6])
    candles = _candle_svg(proof)
    paths = _path_svg(proof)
    markers = _markers_svg(proof)
    blur_def = (
        '<defs><filter id="pc-blur" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur stdDeviation="2.5"/></filter></defs>'
        if proof.blur_candles
        else "<defs></defs>"
    )
    rest_overlay = ""
    if proof.verdict_state == "rest":
        rest_overlay = (
            f'<text x="{_W/2}" y="{_H/2}" text-anchor="middle" fill="rgba(161,161,166,0.85)" '
            f'font-family="Inter,sans-serif" font-size="15" font-weight="500">'
            f"Proof refreshes at market open</text>"
        )
    svg = (
        f'<svg class="proof-svg" viewBox="0 0 {_W} {_H}" xmlns="http://www.w3.org/2000/svg" '
        f'aria-label="Proof annotations for { _esc(proof.symbol) }" '
        f'style="opacity:{opacity:.2f}">'
        f"{blur_def}"
        f'<rect width="{_W}" height="{_H}" fill="#1C1C1E"/>'
        f"{candles}"
        f"{zones_html}"
        f"{paths}"
        f"{markers}"
        f"{rest_overlay}"
        f"</svg>"
    )
    return (
        f'<div class="proof-frame" data-proof="{_esc(proof.verdict_state)}">'
        f"{svg}</div>"
    )
