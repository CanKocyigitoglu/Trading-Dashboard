"""Trading-risk dashboard prototype (Streamlit presentation layer).

This file contains presentation logic only. All financial calculations and
alert rules live in the ``src`` package so they can be unit tested in
isolation. Sample data is synthetic and for demonstration only.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src import alerts, config, data_loader, formatting, metrics

st.set_page_config(page_title="Trading Risk Dashboard (Prototype)", layout="wide")


@st.cache_data
def _load() -> pd.DataFrame:
    return data_loader.load_positions()


def _format_positions_table(enriched: pd.DataFrame) -> pd.DataFrame:
    """Build a display table with business labels and presentation formatting."""
    display = pd.DataFrame()
    display[config.COLUMN_LABELS["desk"]] = enriched["desk"]
    display[config.COLUMN_LABELS["trader"]] = enriched["trader"]
    display[config.COLUMN_LABELS["instrument"]] = enriched["instrument"]
    display[config.COLUMN_LABELS["commodity"]] = enriched["commodity"]
    display[config.COLUMN_LABELS["side"]] = enriched["side"]
    display[config.COLUMN_LABELS["quantity"]] = enriched["quantity"].map(
        lambda v: formatting.number(v)
    )
    display[config.COLUMN_LABELS["unit"]] = enriched["unit"]
    display[config.COLUMN_LABELS["avg_price"]] = enriched["avg_price"].map(
        lambda v: formatting.number(v, decimals=2)
    )
    display[config.COLUMN_LABELS["market_price"]] = enriched["market_price"].map(
        lambda v: formatting.number(v, decimals=2)
    )
    display[config.COLUMN_LABELS["currency"]] = enriched["currency"]
    display[config.COLUMN_LABELS["market_value"]] = enriched["market_value"].map(
        lambda v: formatting.money(v)
    )
    display[config.COLUMN_LABELS["unrealised_pl"]] = enriched["unrealised_pl"].map(
        lambda v: formatting.money(v)
    )
    display[config.COLUMN_LABELS["var_1d"]] = enriched["var_1d"].map(lambda v: formatting.money(v))
    display[config.COLUMN_LABELS["utilisation_pct"]] = enriched["utilisation_pct"].map(
        lambda v: formatting.percent(v)
    )
    display[config.COLUMN_LABELS["exposure_limit"]] = enriched["exposure_limit"].map(
        lambda v: formatting.money(v)
    )
    return display


def _sidebar_filters(positions: pd.DataFrame) -> pd.DataFrame:
    """Render multi-select filters and return the filtered positions."""
    st.sidebar.header("Filters")
    filtered = positions
    for column, label in (("desk", "Desk"), ("trader", "Trader"), ("commodity", "Commodity")):
        options = sorted(positions[column].dropna().unique())
        chosen = st.sidebar.multiselect(label, options, default=options)
        filtered = filtered[filtered[column].isin(chosen)]
    return filtered


def _render_kpis(kpis: metrics.PortfolioKPIs, open_exceptions: int) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Net Exposure",
        formatting.money(kpis.net_exposure),
        help="Sum of signed market values (long minus short).",
    )
    c2.metric(
        "Gross Exposure",
        formatting.money(kpis.gross_exposure),
        help="Sum of absolute market values (total capital at risk).",
    )
    c3.metric("Unrealised P/L", formatting.money(kpis.total_unrealised_pl))
    c4.metric(
        "1-Day VaR (prototype)",
        formatting.money(kpis.total_var_1d),
        help=(
            "Simple sum of supplied per-position 1-day VaR. Prototype figure "
            "only: it ignores diversification and is not an authoritative "
            "portfolio VaR."
        ),
    )
    c5.metric("Open Exceptions", formatting.number(open_exceptions))


def _render_charts(enriched: pd.DataFrame) -> None:
    left, right = st.columns(2)

    with left:
        st.subheader("Exposure concentration by desk")
        by_desk = metrics.aggregate_exposure(enriched, "desk")
        fig = px.bar(
            by_desk,
            x="gross_exposure",
            y="desk",
            orientation="h",
            labels={"gross_exposure": f"Gross Exposure ({config.REPORTING_CURRENCY})", "desk": ""},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=0, r=0, t=10))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Unrealised P/L by trader")
        by_trader = metrics.aggregate_pl(enriched, "trader")
        fig = px.bar(
            by_trader,
            x="trader",
            y="unrealised_pl",
            labels={"unrealised_pl": f"Unrealised P/L ({config.REPORTING_CURRENCY})", "trader": ""},
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10))
        st.plotly_chart(fig, use_container_width=True)


def _render_alerts(alert_frame: pd.DataFrame) -> None:
    st.subheader("Alerts & exceptions")
    if alert_frame.empty:
        st.success("No alerts triggered for the current selection.")
        return
    st.caption(
        "Severity is also shown as text (High / Medium), not by colour alone. "
        "Each alert lists the affected scope, the observed value, the threshold "
        "and the reason it triggered."
    )
    st.dataframe(alert_frame, use_container_width=True, hide_index=True)


def main() -> None:
    st.title("Trading Risk Dashboard")
    st.caption(
        "Internal prototype for commodities trading risk. "
        "**Synthetic demonstration data — not real positions.**"
    )

    positions = _load()
    dataset_ts = data_loader.dataset_timestamp(positions)

    filtered = _sidebar_filters(positions)

    ts_text = (
        dataset_ts.strftime("%Y-%m-%d %H:%M") if dataset_ts is not None else formatting.MISSING
    )
    st.caption(f"Data as of: **{ts_text}**  ·  Reporting currency: **{config.REPORTING_CURRENCY}**")

    if filtered.empty:
        st.warning("No positions match the current filters. Adjust the filters to see data.")
        return

    enriched = metrics.enrich_positions(filtered)
    kpis = metrics.portfolio_kpis(enriched)

    now = pd.Timestamp.now()
    triggered = alerts.evaluate_alerts(enriched, now=now, dataset_timestamp=dataset_ts)

    if kpis.incomplete_position_count:
        st.warning(
            f"{kpis.incomplete_position_count} position(s) are missing a required value "
            "and are excluded from value-based totals. They are not counted as zero."
        )

    _render_kpis(kpis, open_exceptions=len(triggered))
    st.divider()
    _render_charts(enriched)
    st.divider()

    st.subheader("Positions")
    st.dataframe(_format_positions_table(enriched), use_container_width=True, hide_index=True)
    st.divider()

    _render_alerts(alerts.alerts_to_frame(triggered))


if __name__ == "__main__":
    main()
