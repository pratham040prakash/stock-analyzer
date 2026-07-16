"""Invisible Lightweight Charts embed — ghost depth only."""

from __future__ import annotations

import json

import streamlit.components.v1 as components

from ui.components.proof_models import CandleBar, StructureProof


def _bars_json(candles: tuple[CandleBar, ...]) -> str:
    payload = []
    for bar in candles:
        payload.append(
            {
                "time": bar.time[:10] if len(bar.time) >= 10 else bar.time,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
            }
        )
    return json.dumps(payload)


def render_proof_lwc(proof: StructureProof, *, height: int = 200) -> None:
    """Render raw candles via LW Charts — only when user opts in."""
    if not proof.candles:
        return
    bars = _bars_json(proof.candles)
    html_doc = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
  <style>
    html, body {{ margin: 0; padding: 0; background: #1C1C1E; }}
    #chart {{ width: 100%; height: {height}px; }}
  </style>
</head>
<body>
  <div id="chart"></div>
  <script>
    const bars = {bars};
    const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
      layout: {{ background: {{ color: '#1C1C1E' }}, textColor: 'rgba(245,245,247,0.45)' }},
      grid: {{ vertLines: {{ visible: false }}, horzLines: {{ color: '#2C2C2E' }} }},
      rightPriceScale: {{ borderVisible: false }},
      timeScale: {{ borderVisible: false }},
      crosshair: {{ vertLine: {{ visible: false }}, horzLine: {{ visible: false }} }},
    }});
    const series = chart.addCandlestickSeries({{
      upColor: '#00E676', downColor: '#FF6B6B', borderVisible: false,
      wickUpColor: '#00E676', wickDownColor: '#FF6B6B',
    }});
    const mapped = bars.map((b, i) => ({{
      time: i + 1,
      open: b.open, high: b.high, low: b.low, close: b.close,
    }}));
    series.setData(mapped);
    chart.timeScale().fitContent();
  </script>
</body>
</html>
"""
    components.html(html_doc, height=height + 8, scrolling=False)
