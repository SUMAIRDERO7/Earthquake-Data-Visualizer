"""
Streamlit demo — Earthquake Data Visualizer "Seismic Monitor".

Layout: a map-first dashboard — a full-width interactive Folium map
dominates the page, with a slim top KPI strip and a collapsible
sidebar for filters, plus an analytics strip below the map. This is
the natural shape for a geospatial tool and a new layout family for
this portfolio (Day 36: SaaS console, Day 37: score console, Day 38:
master-detail, Day 40: split-pane — none of those are map-centric).

Run with: streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.config import (
    COLOR_ACCENT,
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_CARD,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
)
from src.exceptions import EarthquakeVisualizerError
from src.map_builder import build_earthquake_map
from src.visualizer_service import build_report

st.set_page_config(page_title="Earthquake Visualizer", page_icon="🌍", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp {{ background: {COLOR_BACKGROUND}; }}
    h1, h2, h3, h4 {{ color: {COLOR_TEXT_PRIMARY} !important; font-weight: 700; }}
    p, label, .stMarkdown, span {{ color: {COLOR_TEXT_PRIMARY}; }}
    .subtle {{ color: {COLOR_TEXT_SECONDARY} !important; font-size: 13px; }}

    .hero {{
        background: linear-gradient(120deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
        border-radius: 16px; padding: 24px 32px; margin-bottom: 16px;
    }}
    .hero h1, .hero p {{ color: #FFFFFF !important; }}
    .hero .subtitle {{ color: #DCEBFF !important; font-size: 14px; margin-top: 4px; }}

    .kpi-card {{
        background: {COLOR_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 12px;
        padding: 14px 18px; box-shadow: 0 1px 3px rgba(10,37,64,0.06);
    }}
    .kpi-label {{ font-size: 11px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.5px; color: {COLOR_TEXT_SECONDARY} !important; }}
    .kpi-value {{ font-size: 22px; font-weight: 700; color: {COLOR_PRIMARY} !important; margin-top: 2px; }}

    .source-badge {{
        display: inline-block; font-size: 11px; font-weight: 700; padding: 3px 10px;
        border-radius: 10px; margin-bottom: 8px;
    }}
    .source-live {{ background: #D1FAE5; color: #065F46; }}
    .source-cached {{ background: #FEF3C7; color: #92400E; }}

    .zone-card {{
        background: {COLOR_CARD}; border: 1px solid {COLOR_BORDER}; border-left: 4px solid {COLOR_DANGER};
        border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; font-size: 13px;
    }}

    .alert-banner {{
        background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid {COLOR_DANGER};
        border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; font-size: 14px; color: #7F1D1D !important;
    }}
    .alert-banner b {{ color: #7F1D1D !important; }}

    .footer {{
        margin-top: 32px; padding: 16px 0; border-top: 1px solid {COLOR_BORDER};
        color: {COLOR_TEXT_SECONDARY} !important; font-size: 12px; text-align: center;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🌍 Earthquake Data Visualizer — Seismic Monitor</h1>
        <p class="subtitle">Live-first USGS feed with a graceful cached fallback · interactive map · risk zones · frequency trends</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 🎛️ Filters")
min_mag, max_mag = st.sidebar.slider("Magnitude range", 0.0, 8.0, (2.5, 8.0), 0.1)
place_query = st.sidebar.text_input("🔎 Search by place (e.g. 'Alaska', 'Japan')", "")
show_heatmap = st.sidebar.checkbox("Show magnitude heatmap layer", value=True)
show_risk_zones = st.sidebar.checkbox("Show risk zone reference circles", value=True)

try:
    report = build_report(min_magnitude=min_mag, max_magnitude=max_mag, place_query=place_query)
except EarthquakeVisualizerError as exc:
    st.error(f"❌ {exc}")
    st.stop()

source_class = "source-live" if report.source == "live" else "source-cached"
source_text = "🟢 LIVE USGS DATA" if report.source == "live" else "🟡 CACHED SNAPSHOT (see README)"
st.markdown(f'<span class="source-badge {source_class}">{source_text}</span>', unsafe_allow_html=True)

if report.significant_events:
    top = report.significant_events[0]
    st.markdown(
        f'<div class="alert-banner">🚨 <b>{len(report.significant_events)} significant earthquake'
        f'{"s" if len(report.significant_events) != 1 else ""} (M6.0+)</b> in this dataset — most recent: '
        f'<b>M{top.magnitude}</b> near {top.place} on {top.occurred_at.strftime("%Y-%m-%d %H:%M UTC")}</div>',
        unsafe_allow_html=True,
    )

kpi_cols = st.columns(4)
kpi_cols[0].markdown(
    f'<div class="kpi-card"><div class="kpi-label">Earthquakes</div>'
    f'<div class="kpi-value">{len(report.earthquakes)}</div></div>', unsafe_allow_html=True,
)
strongest = max((eq.magnitude for eq in report.earthquakes), default=0.0)
kpi_cols[1].markdown(
    f'<div class="kpi-card"><div class="kpi-label">Strongest</div>'
    f'<div class="kpi-value">M {strongest}</div></div>', unsafe_allow_html=True,
)
avg_mag = round(sum(eq.magnitude for eq in report.earthquakes) / len(report.earthquakes), 2) if report.earthquakes else 0
kpi_cols[2].markdown(
    f'<div class="kpi-card"><div class="kpi-label">Average Magnitude</div>'
    f'<div class="kpi-value">{avg_mag}</div></div>', unsafe_allow_html=True,
)
kpi_cols[3].markdown(
    f'<div class="kpi-card"><div class="kpi-label">Risk Zones</div>'
    f'<div class="kpi-value">{len(report.risk_zones)}</div></div>', unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

if not report.earthquakes:
    st.info("No earthquakes in this magnitude range. Try widening the filter.")
else:
    fmap = build_earthquake_map(report.earthquakes, risk_zones=report.risk_zones if show_risk_zones else None, show_heatmap=show_heatmap)
    st_folium(fmap, width=None, height=520, returned_objects=[])

    st.markdown("<br>", unsafe_allow_html=True)
    tab_frequency, tab_distribution, tab_zones, tab_table = st.tabs(
        ["📈 Frequency Trend", "📊 Magnitude Distribution", "🔥 Top Risk Zones", "📋 Data Table"]
    )

    with tab_frequency:
        if report.daily_frequency:
            df = pd.DataFrame(
                [{"Date": d.day, "Count": d.count, "Avg Magnitude": d.average_magnitude} for d in report.daily_frequency]
            ).set_index("Date")
            st.line_chart(df["Count"])
            st.caption("Daily earthquake count over the available window.")
        else:
            st.info("No data to chart.")

    with tab_distribution:
        dist = report.magnitude_distribution.band_counts
        df = pd.DataFrame({"Band": list(dist.keys()), "Count": list(dist.values())}).set_index("Band")
        st.bar_chart(df)

    with tab_zones:
        if not report.risk_zones:
            st.info("No risk zones meet the minimum event threshold at this filter.")
        else:
            for zone in report.risk_zones[:10]:
                st.markdown(
                    f'<div class="zone-card"><b>({zone.center_lat:.1f}, {zone.center_lon:.1f})</b> — '
                    f'{zone.event_count} events · max M{zone.max_magnitude} · avg M{zone.average_magnitude}</div>',
                    unsafe_allow_html=True,
                )

    with tab_table:
        table_df = pd.DataFrame(
            [
                {
                    "Time (UTC)": eq.occurred_at.strftime("%Y-%m-%d %H:%M"),
                    "Magnitude": eq.magnitude,
                    "Place": eq.place,
                    "Depth (km)": eq.depth_km,
                    "Latitude": eq.latitude,
                    "Longitude": eq.longitude,
                }
                for eq in report.earthquakes
            ]
        )
        st.caption(f"{len(table_df)} earthquake(s) matching the current filters — click a column header to sort.")
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇ Download filtered results (CSV)",
            table_df.to_csv(index=False),
            file_name="earthquakes_filtered.csv",
            mime="text/csv",
        )

st.markdown(
    '<div class="footer">Earthquake Data Visualizer · Day 39 of the 60-Day Python/AI Portfolio Challenge · '
    "Real USGS feed attempted first, every time — see the source badge above and README for details</div>",
    unsafe_allow_html=True,
)
