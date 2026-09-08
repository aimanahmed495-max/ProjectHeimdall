
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


FRONTEND_DIR = Path(__file__).resolve().parent
CONSOLE_PATH = FRONTEND_DIR / "heimdall_console.html"
DESIGN_CSS_PATH = FRONTEND_DIR / "assets" / "nocturne.css"

API_BASE_URL = os.getenv("HEIMDALL_API_URL", "http://localhost:8000")
WS_URL = os.getenv("HEIMDALL_WS_URL", "ws://localhost:8000/ws/events")


def build_console_html() -> str:
    """Inline local design assets and inject configurable backend addresses."""

    html = CONSOLE_PATH.read_text(encoding="utf-8")
    design_css = DESIGN_CSS_PATH.read_text(encoding="utf-8")

    html = html.replace(
        '<link rel="stylesheet" href="assets/nocturne.css">',
        f"<style>\n{design_css}\n</style>",
    )
    html = html.replace(
        '<script src="_ds/nocturne-9932346f-a3a2-45d1-8b71-183d5acca929/_ds_bundle.js"></script>',
        "",
    )
    html = html.replace("__HEIMDALL_API_URL__", json.dumps(API_BASE_URL)[1:-1])
    html = html.replace("__HEIMDALL_WS_URL__", json.dumps(WS_URL)[1:-1])
    return html


st.set_page_config(
    page_title="Heimdall Operations Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        header[data-testid="stHeader"] { display: none; }
        .stApp { background: #12141f; }
        .block-container {
            max-width: none;
            padding: 0;
        }
        iframe[title="streamlit.components.v1.html"] {
            display: block;
            border: 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

components.html(
    build_console_html(),
    height=940,
    scrolling=False,
)
