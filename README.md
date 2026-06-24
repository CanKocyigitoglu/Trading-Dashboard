# Trading Risk Dashboard (Prototype)

A lightweight, local prototype of an internal trading-risk dashboard for a
commodities trading business. It demonstrates how a spreadsheet-based workflow
could become a simple internal tool for viewing positions, exposure, P/L,
utilisation and exceptions.

> **Demonstration only.** This is a decision-support prototype, not a
> production trading, pricing, risk-management or order-execution system. All
> sample data is **synthetic**.

## What it shows

The first screen answers four questions:

1. **What is the current exposure?** — Net and gross exposure KPIs.
2. **Where is the largest concentration?** — Exposure-by-desk chart.
3. **What has moved?** — Unrealised P/L KPI and P/L-by-trader chart.
4. **What requires attention?** — Alerts & exceptions table.

It includes 5 KPI cards, a positions table, two charts, filters (desk / trader
/ commodity), a deterministic alerts section, and a visible data timestamp.

## Quick start

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Development commands

```bash
python -m pytest          # business-logic tests (metrics + alerts)
ruff check .              # lint
ruff format --check .     # formatting
```

## Project layout

| Path                 | Responsibility                                             |
| -------------------- | --------------------------------------------------------- |
| `app.py`             | Streamlit presentation only                               |
| `src/config.py`      | Alert thresholds and business labels (single source)      |
| `src/data_loader.py` | CSV loading and typing; preserves missing values          |
| `src/metrics.py`     | KPIs and aggregations (pure, testable)                     |
| `src/alerts.py`      | Deterministic alert rules (pure, testable)                |
| `src/formatting.py`  | Presentation formatting helpers                           |
| `data/positions.csv` | Deterministic synthetic positions                         |
| `tests/`             | pytest suite for the calculation and alert layers         |

Calculations are kept separate from presentation so the financial logic can be
unit tested in isolation.

## Key conventions and assumptions

- **Single currency (USD).** All positions are in USD to avoid inventing FX
  rates. Currency is shown explicitly.
- **Sign convention.** `quantity` is signed: long is positive, short is
  negative. `market_value = quantity × market_price`;
  `unrealised_pl = quantity × (market_price − avg_price)`. A short gains when
  the price falls.
- **Missing vs zero.** Missing inputs are kept as missing (never coerced to
  zero), excluded from totals, and surfaced both as a warning and a
  data-quality alert. Row 14 of the sample data has missing values on purpose
  to demonstrate this.
- **VaR is a supplied input.** Per-position 1-day VaR is read from the data,
  not computed. The portfolio VaR card is a **simple sum** that ignores
  diversification — a prototype figure, not an authoritative portfolio VaR.

## Alerts

All alert rules are plain numeric/temporal comparisons against thresholds in
`src/config.py` — no model or heuristic. Each alert reports its severity, the
affected scope, the observed value, the threshold and a plain-English reason:

| Rule           | Condition                                   | Severity |
| -------------- | ------------------------------------------- | -------- |
| Exposure limit | utilisation ≥ 100% (breach) / ≥ 85% (warn)  | High / Medium |
| P/L            | unrealised P/L < −150,000 USD               | High     |
| VaR            | supplied 1-day VaR > 200,000 USD            | Medium   |
| Data quality   | a required value is missing                 | High     |
| Staleness      | dataset timestamp older than 24h            | High     |

Thresholds are prototype demonstration values and can be adjusted in one place.
