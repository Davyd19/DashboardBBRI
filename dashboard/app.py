from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "BBRI_logo.png"
sys.path.append(str(PROJECT_ROOT / "etl"))

from pipeline import (  # noqa: E402
    RAW_PATH,
    ValidationReport,
    build_data_mart,
    run_pipeline,
    summarize_metrics,
    transform_dataframe,
    validate_dataframe,
)

try:  # noqa: E402
    from database import load_data_mart, read_fact_data
except Exception:  # pragma: no cover
    load_data_mart = None
    read_fact_data = None


st.set_page_config(
    page_title="BBRI Executive Signal Dashboard",
    page_icon="BBRI",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def logo_base64() -> str:
    return base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")


def inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bbri:#00529c;
            --navy:#07396f;
            --sky:#f2f8ff;
            --ink:#111827;
            --muted:#667085;
            --line:#d8e5f3;
            --soft:#ffffff;
            --green:#059669;
            --amber:#d97706;
            --red:#dc2626;
            --orange:#f37021;
        }
        .stApp { background:#f5f9fe; color:var(--ink); }
        .block-container { padding-top:1rem; padding-bottom:2rem; max-width:1460px; }
        [data-testid="stSidebar"] {
            background:#ffffff;
            border-right:1px solid var(--line);
            min-width:250px;
            max-width:250px;
        }
        [data-testid="stSidebar"] * { color:var(--ink) !important; }
        [data-testid="stSidebar"] img { width:54px !important; border-radius:12px; }
        [data-testid="stSidebar"] .stRadio label {
            background:#f8fbff;
            border:1px solid var(--line);
            border-radius:10px;
            padding:7px 10px;
            margin:3px 0;
        }
        [data-testid="stSidebar"] .stButton button {
            border:1px solid var(--line);
            background:#ffffff;
            border-radius:9px;
        }
        .hero {
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:14px;
            background:linear-gradient(135deg,#062f5f 0%,#00529c 64%,#1878c7 100%);
            color:#ffffff;
            border-radius:14px;
            padding:12px 18px;
            margin-bottom:14px;
            box-shadow:0 10px 24px rgba(0,82,156,.16);
        }
        .hero-left { display:flex; align-items:center; gap:14px; min-width:0; }
        .hero-logo {
            width:48px;
            height:48px;
            border-radius:12px;
            border:1px solid rgba(255,255,255,.35);
            flex:0 0 auto;
        }
        .hero h1 { margin:0; font-size:23px; line-height:1.08; letter-spacing:0; }
        .hero p { margin:4px 0 0; color:#d8edff; font-size:13px; }
        .hero-pill {
            background:rgba(255,255,255,.14);
            border:1px solid rgba(255,255,255,.28);
            border-radius:999px;
            padding:8px 12px;
            font-size:12px;
            white-space:nowrap;
        }
        .signal-strip {
            display:grid;
            grid-template-columns: 170px 1fr 230px;
            gap:14px;
            align-items:center;
            background:#ffffff;
            border:1px solid var(--line);
            border-radius:14px;
            padding:12px 16px;
            margin:8px 0 14px;
            box-shadow:0 8px 20px rgba(16,24,40,.05);
        }
        .status-badge {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:100%;
            border-radius:999px;
            padding:10px 12px;
            font-size:16px;
            font-weight:850;
            color:#ffffff;
        }
        .status-normal { background:var(--green); }
        .status-watch { background:var(--amber); }
        .status-pressure { background:var(--red); }
        .signal-text b { color:var(--ink); }
        .signal-text { color:var(--muted); font-size:14px; line-height:1.5; }
        .watch-box {
            border:1px solid var(--line);
            background:#f8fbff;
            border-radius:12px;
            padding:10px 12px;
        }
        .watch-box span { display:block; color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; }
        .watch-box b { display:block; color:var(--ink); font-size:15px; margin-top:3px; }
        .kpi-card {
            background:#ffffff;
            border:1px solid var(--line);
            border-radius:12px;
            padding:12px 13px;
            min-height:94px;
            box-shadow:0 8px 20px rgba(16,24,40,.05);
            position:relative;
            overflow:hidden;
        }
        .kpi-card:before {
            content:"";
            position:absolute;
            top:0;
            left:0;
            right:0;
            height:4px;
            background:var(--bbri);
        }
        .kpi-card.good:before { background:var(--green); }
        .kpi-card.warn:before { background:var(--amber); }
        .kpi-card.danger:before { background:var(--red); }
        .kpi-label {
            color:var(--muted);
            font-size:10px;
            font-weight:850;
            text-transform:uppercase;
            margin-bottom:8px;
        }
        .kpi-value {
            color:var(--ink);
            font-size:20px;
            font-weight:850;
            line-height:1.1;
            overflow-wrap:anywhere;
        }
        .kpi-note { color:var(--muted); font-size:12px; margin-top:8px; line-height:1.3; }
        .section-title {
            color:var(--ink);
            font-size:19px;
            font-weight:850;
            margin:19px 0 4px;
        }
        .section-subtitle {
            color:var(--muted);
            font-size:13px;
            margin-bottom:10px;
        }
        .signal-tile {
            background:#ffffff;
            border:1px solid var(--line);
            border-radius:12px;
            padding:12px 13px;
            min-height:98px;
            box-shadow:0 8px 20px rgba(16,24,40,.04);
            position:relative;
            overflow:hidden;
        }
        .signal-tile:before {
            content:"";
            position:absolute;
            top:0;
            left:0;
            right:0;
            height:5px;
            background:var(--bbri);
        }
        .signal-tile.good:before { background:var(--green); }
        .signal-tile.warn:before { background:var(--amber); }
        .signal-tile.danger:before { background:var(--red); }
        .signal-name {
            color:var(--muted);
            font-size:10px;
            font-weight:850;
            text-transform:uppercase;
            margin-bottom:10px;
        }
        .signal-state {
            color:var(--ink);
            font-size:17px;
            font-weight:850;
            line-height:1.15;
        }
        .signal-measure {
            color:var(--muted);
            font-size:12px;
            margin-top:8px;
        }
        .legend-row {
            display:flex;
            flex-wrap:wrap;
            gap:10px;
            align-items:center;
            margin:4px 0 12px;
            color:var(--muted);
            font-size:12px;
        }
        .legend-dot {
            width:10px;
            height:10px;
            border-radius:999px;
            display:inline-block;
            margin-right:5px;
        }
        .dot-good { background:var(--green); }
        .dot-warn { background:var(--amber); }
        .dot-danger { background:var(--red); }
        .chart-card {
            background:#ffffff;
            border:1px solid var(--line);
            border-radius:12px;
            padding:12px 14px 6px;
            box-shadow:0 8px 20px rgba(16,24,40,.04);
            margin-bottom:12px;
        }
        .chart-title { color:var(--ink); font-size:14px; font-weight:850; margin-bottom:2px; }
        .chart-note { color:var(--muted); font-size:12px; margin-bottom:8px; }
        .status-chip {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            border-radius:999px;
            padding:6px 10px;
            color:#ffffff !important;
            font-size:12px;
            font-weight:850;
            min-width:76px;
        }
        .validation-card .status-chip { color:#ffffff !important; }
        .chip-valid { background:var(--green); }
        .chip-warning { background:var(--amber); }
        .chip-error { background:var(--red); }
        .validation-card {
            background:#ffffff;
            border:1px solid var(--line);
            border-radius:12px;
            padding:13px 14px;
            min-height:112px;
            box-shadow:0 8px 20px rgba(16,24,40,.04);
        }
        .validation-card b {
            display:block;
            color:var(--ink);
            font-size:15px;
            margin:8px 0 4px;
        }
        .validation-card span {
            color:var(--muted);
            font-size:12px;
            line-height:1.35;
        }
        .callout {
            background:#ffffff;
            border:1px solid var(--line);
            border-left:6px solid var(--bbri);
            border-radius:12px;
            padding:14px 16px;
            box-shadow:0 8px 20px rgba(16,24,40,.04);
            min-height:120px;
        }
        .callout.warning { border-left-color:var(--amber); background:#fffaf0; }
        .callout.error { border-left-color:var(--red); background:#fff5f5; }
        .callout.success { border-left-color:var(--green); background:#f0fdf4; }
        .callout h4 { margin:0 0 8px; color:var(--ink); font-size:16px; }
        .callout ul { margin:0; padding-left:18px; color:var(--ink); font-size:13px; line-height:1.45; }
        .callout p { margin:0; color:var(--ink); font-size:13px; line-height:1.45; }
        .etl-flow-card {
            background:#ffffff;
            border:1px solid var(--line);
            border-radius:14px;
            padding:16px;
            box-shadow:0 10px 24px rgba(16,24,40,.05);
        }
        .etl-flow-layout {
            display:grid;
            grid-template-columns:minmax(0,1fr) 330px;
            gap:16px;
            align-items:stretch;
        }
        .etl-flow-title {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:12px;
            margin-bottom:12px;
        }
        .etl-flow-title h3 { margin:0; color:var(--ink); font-size:18px; }
        .etl-flow-title span { color:var(--muted); font-size:12px; }
        .etl-flow-grid {
            display:grid;
            grid-template-columns:1.1fr 34px 1fr 34px 1fr 34px 1fr 34px 1fr 34px 1fr;
            gap:8px;
            align-items:center;
        }
        .etl-node {
            border:1px solid var(--line);
            border-radius:12px;
            padding:12px;
            min-height:128px;
            background:#f8fbff;
        }
        .etl-node.source { background:#f8fbff; }
        .etl-node.extract { background:#eef6ff; border-color:#afd5ff; }
        .etl-node.validate { background:#f0fdf4; border-color:#bbf7d0; }
        .etl-node.transform { background:#fff8e8; border-color:#fed7aa; }
        .etl-node.load { background:#f0fdf4; border-color:#bbf7d0; }
        .etl-node.dashboard-node { background:#eef6ff; border-color:#afd5ff; }
        .etl-node-icon {
            width:38px;
            height:38px;
            border-radius:10px;
            display:flex;
            align-items:center;
            justify-content:center;
            background:#ffffff;
            border:1px solid var(--line);
            color:var(--bbri);
            font-weight:850;
            font-size:12px;
            margin-bottom:8px;
        }
        .etl-node b { display:block; color:var(--ink); font-size:14px; margin-bottom:6px; }
        .etl-node span { display:block; color:var(--muted); font-size:12px; line-height:1.35; }
        .etl-node small { display:block; color:var(--ink); font-size:12px; font-weight:750; margin-top:8px; }
        .etl-arrow {
            display:flex;
            justify-content:center;
            align-items:center;
            color:var(--bbri);
            font-size:24px;
            font-weight:850;
        }
        .etl-mini-pipeline {
            margin-top:14px;
            border:1px dashed #b8cce2;
            background:#fbfdff;
            border-radius:12px;
            padding:10px 12px;
            display:flex;
            align-items:center;
            justify-content:center;
            flex-wrap:wrap;
            gap:10px;
            color:var(--muted);
            font-size:12px;
        }
        .etl-mini-step {
            display:inline-flex;
            align-items:center;
            gap:6px;
            color:var(--ink);
            font-weight:750;
        }
        .etl-mini-icon {
            width:24px;
            height:24px;
            border-radius:8px;
            background:#e7f2ff;
            color:var(--bbri);
            display:inline-flex;
            align-items:center;
            justify-content:center;
            font-size:10px;
            font-weight:850;
        }
        .etl-code-panel {
            border:1px solid var(--line);
            border-radius:12px;
            background:#0f172a;
            color:#dbeafe;
            padding:14px;
            min-height:100%;
        }
        .etl-code-panel h4 { margin:0 0 10px; color:#ffffff; font-size:15px; }
        .etl-code-panel pre {
            margin:0;
            white-space:pre-wrap;
            font-size:12px;
            line-height:1.55;
            font-family:Consolas, "Courier New", monospace;
        }
        .etl-code-panel .fn { color:#93c5fd; }
        .etl-code-panel .comment { color:#a7f3d0; }
        .mart-card {
            background:#ffffff;
            border:1px solid var(--line);
            border-radius:12px;
            padding:13px 14px;
            box-shadow:0 8px 20px rgba(16,24,40,.04);
        }
        .mart-card b { display:block; color:var(--ink); font-size:15px; margin-bottom:8px; }
        .mart-card span { color:var(--muted); font-size:13px; }
        .active-range {
            background:#f2f8ff;
            border:1px solid var(--line);
            border-radius:10px;
            padding:8px 10px;
            color:var(--ink);
            font-size:12px;
            margin-top:8px;
        }
        div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; }
        @media (max-width: 1100px) {
            .signal-strip { grid-template-columns:1fr; }
            .hero { align-items:flex-start; flex-direction:column; }
            .etl-flow-layout { grid-template-columns:1fr; }
            .etl-flow-grid { grid-template-columns:1fr; }
            .etl-arrow { transform:rotate(90deg); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def compact_number(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    value = float(value)
    if abs(value) >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:,.2f}T"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.1f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.1f}M"
    return f"{value:,.0f}"


def pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value * 100:,.2f}%"


def variant_for_status(status: str) -> str:
    status = status.lower()
    if status == "pressure":
        return "danger"
    if status == "watch":
        return "warn"
    return "good"


def variant_for_negative(value: float | None, warn: float = 0, danger: float | None = None) -> str:
    if value is None or pd.isna(value):
        return ""
    if danger is not None and value <= danger:
        return "danger"
    if value < warn:
        return "warn"
    return "good"


def short_status_reason(s: dict[str, Any]) -> str:
    reasons: list[str] = []
    if s["latest_drawdown"] <= -0.20:
        reasons.append("drawdown pressure")
    elif s["latest_drawdown"] <= -0.10:
        reasons.append("drawdown watch")
    if s["return_20d"] < 0:
        reasons.append("return 20D negatif")
    if s["rolling_net_foreign_20d"] < 0:
        reasons.append("foreign flow negatif")
    return ", ".join(reasons[:2]) if reasons else "indikator stabil"


def kpi_card(label: str, value: str, note: str, variant: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card {variant}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_chip(status: str) -> str:
    normalized = status.lower()
    css_class = "chip-error" if normalized == "error" else "chip-warning" if normalized == "warning" else "chip-valid"
    return f'<span class="status-chip {css_class}">{status}</span>'


def validation_card(title: str, status: str, detail: str, variant: str = "VALID") -> None:
    st.markdown(
        f"""
        <div class="validation-card">
            {status_chip(variant)}
            <b>{title}</b>
            <span>{detail}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def warning_callout(title: str, items: list[str], variant: str) -> None:
    if items:
        rows = "".join(f"<li>{item}</li>" for item in items)
        body = f"<ul>{rows}</ul>"
    else:
        body = "<p>Tidak ada catatan pada kategori ini.</p>"
    st.markdown(
        f"""
        <div class="callout {variant}">
            <h4>{title}</h4>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def etl_process_flow(report, mart: dict[str, pd.DataFrame]) -> None:
    mart_count = len(mart)
    period_text = f"{report.min_date or '-'} sampai {report.max_date or '-'}"
    node_html = f"""
    <div class="etl-node source">
        <div class="etl-node-icon">CSV</div>
        <b>Data Sources</b>
        <span>BBRI.csv atau CSV baru dari upload user.</span>
        <small>{report.row_count:,} rows | {period_text}</small>
    </div>
    <div class="etl-arrow">-&gt;</div>
    <div class="etl-node extract">
        <div class="etl-node-icon">EXT</div>
        <b>Extract</b>
        <span>Membaca file sumber dan menyiapkan dataframe raw.</span>
        <small>read_csv()</small>
    </div>
    <div class="etl-arrow">-&gt;</div>
    <div class="etl-node validate">
        <div class="etl-node-icon">CHK</div>
        <b>Validate</b>
        <span>Cek schema, ticker, date, duplicate, Open = 0, OHLC, dan outlier.</span>
        <small>Status: {report.status}</small>
    </div>
    <div class="etl-arrow">-&gt;</div>
    <div class="etl-node transform">
        <div class="etl-node-icon">FX</div>
        <b>Transform</b>
        <span>Imputasi Open = 0, hitung return, MA20/MA60, drawdown, volatility, foreign flow, volume ratio.</span>
        <small>signal metrics</small>
    </div>
    <div class="etl-arrow">-&gt;</div>
    <div class="etl-node load">
        <div class="etl-node-icon">LOAD</div>
        <b>Load</b>
        <span>Membentuk processed data, fact table, dimension table, metrics, dan visual signal.</span>
        <small>{mart_count} data mart tables</small>
    </div>
    <div class="etl-arrow">-&gt;</div>
    <div class="etl-node dashboard-node">
        <div class="etl-node-icon">BI</div>
        <b>Dashboard</b>
        <span>Menampilkan KPI, chart, visual signal, dan quality status.</span>
        <small>executive signal</small>
    </div>
    """
    mini_steps = [
        ("SRC", "Source"),
        ("RAW", "Raw Table"),
        ("VAL", "Validation"),
        ("TRF", "Transform"),
        ("DM", "Data Mart"),
        ("BI", "Dashboard"),
    ]
    mini_html = '<span>ETL Pipeline</span>' + "".join(
        f'<span class="etl-mini-step"><span class="etl-mini-icon">{icon}</span>{label}</span><span>-&gt;</span>'
        for icon, label in mini_steps[:-1]
    )
    mini_html += f'<span class="etl-mini-step"><span class="etl-mini-icon">{mini_steps[-1][0]}</span>{mini_steps[-1][1]}</span>'
    code_html = """
<span class="comment"># reusable ETL engine</span>
raw = <span class="fn">read_csv</span>(source)
validated, report = <span class="fn">validate_dataframe</span>(raw)

if report.status != "ERROR":
    transformed = <span class="fn">transform_dataframe</span>(validated)
    mart = <span class="fn">build_data_mart</span>(transformed)
    metrics = <span class="fn">summarize_metrics</span>(transformed)
"""
    st.markdown(
        f"""
        <div class="etl-flow-card">
            <div class="etl-flow-title">
                <h3>ETL Process Flow</h3>
                <span>Source data -&gt; validation -&gt; transformation -&gt; BI dashboard</span>
            </div>
            <div class="etl-flow-layout">
                <div>
                    <div class="etl-flow-grid">{node_html}</div>
                    <div class="etl-mini-pipeline">{mini_html}</div>
                </div>
                <div class="etl-code-panel">
                    <h4>ETL Logic</h4>
                    <pre>{code_html}</pre>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mart_cards(mart: dict[str, pd.DataFrame]) -> None:
    columns = st.columns(min(len(mart), 3))
    for column, (name, frame) in zip(columns, mart.items()):
        with column:
            st.markdown(
                f'<div class="mart-card"><b>{name}</b><span>{len(frame):,} rows | {len(frame.columns)} columns</span></div>',
                unsafe_allow_html=True,
            )


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def chart_card(title: str, note: str, frame: pd.DataFrame, height: int = 280) -> None:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-note">{note}</div>', unsafe_allow_html=True)
    st.line_chart(frame, height=height)
    st.markdown("</div>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_default_data():
    return run_pipeline(RAW_PATH)


def report_from_database(data: pd.DataFrame) -> ValidationReport:
    return ValidationReport(
        status="DATABASE",
        errors=[],
        warnings=[],
        row_count=len(data),
        column_count=len(data.columns),
        min_date=data["Date"].min().strftime("%Y-%m-%d") if not data.empty else None,
        max_date=data["Date"].max().strftime("%Y-%m-%d") if not data.empty else None,
        duplicate_dates=int(data["Date"].duplicated().sum()) if "Date" in data else 0,
        open_zero_count=int(data.get("Open_Was_Imputed", pd.Series(dtype=bool)).sum()),
        missing_critical_count=0,
        ticker_values=sorted([str(x) for x in data["Ticker"].dropna().unique().tolist()]) if "Ticker" in data else [],
    )


@st.cache_data(show_spinner=False)
def load_database_data():
    if read_fact_data is None:
        raise RuntimeError("Modul database tidak tersedia.")
    data = read_fact_data()
    report = report_from_database(data)
    mart = build_data_mart(data)
    metrics = summarize_metrics(data)
    return data, report, mart, metrics


@st.cache_data(show_spinner=False)
def filter_by_date(data: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()
    return data[(data["Date"].dt.date >= start) & (data["Date"].dt.date <= end)].copy()


def resolve_date_range(data: pd.DataFrame, preset: str, custom_range: tuple[Any, ...] | None = None) -> tuple[Any, Any]:
    min_date = data["Date"].min().date()
    max_date = data["Date"].max().date()

    if preset == "Custom" and custom_range and len(custom_range) == 2:
        start, end = custom_range
        return max(start, min_date), min(end, max_date)
    if preset == "1 Bulan":
        start = (pd.Timestamp(max_date) - pd.DateOffset(months=1)).date()
    elif preset == "3 Bulan":
        start = (pd.Timestamp(max_date) - pd.DateOffset(months=3)).date()
    elif preset == "6 Bulan":
        start = (pd.Timestamp(max_date) - pd.DateOffset(months=6)).date()
    elif preset == "1 Tahun":
        start = (pd.Timestamp(max_date) - pd.DateOffset(years=1)).date()
    elif preset == "YTD":
        start = pd.Timestamp(year=max_date.year, month=1, day=1).date()
    else:
        start = min_date
    return max(start, min_date), max_date


@st.cache_data(show_spinner=False)
def cached_summary(filtered: pd.DataFrame) -> dict[str, Any]:
    return filtered_summary(filtered)


@st.cache_data(show_spinner=False)
def prepare_chart_data(filtered: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    chart_data = filtered.sort_values("Date").set_index("Date")
    date_span = (chart_data.index.max() - chart_data.index.min()).days if len(chart_data) > 1 else 0
    mode = "harian"

    if date_span > 365:
        chart_data = chart_data.resample("W-FRI").last().dropna(how="all")
        mode = "mingguan"

    chart_data = chart_data.assign(
        Drawdown_Watch=-0.10,
        Drawdown_Pressure=-0.20,
        Volatility_Watch=0.45,
    )
    return chart_data, mode


def get_active_data():
    uploaded = st.session_state.get("uploaded_file")
    if uploaded is not None:
        raw = pd.read_csv(uploaded, encoding="utf-8-sig")
        uploaded.seek(0)
        validated, report = validate_dataframe(raw)
        if report.status == "ERROR":
            return validated, report, {}, {}
        transformed = transform_dataframe(validated)
        mart = build_data_mart(transformed)
        metrics = summarize_metrics(transformed)
        if load_data_mart is not None:
            try:
                load_data_mart(mart)
                st.session_state["data_source"] = "Uploaded CSV -> MySQL"
                st.cache_data.clear()
            except Exception as exc:
                st.session_state["db_warning"] = f"Upload valid, tetapi gagal load ke MySQL: {exc}"
                st.session_state["data_source"] = "Uploaded CSV"
        else:
            st.session_state["data_source"] = "Uploaded CSV"
        return transformed, report, mart, metrics
    try:
        data, report, mart, metrics = load_database_data()
        st.session_state["data_source"] = "MySQL"
        st.session_state.pop("db_warning", None)
        return data, report, mart, metrics
    except Exception as exc:
        st.session_state["db_warning"] = f"Database fallback aktif: {exc}"
        st.session_state["data_source"] = "CSV"
        return load_default_data()


def hero(report, metrics: dict[str, Any]) -> None:
    latest_date = metrics.get("latest_date") or report.max_date or "-"
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-left">
                <img src="data:image/png;base64,{logo_base64()}" class="hero-logo" />
                <div>
                    <h1>Executive Signal Dashboard BBRI</h1>
                    <p>Market intelligence dan corporate action watch berbasis data perdagangan harian</p>
                </div>
            </div>
            <div class="hero-pill">Status Data {report.status} | Data terakhir {latest_date}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar(report, data: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    st.sidebar.image(str(LOGO_PATH), width=54)
    st.sidebar.markdown("### BBRI BI")
    st.sidebar.caption("Executive Signal Dashboard")
    page = st.sidebar.radio("Menu", ["Dashboard", "Proses Data"])

    st.sidebar.markdown("---")
    uploaded = st.sidebar.file_uploader("Import CSV BBRI", type=["csv"])
    if uploaded is not None:
        st.session_state["uploaded_file"] = uploaded
        st.sidebar.success("CSV diterima. Validasi otomatis berjalan.")

    if st.sidebar.button("Reset data default", use_container_width=True):
        st.session_state.pop("uploaded_file", None)
        st.cache_data.clear()
        st.rerun()

    filtered = data.copy()
    if report.status != "ERROR" and "Date" in filtered.columns and not filtered.empty:
        st.sidebar.markdown("---")
        min_date = filtered["Date"].min().date()
        max_date = filtered["Date"].max().date()
        preset = st.sidebar.selectbox(
            "Rentang waktu",
            ["Semua Data", "1 Bulan", "3 Bulan", "6 Bulan", "1 Tahun", "YTD", "Custom"],
            index=0,
        )
        custom_range = None
        if preset == "Custom":
            custom_range = st.sidebar.date_input(
                "Pilih tanggal",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        start, end = resolve_date_range(filtered, preset, custom_range if isinstance(custom_range, tuple) else None)
        filtered = filter_by_date(filtered, str(start), str(end))
        st.sidebar.markdown(
            f'<div class="active-range">{start.strftime("%Y-%m-%d")} - {end.strftime("%Y-%m-%d")}</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Status Data**")
    st.sidebar.write(report.status)
    st.sidebar.caption(f"Source: {st.session_state.get('data_source', 'CSV')}")
    if st.session_state.get("db_warning"):
        st.sidebar.warning(st.session_state["db_warning"])
    st.sidebar.caption(f"{report.min_date} - {report.max_date}")
    st.sidebar.caption(f"Rows: {report.row_count:,} | Open imputed: {report.open_zero_count}")
    return page, filtered


def filtered_summary(filtered: pd.DataFrame) -> dict[str, Any]:
    ordered = filtered.sort_values("Date")
    latest = ordered.iloc[-1]
    first = ordered.iloc[0]
    recent = ordered.tail(20)
    return {
        "first_date": first["Date"].strftime("%Y-%m-%d"),
        "latest_date": latest["Date"].strftime("%Y-%m-%d"),
        "latest_close": float(latest["Close"]),
        "period_return": float(latest["Close"] / first["Close"] - 1),
        "return_20d": float(latest["Close"] / recent.iloc[0]["Close"] - 1) if len(recent) > 1 else 0.0,
        "latest_drawdown": float(latest["Drawdown"]),
        "drawdown_zone": str(latest["Drawdown_Zone"]),
        "latest_volatility": float(latest["Rolling_Volatility_20D"]) if pd.notna(latest["Rolling_Volatility_20D"]) else None,
        "rolling_net_foreign_20d": float(latest["Rolling_Net_Foreign_20D"]) if pd.notna(latest["Rolling_Net_Foreign_20D"]) else float(recent["Net_Foreign_Flow"].sum()),
        "volume_ratio_20d": float(latest["Volume_Ratio_20D"]) if pd.notna(latest["Volume_Ratio_20D"]) else None,
        "ma20": float(latest["MA20"]) if pd.notna(latest["MA20"]) else None,
        "ma60": float(latest["MA60"]) if pd.notna(latest["MA60"]) else None,
        "market_status": str(latest["Market_Status"]),
        "corporate_action_watch": str(latest["Corporate_Action_Watch"]),
        "daily_return": float(latest["Daily_Return"]) if pd.notna(latest["Daily_Return"]) else 0.0,
    }


def trend_state(s: dict[str, Any]) -> tuple[str, str, str]:
    below_ma20 = s["ma20"] is not None and s["latest_close"] < s["ma20"]
    below_ma60 = s["ma60"] is not None and s["latest_close"] < s["ma60"]
    if below_ma20 and below_ma60:
        return "Pressure", "Below MA20/MA60", "danger"
    if below_ma20 or below_ma60:
        return "Watch", "Below one MA", "warn"
    return "Normal", "Above MA", "good"


def signal_tiles(summary: dict[str, Any]) -> None:
    trend_label, trend_measure, trend_variant = trend_state(summary)
    drawdown_variant = "danger" if summary["latest_drawdown"] <= -0.20 else "warn" if summary["latest_drawdown"] <= -0.10 else "good"
    foreign_variant = "danger" if summary["rolling_net_foreign_20d"] < 0 else "good"
    volume_variant = "warn" if (summary["volume_ratio_20d"] or 0) >= 1.5 else "good"
    volatility_variant = "warn" if (summary["latest_volatility"] or 0) >= 0.45 else "good"
    action_variant = "danger" if summary["corporate_action_watch"] == "Buyback Watch" else "warn" if "Watch" in summary["corporate_action_watch"] else "good"
    tiles = [
        ("Trend", trend_label, trend_measure, trend_variant),
        ("Drawdown", summary["drawdown_zone"].replace(" Zone", ""), pct(summary["latest_drawdown"]), drawdown_variant),
        ("Foreign Flow", "Negative" if summary["rolling_net_foreign_20d"] < 0 else "Positive", compact_number(summary["rolling_net_foreign_20d"]), foreign_variant),
        ("Volume Spike", "Spike" if (summary["volume_ratio_20d"] or 0) >= 1.5 else "Normal", f"{summary['volume_ratio_20d']:.2f}x" if summary["volume_ratio_20d"] is not None else "-", volume_variant),
        ("Volatility", "Watch" if (summary["latest_volatility"] or 0) >= 0.45 else "Normal", pct(summary["latest_volatility"]), volatility_variant),
        ("Action Watch", summary["corporate_action_watch"], "visual signal", action_variant),
    ]
    st.markdown(
        """
        <div class="legend-row">
            <span><span class="legend-dot dot-good"></span>Normal</span>
            <span><span class="legend-dot dot-warn"></span>Watch</span>
            <span><span class="legend-dot dot-danger"></span>Pressure</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    columns = st.columns(6)
    for column, (name, state, measure, variant) in zip(columns, tiles):
        with column:
            st.markdown(
                f'<div class="signal-tile {variant}"><div class="signal-name">{name}</div><div class="signal-state">{state}</div><div class="signal-measure">{measure}</div></div>',
                unsafe_allow_html=True,
            )


def donut_chart(title: str, note: str, frame: pd.DataFrame, category: str) -> None:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-note">{note}</div>', unsafe_allow_html=True)
    counts = frame[category].value_counts().rename_axis(category).reset_index(name="Days")
    st.vega_lite_chart(
        counts,
        {
            "mark": {"type": "arc", "innerRadius": 58, "outerRadius": 105},
            "encoding": {
                "theta": {"field": "Days", "type": "quantitative"},
                "color": {
                    "field": category,
                    "type": "nominal",
                    "scale": {
                        "domain": ["Normal", "Watch", "Pressure", "Normal Zone", "Watch Zone", "Pressure Zone"],
                        "range": ["#059669", "#d97706", "#dc2626", "#059669", "#d97706", "#dc2626"],
                    },
                },
                "tooltip": [{"field": category}, {"field": "Days", "type": "quantitative"}],
            },
            "view": {"stroke": None},
        },
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def monthly_return_heatmap(frame: pd.DataFrame) -> None:
    monthly = (
        frame.sort_values("Date")
        .groupby([frame["Date"].dt.year.rename("Year"), frame["Date"].dt.month.rename("Month")])
        .agg(first_close=("Close", "first"), last_close=("Close", "last"))
        .reset_index()
    )
    monthly["Return"] = monthly["last_close"] / monthly["first_close"] - 1
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Monthly Return Heatmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-note">Warna memperlihatkan bulan positif dan negatif pada rentang aktif.</div>', unsafe_allow_html=True)
    st.vega_lite_chart(
        monthly,
        {
            "mark": {"type": "rect", "cornerRadius": 4},
            "encoding": {
                "x": {"field": "Month", "type": "ordinal", "title": "Month"},
                "y": {"field": "Year", "type": "ordinal", "title": "Year"},
                "color": {
                    "field": "Return",
                    "type": "quantitative",
                    "scale": {"domainMid": 0, "range": ["#dc2626", "#ffffff", "#059669"]},
                    "format": ".2%",
                },
                "tooltip": [
                    {"field": "Year", "type": "ordinal"},
                    {"field": "Month", "type": "ordinal"},
                    {"field": "Return", "type": "quantitative", "format": ".2%"},
                ],
            },
            "height": 250,
        },
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def volume_return_scatter(frame: pd.DataFrame) -> None:
    plot_data = frame[["Date", "Daily_Return", "Volume_Ratio_20D", "Market_Status"]].dropna().copy()
    plot_data["Date_Label"] = plot_data["Date"].dt.strftime("%Y-%m-%d")
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Volume Ratio vs Daily Return</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-note">Titik kanan-bawah menunjukkan volume tinggi saat harga turun.</div>', unsafe_allow_html=True)
    st.vega_lite_chart(
        plot_data,
        {
            "mark": {"type": "circle", "opacity": 0.72, "size": 60},
            "encoding": {
                "x": {"field": "Volume_Ratio_20D", "type": "quantitative", "title": "Volume Ratio 20D"},
                "y": {"field": "Daily_Return", "type": "quantitative", "title": "Daily Return", "axis": {"format": ".1%"}},
                "color": {
                    "field": "Market_Status",
                    "type": "nominal",
                    "scale": {"domain": ["Normal", "Watch", "Pressure"], "range": ["#059669", "#d97706", "#dc2626"]},
                },
                "tooltip": [
                    {"field": "Date_Label", "title": "Date"},
                    {"field": "Volume_Ratio_20D", "format": ".2f"},
                    {"field": "Daily_Return", "format": ".2%"},
                    {"field": "Market_Status"},
                ],
            },
            "height": 260,
        },
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def page_dashboard(report, metrics: dict[str, Any], filtered: pd.DataFrame) -> None:
    hero(report, metrics)
    if filtered.empty:
        st.warning("Tidak ada data pada rentang waktu yang dipilih.")
        return

    summary = cached_summary(filtered)
    status_class = f"status-{summary['market_status'].lower()}"

    st.markdown(
        f"""
        <div class="signal-strip">
            <div class="status-badge {status_class}">{summary['market_status'].upper()}</div>
            <div class="signal-text">
                <b>Active Period:</b> {summary['first_date']} - {summary['latest_date']}<br>
                <b>Visual Mode:</b> KPI, threshold, zone, and chart-based interpretation
            </div>
            <div class="watch-box"><span>Corporate Action Watch</span><b>{summary['corporate_action_watch']}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Market Status", summary["market_status"], short_status_reason(summary), variant_for_status(summary["market_status"]))
    with c2:
        kpi_card("Harga Terakhir", f"{summary['latest_close']:,.0f}", str(summary["latest_date"]))
    with c3:
        kpi_card("Return 20D", pct(summary["return_20d"]), "momentum pendek", variant_for_negative(summary["return_20d"], 0, -0.05))
    with c4:
        kpi_card("Drawdown Terkini", pct(summary["latest_drawdown"]), summary["drawdown_zone"], "danger" if summary["latest_drawdown"] <= -0.20 else "warn" if summary["latest_drawdown"] <= -0.10 else "good")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        kpi_card("Volatilitas 20D", pct(summary["latest_volatility"]), "threshold watch 45%", "warn" if (summary["latest_volatility"] or 0) >= 0.45 else "good")
    with c6:
        kpi_card("Net Foreign Flow 20D", compact_number(summary["rolling_net_foreign_20d"]), "rolling 20D", "danger" if summary["rolling_net_foreign_20d"] < 0 else "good")
    with c7:
        kpi_card("Volume vs Avg 20D", f"{summary['volume_ratio_20d']:.2f}x" if summary["volume_ratio_20d"] is not None else "-", "spike > 1.5x", "warn" if (summary["volume_ratio_20d"] or 0) >= 1.5 else "good")
    with c8:
        kpi_card("Corporate Action Watch", summary["corporate_action_watch"], "decision signal", "danger" if summary["corporate_action_watch"] == "Buyback Watch" else "warn" if "Watch" in summary["corporate_action_watch"] else "good")

    section("Visual Signal Board", "Warna dan status membantu pembacaan cepat tanpa narasi rekomendasi.")
    signal_tiles(summary)

    chart_data, chart_mode = prepare_chart_data(filtered)
    section(
        "Market Trend & Risk",
        f"Visualisasi memakai data {chart_mode}; rentang panjang otomatis diagregasi mingguan agar dashboard tetap ringan.",
    )

    c9, c10 = st.columns(2)
    with c9:
        chart_card("Close Price vs Moving Average", "Close dibandingkan MA20 dan MA60 untuk membaca posisi tren.", chart_data[["Close", "MA20", "MA60"]], 300)
    with c10:
        chart_card("Drawdown Zone", "Zona watch dimulai -10%, zona pressure di bawah -20%.", chart_data[["Drawdown", "Drawdown_Watch", "Drawdown_Pressure"]], 300)

    chart_card(
        "Foreign Flow Pressure",
        "Rolling net foreign flow 20 hari untuk menangkap tekanan investor asing.",
        chart_data[["Rolling_Net_Foreign_20D"]],
        260,
    )

    section("Komposisi dan Pola")
    c11, c12 = st.columns(2)
    with c11:
        donut_chart("Market Status Composition", "Komposisi jumlah hari berdasarkan status pasar.", filtered, "Market_Status")
    with c12:
        donut_chart("Drawdown Zone Composition", "Komposisi jumlah hari berdasarkan zona drawdown.", filtered, "Drawdown_Zone")

    monthly_return_heatmap(filtered)

    section("Volume & Volatility")
    c13, c14 = st.columns(2)
    with c13:
        volume_return_scatter(filtered)
    with c14:
        chart_card("Volatility Trend", "Rolling volatility 20 hari dengan batas watch 45%.", chart_data[["Rolling_Volatility_20D", "Volatility_Watch"]], 260)


def page_process_data(data: pd.DataFrame, report, metrics: dict[str, Any], mart: dict[str, pd.DataFrame]) -> None:
    hero(report, metrics)
    section("Proses Data", "Halaman ini dipakai untuk melihat validasi CSV, quality warning, dan hasil ETL.")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Status", report.status, "hasil validasi", "danger" if report.status == "ERROR" else "warn" if report.status == "WARNING" else "good")
    with c2:
        kpi_card("Rows", f"{report.row_count:,}", f"{report.column_count} kolom")
    with c3:
        kpi_card("Periode", report.min_date or "-", f"sampai {report.max_date or '-'}")
    with c4:
        kpi_card("Duplicate Date", str(report.duplicate_dates), "data harian harus unik", "danger" if report.duplicate_dates else "good")
    with c5:
        kpi_card("Open Imputed", str(report.open_zero_count), "Previous / prior close", "warn" if report.open_zero_count else "good")

    section("Quality Check", "Ringkasan kualitas dataset aktif sebelum dipakai oleh dashboard.")
    outlier_warnings = [warning for warning in report.warnings if "outlier" in warning.lower()]
    q1, q2, q3 = st.columns(3)
    with q1:
        validation_card(
            "Schema",
            "Kolom wajib lengkap" if not any("Kolom wajib" in error for error in report.errors) else "Kolom wajib belum lengkap",
            f"{report.column_count} kolom terbaca.",
            "ERROR" if any("Kolom wajib" in error for error in report.errors) else "VALID",
        )
    with q2:
        validation_card(
            "Ticker",
            "Ticker BBRI" if report.ticker_values == ["BBRI"] else "Ticker perlu dicek",
            ", ".join(report.ticker_values) if report.ticker_values else "Tidak ada ticker terbaca.",
            "VALID" if report.ticker_values == ["BBRI"] else "ERROR",
        )
    with q3:
        validation_card(
            "Date",
            "Format tanggal valid" if report.min_date and report.max_date else "Tanggal tidak valid",
            f"{report.min_date or '-'} sampai {report.max_date or '-'}",
            "VALID" if report.min_date and report.max_date else "ERROR",
        )

    q4, q5, q6 = st.columns(3)
    with q4:
        validation_card(
            "Duplicate Date",
            "Tidak ada duplikasi" if report.duplicate_dates == 0 else "Ada duplikasi tanggal",
            f"{report.duplicate_dates} duplicate date.",
            "VALID" if report.duplicate_dates == 0 else "ERROR",
        )
    with q5:
        validation_card(
            "Open Imputation",
            "Sudah diproses" if report.open_zero_count else "Tidak perlu imputasi",
            f"{report.open_zero_count} baris Open = 0 diisi dari Previous atau Close hari sebelumnya.",
            "WARNING" if report.open_zero_count else "VALID",
        )
    with q6:
        validation_card(
            "Outlier",
            "Potensi outlier ditemukan" if outlier_warnings else "Tidak ada outlier terdeteksi",
            f"{len(outlier_warnings)} catatan outlier volume/value.",
            "WARNING" if outlier_warnings else "VALID",
        )

    section("ETL Pipeline")
    etl_process_flow(report, mart)

    v1, v2 = st.columns(2)
    with v1:
        warning_callout("Errors", report.errors, "error" if report.errors else "success")
    with v2:
        warning_callout("Warnings", report.warnings, "warning" if report.warnings else "success")

    section("Output Data Mart")
    if mart:
        mart_cards(mart)
    else:
        st.info("Data mart belum dibuat karena data masih berstatus ERROR.")

    with st.expander("Preview data hasil transformasi", expanded=False):
        st.dataframe(data.tail(30), use_container_width=True)


def main() -> None:
    inject_style()
    data, report, mart, metrics = get_active_data()
    page, filtered = sidebar(report, data)

    if report.status == "ERROR":
        page_process_data(data, report, metrics, mart)
        return

    if page == "Dashboard":
        page_dashboard(report, metrics, filtered)
    else:
        page_process_data(data, report, metrics, mart)


if __name__ == "__main__":
    main()
