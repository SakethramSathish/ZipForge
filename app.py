"""
app.py — Streamlit front-end for the File Compressor application.

Tabs:
  1. 🗜️  File Compression  — compress files to .fcmp archives
  2. 📂  File Decompression — extract .fcmp archives
  3. 🖼️  Image Optimizer    — profile-based + target-size image compression
  4. 📊  Benchmark          — compare algorithms on uploaded files
  5. 🔍  Inspect Archive    — view .fcmp archive metadata without extracting

Design principles:
  - All actual work is delegated to application services (no business logic in UI)
  - Every file operation shows real metrics (no fake percentages)
  - Errors are displayed clearly with remediation hints
"""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import streamlit as st

# Configure logging before any other imports
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

# Application imports (no Streamlit dependency in any of these)
from application.compression_service import (
    compress_files,
    compress_files_to_target,
    decompress_to_memory,
    inspect_archive,
)
from application.image_service import compress_image, optimize_image_to_target
from algorithms.registry import get_registry, compress_with
from config import (
    SUPPORTED_INPUT_FORMATS,
    TARGET_SIZE_MAX_ITERATIONS,
    TARGET_SIZE_MAX_QUALITY,
    TARGET_SIZE_MIN_QUALITY,
)
from exceptions import FileCompressorError
from models.image import ImageProfile

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ZipForge — Multi-Engine File Compressor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — premium dark theme
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Root theme ─────────────────────────────────── */
:root {
    --bg-primary:    #0d1117;
    --bg-card:       #161b22;
    --bg-card-hover: #1c2128;
    --border:        #30363d;
    --accent:        #58a6ff;
    --accent-glow:   rgba(88,166,255,0.15);
    --green:         #3fb950;
    --red:           #f85149;
    --yellow:        #d29922;
    --text-primary:  #e6edf3;
    --text-muted:    #8b949e;
    --radius:        12px;
    --radius-sm:     8px;
}

/* ── Global app backgrounds and text ────────────── */
html, body, .stApp, 
[data-testid="stAppViewContainer"], 
[data-testid="stHeader"], 
[data-testid="stSidebar"], 
[data-testid="stSidebarContent"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* ── Hide Streamlit chrome ───────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── App container ───────────────────────────────── */
.block-container { 
    padding: 2rem 3rem !important; 
    max-width: 1400px !important;
}

/* ── Ensure all text, markdown & labels have high contrast in dark mode ── */
label,
.stWidgetLabel,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] li,
.stSelectbox label p,
.stTextInput label p,
.stNumberInput label p,
.stFileUploader label p,
.stRadio label p {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* ── Hero banner ─────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 50%, #161b22 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 2.2rem;
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.35);
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #ffffff 30%, var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.2;
}
.hero-sub {
    color: var(--text-muted);
    font-size: 1.05rem;
    margin-top: 0.75rem;
    font-weight: 400;
}

/* ── Metric card ─────────────────────────────────── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 1.25rem 1.5rem;
    text-align: center;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}
.metric-card:hover {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
    transform: translateY(-2px);
}
.metric-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
    display: block;
}
.metric-label {
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.4rem;
    display: block;
}

/* ── Status badges ───────────────────────────────── */
.badge { 
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-green { background: rgba(63,185,80,0.15); color: var(--green); border: 1px solid rgba(63,185,80,0.3); }
.badge-blue  { background: var(--accent-glow); color: var(--accent); border: 1px solid rgba(88,166,255,0.3); }
.badge-red   { background: rgba(248,81,73,0.15); color: var(--red);   border: 1px solid rgba(248,81,73,0.3); }
.badge-yellow{ background: rgba(210,153,34,0.15); color: var(--yellow); border: 1px solid rgba(210,153,34,0.3); }

/* ── Algorithm badge ─────────────────────────────── */
.algo-tag {
    display: inline-block;
    background: linear-gradient(135deg, var(--accent-glow), rgba(88,166,255,0.05));
    color: var(--accent);
    border: 1px solid rgba(88,166,255,0.25);
    border-radius: 6px;
    padding: 0.15rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}

/* ── Info section ────────────────────────────────── */
.info-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: var(--radius-sm);
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    color: var(--text-primary);
}

/* ── Progress bar override ───────────────────────── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent), #79c0ff) !important;
}

/* ── Table ───────────────────────────────────────── */
.styled-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: var(--radius-sm);
    overflow: hidden;
    border: 1px solid var(--border);
    font-size: 0.875rem;
    background: var(--bg-card);
}
.styled-table th {
    background: #1c2128;
    color: var(--text-muted);
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
}
.styled-table td {
    padding: 0.65rem 1rem;
    border-bottom: 1px solid rgba(48,54,61,0.5);
    color: var(--text-primary);
}
.styled-table tr:last-child td { border-bottom: none; }
.styled-table tr:hover td { background: var(--bg-card-hover); }

/* ── Buttons ─────────────────────────────────────── */
button[kind="primary"], .stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #1f6feb, #388bfd) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(31,111,235,0.3) !important;
}
button[kind="primary"]:hover, .stButton > button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(31,111,235,0.45) !important;
}

button[kind="secondary"], .stButton > button[data-testid="baseButton-secondary"] {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
button[kind="secondary"]:hover, .stButton > button[data-testid="baseButton-secondary"]:hover {
    border-color: var(--accent) !important;
    background-color: var(--bg-card-hover) !important;
    color: var(--accent) !important;
}

/* ── Download button ─────────────────────────────── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #238636, #2ea043) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(35,134,54,0.3) !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(35,134,54,0.45) !important;
}

/* ── File uploader ───────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
    transition: border-color 0.2s ease !important;
    background: var(--bg-card) !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small,
[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: var(--text-muted) !important;
}

/* ── Form Inputs & Selects ───────────────────────── */
[data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}
[data-baseweb="input"] input {
    color: var(--text-primary) !important;
    background-color: transparent !important;
}
[data-baseweb="select"] > div {
    background-color: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
}
[data-baseweb="menu"] li {
    color: var(--text-primary) !important;
}
[data-baseweb="menu"] li:hover {
    background-color: var(--bg-card-hover) !important;
}

/* ── Tab bar ─────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: var(--radius) var(--radius) 0 0 !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
    padding: 0 0.5rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 0 !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    padding: 0.85rem 1.4rem !important;
    transition: all 0.2s ease !important;
    font-size: 0.92rem !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius) var(--radius) !important;
    padding: 2rem !important;
}

/* ── Divider ─────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── Expander ────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
}
[data-testid="stExpander"] summary:hover {
    color: var(--accent) !important;
}

/* ── Sidebar ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0b0e14 !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarContent"] {
    background-color: #0b0e14 !important;
}

/* ── Code blocks ─────────────────────────────────── */
code {
    background-color: #1f242c !important;
    color: #79c0ff !important;
    padding: 0.15rem 0.4rem !important;
    border-radius: 4px !important;
    font-size: 0.85em !important;
}
/* ── Compression level cards ─────────────────── */
.level-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    margin: 1rem 0 1.5rem 0;
}
.level-card {
    background: var(--bg-card);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    cursor: pointer;
    position: relative;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease;
}
.level-card:hover {
    border-color: rgba(88,166,255,0.5);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}
.level-card.selected {
    border-color: var(--green);
    box-shadow: 0 0 0 3px rgba(63,185,80,0.2);
}
.level-card .check-icon {
    position: absolute;
    top: 1rem;
    right: 1rem;
    width: 26px;
    height: 26px;
    background: var(--green);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    color: #fff;
    font-weight: 700;
    opacity: 0;
    transition: opacity 0.2s ease;
}
.level-card.selected .check-icon { opacity: 1; }
.level-card .card-title {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}
.level-card .card-desc {
    font-size: 0.88rem;
    color: var(--text-muted);
    line-height: 1.45;
}
.level-extreme  .card-title { color: #f85149; }
.level-recommended .card-title { color: #f0883e; }
.level-less     .card-title { color: var(--green); }

/* ── Target-size panel ───────────────────────── */
.target-size-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: var(--radius-sm);
    padding: 1.1rem 1.4rem;
    margin: 0.5rem 0 1rem 0;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _fmt_bytes(n: int) -> str:
    """Human-readable file size."""
    if n < 1024:
        return f"{n} B"
    elif n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    elif n < 1024 ** 3:
        return f"{n / 1024 ** 2:.2f} MB"
    return f"{n / 1024 ** 3:.2f} GB"


def _fmt_pct(pct: float) -> str:
    return f"{pct:.1f}%"


def _fmt_ratio(r: float) -> str:
    return f"{r:.2f}×" if r != float("inf") else "∞×"


def _metric_html(value: str, label: str) -> str:
    return (
        f'<div class="metric-card">'
        f'<span class="metric-value">{value}</span>'
        f'<span class="metric-label">{label}</span>'
        f'</div>'
    )


def _show_metrics_row(cols, metrics: list[tuple[str, str]]) -> None:
    """Render a row of metric cards."""
    for col, (value, label) in zip(cols, metrics):
        col.markdown(_metric_html(value, label), unsafe_allow_html=True)


def _badge(text: str, color: str = "blue") -> str:
    return f'<span class="badge badge-{color}">{text}</span>'


def _algo_tag(name: str) -> str:
    return f'<span class="algo-tag">{name}</span>'


def _render_entry_table(entries) -> None:
    """Render archive inspection table."""
    rows = ""
    for entry in entries:
        status_badge = {
            "VALID": _badge("✓ VALID", "green"),
            "CORRUPTED": _badge("✗ CORRUPTED", "red"),
            "UNVERIFIED": _badge("~ UNVERIFIED", "yellow"),
        }.get(entry.integrity_status, _badge("?", "yellow"))

        rows += f"""
        <tr>
            <td><code>{entry.path}</code></td>
            <td>{_algo_tag(entry.algorithm)}</td>
            <td>{_fmt_bytes(entry.original_size)}</td>
            <td>{_fmt_bytes(entry.compressed_size)}</td>
            <td>{_fmt_pct(entry.reduction_percent)}</td>
            <td>{status_badge}</td>
        </tr>
        """

    html = f"""
    <table class="styled-table">
        <thead>
            <tr>
                <th>Path</th>
                <th>Algorithm</th>
                <th>Original</th>
                <th>Compressed</th>
                <th>Reduction</th>
                <th>Integrity</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-title">⚡ ZipForge</div>
        <div class="hero-sub">
            Adaptive Multi-Engine Compression · RLE · Huffman · LZW · Smart Target-Size Optimizer
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar — algorithm info
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚡ ZipForge Engine")

    with st.expander("🟦 RLE — Run Length Encoding", expanded=False):
        st.markdown(
            """
            **Best for:** Data with long repeated sequences  
            **How it works:** Replaces runs of identical bytes with  
            _(escape, count, byte)_ tokens.  
            **Worst case:** Alternating bytes (slight expansion)
            """
        )

    with st.expander("🟩 Huffman Coding", expanded=False):
        st.markdown(
            """
            **Best for:** Text with skewed character frequencies  
            **How it works:** Assigns shorter bit codes to more  
            frequent bytes using an optimal binary tree.  
            **Guaranteed:** Always ≥ entropy lower bound
            """
        )

    with st.expander("🟨 LZW — Lempel-Ziv-Welch", expanded=False):
        st.markdown(
            """
            **Best for:** Repeated phrases and patterns  
            **How it works:** Builds a shared phrase dictionary  
            on-the-fly. Variable-width codes (9–16 bits).  
            **Note:** Dictionary resets on full (64K entries)
            """
        )

    with st.expander("🟥 STORE — No Compression", expanded=False):
        st.markdown(
            """
            **Used when:** No algorithm reduces file size  
            Payload is stored verbatim with full SHA-256  
            integrity protection.
            """
        )

    st.divider()
    st.markdown("### 🔒 Security")
    st.markdown(
        """
        - SHA-256 integrity on every file  
        - Path traversal prevention  
        - Archive version validation  
        - Malicious size field rejection
        """
    )
    st.divider()
    st.caption("⚡ **ZipForge v2.0** · Multi-Engine Compression Platform")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_compress, tab_decompress, tab_image, tab_benchmark, tab_inspect = st.tabs([
    "🗜️ Compress",
    "📂 Decompress",
    "🖼️ Image Optimizer",
    "📊 Benchmark",
    "🔍 Inspect Archive",
])


# ──────────────────────────────────────────────────────────────────────────────
# Tab 1: Compress
# ──────────────────────────────────────────────────────────────────────────────

with tab_compress:
    st.markdown("### Upload Files to Compress")

    uploaded_files = st.file_uploader(
        "Drop files here or click to browse",
        accept_multiple_files=True,
        key="compress_upload",
        help="Select one or more files to compress into a standard .zip archive",
    )

    if uploaded_files:
        st.divider()

        # ── Compression Level selector ──────────────────────────────────
        st.markdown("#### Compression Level")

        _LEVELS = [
            {
                "id": "EXTREME",
                "css": "level-extreme",
                "title": "EXTREME COMPRESSION",
                "desc": "Less quality, high compression",
            },
            {
                "id": "RECOMMENDED",
                "css": "level-recommended",
                "title": "RECOMMENDED COMPRESSION",
                "desc": "Good quality, good compression",
            },
            {
                "id": "LESS",
                "css": "level-less",
                "title": "LESS COMPRESSION",
                "desc": "High quality, less compression",
            },
        ]

        # Use session state to persist the selection
        if "compress_level" not in st.session_state:
            st.session_state["compress_level"] = "RECOMMENDED"

        # Render cards as columns with click buttons
        card_cols = st.columns(3)
        for col, lvl in zip(card_cols, _LEVELS):
            with col:
                is_selected = st.session_state["compress_level"] == lvl["id"]
                selected_css = "selected" if is_selected else ""
                check_html = '<div class="check-icon">✓</div>' if is_selected else '<div class="check-icon">✓</div>'
                st.markdown(
                    f"""
                    <div class="level-card {lvl['css']} {selected_css}" id="card-{lvl['id'].lower()}">
                        {check_html}
                        <div class="card-title">{lvl['title']}</div>
                        <div class="card-desc">{lvl['desc']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                btn_label = "\u2713 Selected" if is_selected else "Select"
                if st.button(
                    btn_label,
                    key=f"lvl_btn_{lvl['id']}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    st.session_state["compress_level"] = lvl["id"]
                    st.rerun()

        # Map level to algorithm
        _LEVEL_TO_ALGO = {
            "EXTREME": "AUTO",       # tries all, picks smallest output
            "RECOMMENDED": "AUTO",   # same strategy — auto best ratio
            "LESS": "STORE",         # no compression, verbatim storage
        }
        selected_level = st.session_state["compress_level"]
        algorithm = _LEVEL_TO_ALGO[selected_level]

        st.divider()

        # ── Archive name ────────────────────────────────────────────────
        archive_name = st.text_input(
            "Output archive name",
            value="archive",
            key="compress_name",
            help="The .zip extension will be added automatically",
        )

        # ── Target Size toggle ──────────────────────────────────────────
        use_target_size = st.checkbox(
            "🎯 Compress to a specific target size",
            key="compress_use_target",
            help="The program will try all algorithms and pick the one that best fits your target.",
        )

        target_size_bytes: int | None = None
        if use_target_size:
            st.markdown(
                '<div class="target-size-panel">'
                '<strong>🎯 Target Size Mode</strong> — The app will automatically try all lossless compression '
                'algorithms first. If the target still cannot be met and your file is an image, it will '
                'fall back to <em>lossy quality reduction</em> (re-encoding at lower quality) to hit the target. '
                'A warning badge will indicate if quality was degraded.'
                '</div>',
                unsafe_allow_html=True,
            )
            ts_col1, ts_col2 = st.columns([2, 1])
            with ts_col1:
                target_val = st.number_input(
                    "Target size",
                    min_value=1,
                    max_value=100_000,
                    value=500,
                    step=50,
                    key="compress_target_val",
                )
            with ts_col2:
                target_unit = st.selectbox(
                    "Unit",
                    options=["KB", "MB"],
                    index=0,
                    key="compress_target_unit",
                )
            multiplier = 1024 if target_unit == "KB" else 1024 * 1024
            target_size_bytes = int(target_val * multiplier)
            st.caption(f"Target: {_fmt_bytes(target_size_bytes)}")

        st.markdown("")

        # Track uploaded files to reset results if files change
        file_signature = tuple((f.name, f.size) for f in uploaded_files)
        if st.session_state.get("last_uploaded_files") != file_signature:
            st.session_state["last_uploaded_files"] = file_signature
            st.session_state["compression_result"] = None

        # ── Compress button ─────────────────────────────────────────────
        if st.button("🚀 Compress Files", type="primary", use_container_width=True):
            file_pairs: list[tuple[str, bytes]] = [
                (f.name, f.read()) for f in uploaded_files
            ]
            total_input = sum(len(d) for _, d in file_pairs)

            progress_bar = st.progress(0, text="Compressing…")
            target_status: str | None = None

            try:
                t0 = time.perf_counter()

                if use_target_size and target_size_bytes is not None:
                    # ── Target-size mode ────────────────────────────────
                    def _ts_progress(label, archive_size, target, step, total_steps):
                        pct = min(95, int(step / max(total_steps, 1) * 95))
                        progress_bar.progress(
                            pct,
                            text=f"Trying {label}… ({_fmt_bytes(archive_size)} vs target {_fmt_bytes(target)})",
                        )

                    archive_bytes, results, target_status, processed_files = compress_files_to_target(
                        file_pairs,
                        target_size_bytes=target_size_bytes,
                        progress_callback=_ts_progress,
                    )
                else:
                    # ── Level-based mode ────────────────────────────────
                    archive_bytes, results, processed_files = compress_files(file_pairs, algorithm=algorithm)

                elapsed = time.perf_counter() - t0
                progress_bar.progress(100, text="Done!")

                clean_name = archive_name.rstrip(".").strip() if archive_name else "archive"
                safe_name = "".join(c for c in clean_name if c.isalnum() or c in "-_. ").strip() or "archive"

                st.session_state["compression_result"] = {
                    "archive_bytes": archive_bytes,
                    "results": results,
                    "target_status": target_status,
                    "total_input": total_input,
                    "total_compressed": len(archive_bytes),
                    "elapsed": elapsed,
                    "file_names": [name for name, _ in file_pairs],
                    "safe_name": safe_name,
                    "clean_name": clean_name,
                    "processed_files": processed_files,
                }
                st.rerun()

            except FileCompressorError as exc:
                progress_bar.empty()
                st.error(f"**Compression failed:** {exc}")
            except Exception as exc:
                progress_bar.empty()
                st.error(f"**Unexpected error:** {exc}")
                st.exception(exc)

        # ── Display compression results (persisted across button clicks) ────
        res = st.session_state.get("compression_result")
        if res is not None:
            target_status = res["target_status"]
            if target_status == "ACHIEVED":
                st.markdown(
                    _badge("✓ Target Size Achieved — Lossless", "green"),
                    unsafe_allow_html=True,
                )
            elif target_status == "ACHIEVED_LOSSY":
                st.markdown(
                    _badge("⚠ Target Achieved with Quality Reduction — Image was re-encoded at lower quality to meet your target size", "yellow"),
                    unsafe_allow_html=True,
                )
            elif target_status == "BEST_EFFORT":
                st.markdown(
                    _badge(
                        "❌ Target Unachievable — This file cannot be compressed further "
                        "(it may already be compressed, e.g. JPEG/MP4/ZIP). "
                        "Showing the smallest possible result.",
                        "red"
                    ),
                    unsafe_allow_html=True,
                )

            total_input = res["total_input"]
            total_compressed = res["total_compressed"]
            elapsed = res["elapsed"]
            safe_name = res["safe_name"]
            clean_name = res.get("clean_name", "archive")
            processed = res.get("processed_files", [])

            # Metrics row
            st.markdown("#### 📊 Compression Results")
            m1, m2, m3, m4 = st.columns(4)
            _show_metrics_row(
                [m1, m2, m3, m4],
                [
                    (_fmt_bytes(total_input), "Original Size"),
                    (_fmt_bytes(total_compressed), "Archive Size"),
                    (_fmt_pct(max(0, (total_input - total_compressed) / max(total_input, 1) * 100)), "Reduction"),
                    (f"{elapsed:.2f}s", "Total Time"),
                ],
            )

            # Per-file breakdown
            st.markdown("#### 📋 Per-File Details")
            rows = ""
            for r, fname in zip(res["results"], res["file_names"]):
                algo_used = r.algorithm.value if hasattr(r.algorithm, 'value') else str(r.algorithm)
                rows += f"""
                <tr>
                    <td><code>{fname}</code></td>
                    <td>{_algo_tag(algo_used)}</td>
                    <td>{_fmt_bytes(r.original_size)}</td>
                    <td>{_fmt_bytes(r.compressed_size)}</td>
                    <td>{_fmt_pct(r.reduction_percent)}</td>
                    <td>{_fmt_ratio(r.compression_ratio)}</td>
                    <td>{r.duration * 1000:.1f} ms</td>
                </tr>
                """
            st.markdown(
                f"""
                <table class="styled-table">
                    <thead>
                        <tr>
                            <th>File</th><th>Algorithm Used</th><th>Original</th>
                            <th>Compressed</th><th>Reduction</th><th>Ratio</th><th>Time</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

            # ── Download buttons with same file extension support ────────────
            st.markdown("")
            _MIME_TYPES = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
                ".bmp": "image/bmp",
                ".gif": "image/gif",
                ".pdf": "application/pdf",
                ".txt": "text/plain",
                ".csv": "text/csv",
                ".json": "application/json",
                ".xml": "application/xml",
                ".html": "text/html",
                ".md": "text/markdown",
                ".zip": "application/zip",
            }

            if len(processed) == 1:
                orig_fname, file_bytes = processed[0]
                ext = Path(orig_fname).suffix.lower()
                mime = _MIME_TYPES.get(ext, "application/octet-stream")

                if clean_name and clean_name.lower() != "archive":
                    single_dl_name = f"{safe_name}{ext}"
                else:
                    single_dl_name = orig_fname

                dl_col1, dl_col2 = st.columns([1, 1])

                with dl_col1:
                    st.download_button(
                        label=f"⬇️ Download {single_dl_name} ({_fmt_bytes(len(file_bytes))})",
                        data=file_bytes,
                        file_name=single_dl_name,
                        mime=mime,
                        type="primary",
                        use_container_width=True,
                        key="download_single_file_btn",
                    )
                    st.caption(f"💾 Direct file download in your original format (**{ext}**).")

                with dl_col2:
                    st.download_button(
                        label=f"📦 Download as {safe_name}.zip ({_fmt_bytes(total_compressed)})",
                        data=res["archive_bytes"],
                        file_name=f"{safe_name}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="download_zip_archive_btn",
                    )
                    st.caption("📦 Packaged in a standard universal .zip archive.")

            else:
                st.download_button(
                    label=f"📦 Download All as {safe_name}.zip ({_fmt_bytes(total_compressed)})",
                    data=res["archive_bytes"],
                    file_name=f"{safe_name}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    key="download_zip_archive_btn",
                )

                st.markdown("##### 📁 Download Individual Files (in Original Extensions):")
                dl_cols = st.columns(min(3, len(processed)))
                for idx, (p_name, p_bytes) in enumerate(processed):
                    col = dl_cols[idx % len(dl_cols)]
                    p_ext = Path(p_name).suffix.lower()
                    p_mime = _MIME_TYPES.get(p_ext, "application/octet-stream")
                    with col:
                        st.download_button(
                            label=f"⬇️ {p_name} ({_fmt_bytes(len(p_bytes))})",
                            data=p_bytes,
                            file_name=p_name,
                            mime=p_mime,
                            use_container_width=True,
                            key=f"dl_indiv_{idx}_{p_name}",
                        )
    else:
        st.info("👆 Upload one or more files above to get started.")


# ──────────────────────────────────────────────────────────────────────────────
# Tab 2: Decompress
# ──────────────────────────────────────────────────────────────────────────────

with tab_decompress:
    st.markdown("### Extract a .zip Archive")

    archive_file = st.file_uploader(
        "Upload a .zip archive to preview or extract",
        type=["zip"],
        key="decompress_upload",
        help="Upload any standard .zip archive created by ZipForge or other tools.",
    )

    if archive_file:
        archive_bytes = archive_file.read()
        st.markdown(
            f'Archive size: **{_fmt_bytes(len(archive_bytes))}**',
        )

        # Reset decompression if archive changes
        arch_sig = (archive_file.name, archive_file.size)
        if st.session_state.get("last_decompress_file") != arch_sig:
            st.session_state["last_decompress_file"] = arch_sig
            st.session_state["decompressed_entries"] = None

        col_preview, col_extract = st.columns([1, 1])

        with col_preview:
            if st.button("🔍 Preview Archive Contents", use_container_width=True):
                try:
                    inspection = inspect_archive(archive_bytes)
                    st.markdown(f"**{inspection.entry_count}** file(s) · "
                                f"**{_fmt_bytes(inspection.total_original)}** original")
                    _render_entry_table(inspection.entries)
                except FileCompressorError as exc:
                    st.error(f"Cannot read archive: {exc}")

        with col_extract:
            if st.button("📂 Extract All Files", type="primary", use_container_width=True):
                try:
                    entries = decompress_to_memory(archive_bytes)
                    st.session_state["decompressed_entries"] = entries
                    st.rerun()
                except FileCompressorError as exc:
                    st.error(f"**Extraction failed:** {exc}")
                except Exception as exc:
                    st.error(f"**Unexpected error:** {exc}")
                    st.exception(exc)

        # Persistent display of extracted files
        saved_entries = st.session_state.get("decompressed_entries")
        if saved_entries is not None:
            st.success(f"✅ Successfully extracted **{len(saved_entries)}** file(s)")
            for path, data in saved_entries:
                fname = Path(path).name
                st.download_button(
                    label=f"⬇️ {path} ({_fmt_bytes(len(data))})",
                    data=data,
                    file_name=fname,
                    mime="application/octet-stream",
                    key=f"dl_{path}",
                )
    else:
        st.info("👆 Upload a .zip archive above to extract or preview it.")


# ──────────────────────────────────────────────────────────────────────────────
# Tab 3: Image Optimizer
# ──────────────────────────────────────────────────────────────────────────────

with tab_image:
    st.markdown("### 🖼️ Image Optimization")

    img_file = st.file_uploader(
        "Upload an image (JPEG, PNG, WEBP, BMP)",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        key="image_upload",
        help="Supported: JPEG, PNG (with transparency), WEBP, BMP",
    )

    if img_file:
        original_bytes = img_file.read()
        original_size = len(original_bytes)

        # Display original
        with st.expander("📷 Original Image", expanded=True):
            st.image(original_bytes, caption=f"{img_file.name} ({_fmt_bytes(original_size)})", use_container_width=True)

        st.divider()

        # Mode selection
        mode = st.radio(
            "Optimization Mode",
            options=["Profile", "Target Size"],
            horizontal=True,
            key="img_mode",
        )

        if mode == "Profile":
            col_prof, col_fmt = st.columns(2)
            with col_prof:
                profile_name = st.selectbox(
                    "Profile",
                    options=["EXTREME", "RECOMMENDED", "LESS_COMPRESSION"],
                    index=1,
                    key="img_profile",
                    help="EXTREME: max compression. RECOMMENDED: balanced. LESS: high quality.",
                )
            with col_fmt:
                out_fmt = st.selectbox(
                    "Output Format",
                    options=["Auto", "JPEG", "PNG", "WEBP"],
                    index=0,
                    key="img_format",
                )
            preserve_meta = st.checkbox("Preserve EXIF metadata", key="img_meta")

            if st.button("🎨 Optimize Image", type="primary", use_container_width=True):
                fmt_arg = None if out_fmt == "Auto" else out_fmt
                try:
                    result = compress_image(
                        original_bytes,
                        profile_name=profile_name,
                        output_format=fmt_arg,
                        preserve_metadata=preserve_meta,
                    )

                    # Metrics
                    m1, m2, m3, m4 = st.columns(4)
                    _show_metrics_row(
                        [m1, m2, m3, m4],
                        [
                            (_fmt_bytes(original_size), "Original"),
                            (_fmt_bytes(result.final_size), "Optimized"),
                            (_fmt_pct(result.reduction_percent), "Reduction"),
                            (str(result.quality), "Quality"),
                        ],
                    )

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.image(original_bytes, caption="Original", use_container_width=True)
                    with col_b:
                        st.image(result.output_bytes, caption=f"Optimized ({result.output_format})", use_container_width=True)

                    ext = result.output_format.lower()
                    st.download_button(
                        label=f"⬇️ Download Optimized Image (.{ext})",
                        data=result.output_bytes,
                        file_name=f"optimized.{ext}",
                        mime="application/octet-stream",
                        use_container_width=True,
                    )

                except FileCompressorError as exc:
                    st.error(f"**Image optimization failed:** {exc}")

        else:  # Target Size mode
            col_t, col_tf = st.columns(2)
            with col_t:
                target_kb = st.number_input(
                    "Target size (KB)",
                    min_value=1,
                    max_value=50000,
                    value=100,
                    step=10,
                    key="img_target_kb",
                    help="The optimizer will find the highest quality that fits.",
                )
            with col_tf:
                target_fmt = st.selectbox(
                    "Output Format",
                    options=["JPEG", "WEBP"],
                    index=0,
                    key="img_target_fmt",
                )

            if st.button("🎯 Optimize to Target Size", type="primary", use_container_width=True):
                target_bytes = int(target_kb * 1024)
                progress_bar = st.progress(0, text="Searching for optimal quality…")
                status_text = st.empty()

                def progress_callback(iteration, max_iter, quality, size):
                    pct = int(iteration / max_iter * 100)
                    progress_bar.progress(pct, text=f"Iteration {iteration}/{max_iter} — quality={quality}, size={_fmt_bytes(size)}")
                    status_text.markdown(
                        f"Quality: **{quality}** → Size: **{_fmt_bytes(size)}** "
                        f"(target: {_fmt_bytes(target_bytes)})"
                    )

                try:
                    result = optimize_image_to_target(
                        original_bytes,
                        target_size_bytes=target_bytes,
                        output_format=target_fmt,
                        progress_callback=progress_callback,
                    )
                    progress_bar.progress(100, text="Done!")
                    status_text.empty()

                    # Status badge
                    from models.image import TargetStatus
                    if result.target_status == TargetStatus.ACHIEVED:
                        st.markdown(_badge("✓ Target Achieved", "green"), unsafe_allow_html=True)
                    else:
                        st.markdown(_badge("⚠ Target Unachievable — showing best result", "yellow"), unsafe_allow_html=True)

                    # Metrics
                    m1, m2, m3, m4 = st.columns(4)
                    _show_metrics_row(
                        [m1, m2, m3, m4],
                        [
                            (_fmt_bytes(original_size), "Original"),
                            (_fmt_bytes(result.final_size), "Final Size"),
                            (_fmt_pct(result.reduction_percent), "Reduction"),
                            (str(result.iterations), "Iterations"),
                        ],
                    )

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.image(original_bytes, caption="Original", use_container_width=True)
                    with col_b:
                        st.image(result.output_bytes, caption=f"Optimized (q={result.quality})", use_container_width=True)

                    ext = result.output_format.lower()
                    st.download_button(
                        label=f"⬇️ Download ({_fmt_bytes(result.final_size)})",
                        data=result.output_bytes,
                        file_name=f"optimized_target.{ext}",
                        mime="application/octet-stream",
                        use_container_width=True,
                    )

                except FileCompressorError as exc:
                    progress_bar.empty()
                    st.error(f"**Optimization failed:** {exc}")

    else:
        st.info("👆 Upload an image above to start optimization.")


# ──────────────────────────────────────────────────────────────────────────────
# Tab 4: Benchmark
# ──────────────────────────────────────────────────────────────────────────────

with tab_benchmark:
    st.markdown("### 📊 Algorithm Comparison Benchmark")
    st.markdown(
        '<div class="info-box">Upload a file to compare RLE, Huffman, and LZW compression. '
        "Results show <strong>real</strong> compression ratios and speeds — no fabrication.</div>",
        unsafe_allow_html=True,
    )

    bench_file = st.file_uploader(
        "Upload file to benchmark",
        key="bench_upload",
        help="The file will be compressed with each algorithm independently.",
    )

    if bench_file:
        bench_data = bench_file.read()
        bench_size = len(bench_data)

        if st.button("🏁 Run Benchmark", type="primary", use_container_width=True):
            registry = get_registry()
            results_table = []
            prog = st.progress(0, text="Benchmarking…")

            algorithms_to_bench = [
                ("RLE", registry.get_by_name("RLE")),
                ("HUFFMAN", registry.get_by_name("HUFFMAN")),
                ("LZW", registry.get_by_name("LZW")),
                ("STORE", registry.get_by_name("STORE")),
            ]

            for i, (algo_name, algo) in enumerate(algorithms_to_bench):
                prog.progress(int((i + 0.5) / len(algorithms_to_bench) * 100), text=f"Compressing with {algo_name}…")
                try:
                    compress_result = algo.compress(bench_data)
                    # Measure decompression
                    t_decomp_start = time.perf_counter()
                    decompressed = algo.decompress(compress_result.payload, compress_result.metadata)
                    decomp_time = time.perf_counter() - t_decomp_start
                    correct = decompressed == bench_data

                    results_table.append({
                        "Algorithm": algo_name,
                        "Original": bench_size,
                        "Compressed": compress_result.compressed_size,
                        "Reduction %": compress_result.reduction_percent,
                        "Ratio": compress_result.compression_ratio,
                        "Compress ms": compress_result.duration * 1000,
                        "Decompress ms": decomp_time * 1000,
                        "Verified": "✅" if correct else "❌",
                    })
                except Exception as exc:
                    results_table.append({
                        "Algorithm": algo_name,
                        "Original": bench_size,
                        "Compressed": 0,
                        "Reduction %": 0.0,
                        "Ratio": 0.0,
                        "Compress ms": 0.0,
                        "Decompress ms": 0.0,
                        "Verified": f"❌ Error: {exc}",
                    })

            prog.progress(100, text="Done!")

            # Find best compressor
            valid = [r for r in results_table if r["Reduction %"] > 0]
            best_algo = max(valid, key=lambda r: r["Reduction %"])["Algorithm"] if valid else "STORE"

            # Render table
            rows = ""
            for r in results_table:
                is_best = r["Algorithm"] == best_algo and r["Reduction %"] > 0
                best_mark = "⭐ " if is_best else ""
                rows += f"""
                <tr>
                    <td>{best_mark}{_algo_tag(r['Algorithm'])}</td>
                    <td>{_fmt_bytes(r['Original'])}</td>
                    <td>{_fmt_bytes(r['Compressed'])}</td>
                    <td>{_fmt_pct(r['Reduction %'])}</td>
                    <td>{_fmt_ratio(r['Ratio'])}</td>
                    <td>{r['Compress ms']:.1f} ms</td>
                    <td>{r['Decompress ms']:.1f} ms</td>
                    <td>{r['Verified']}</td>
                </tr>
                """

            st.markdown(
                f"""
                <table class="styled-table">
                    <thead>
                        <tr>
                            <th>Algorithm</th><th>Original</th><th>Compressed</th>
                            <th>Reduction</th><th>Ratio</th><th>Compress</th><th>Decompress</th><th>Verified</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")
            if best_algo != "STORE":
                st.markdown(f"⭐ **{best_algo}** achieves the best compression for this file type.")
            else:
                st.markdown("📌 No compression algorithm reduced the file size. STORE is optimal for this data.")

    else:
        st.info("👆 Upload a file above to run the benchmark.")


# ──────────────────────────────────────────────────────────────────────────────
# Tab 5: Inspect Archive
# ──────────────────────────────────────────────────────────────────────────────

with tab_inspect:
    st.markdown("### 🔍 Inspect .zip Archive")
    st.markdown(
        '<div class="info-box">Inspect archive metadata and file listing <strong>without</strong> '
        "full decompression. Each entry’s SHA-256 is verified to report integrity status.</div>",
        unsafe_allow_html=True,
    )

    inspect_file = st.file_uploader(
        "Upload a .zip archive to inspect",
        type=["zip"],
        key="inspect_upload",
    )

    if inspect_file:
        inspect_bytes = inspect_file.read()
        try:
            inspection = inspect_archive(inspect_bytes)

            # Header stats
            i1, i2, i3, i4 = st.columns(4)
            _show_metrics_row(
                [i1, i2, i3, i4],
                [
                    (f"v{inspection.version}", "Format Version"),
                    (str(inspection.entry_count), "Total Files"),
                    (_fmt_bytes(inspection.total_original), "Original Size"),
                    (_fmt_pct(inspection.overall_reduction_percent), "Overall Reduction"),
                ],
            )

            st.markdown("#### 📄 Archive Contents")
            _render_entry_table(inspection.entries)

        except FileCompressorError as exc:
            st.error(f"**Cannot inspect archive:** {exc}")
            st.markdown(
                "**Possible causes:**\n"
                "- Not a valid .zip archive from this app\n"
                "- Archive entries are corrupted or truncated\n"
            )
    else:
        st.info("👆 Upload a .zip archive above to inspect its contents.")
