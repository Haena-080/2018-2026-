from pathlib import Path
import re
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =========================================================
# PAGE
# =========================================================
st.set_page_config(
    page_title="Africa Sales Performance",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data")

# =========================================================
# DESIGN
# =========================================================
BG = "#D7C9AE"
CARD = "#F2EFE8"
SIDEBAR = "#2E3033"
TEXT = "#22262D"
MUTED = "#6B6B67"
ACCENT = "#F28C45"
BAR = "#3D3F42"
GRID = "#DDD7CB"

st.markdown(
    f"""
    <style>
      .stApp {{ background: {BG}; color: {TEXT}; }}
      [data-testid="stSidebar"] {{ background: {SIDEBAR}; }}
      [data-testid="stSidebar"] * {{ color: #F7F7F7; }}
      [data-testid="stSidebar"] input {{ color: {TEXT} !important; }}
      [data-testid="stSidebar"] [data-baseweb="select"] * {{ color: {TEXT}; }}
      [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.18); }}
      .block-container {{ padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1500px; }}
      .hero {{
          background: linear-gradient(135deg, rgba(255,255,255,.27), rgba(255,255,255,.08));
          border: 1px solid rgba(255,255,255,.30);
          border-radius: 22px;
          padding: 18px 22px 10px 22px;
          margin-bottom: 12px;
      }}
      .hero h1 {{ margin: 0; font-size: 2rem; font-weight: 650; letter-spacing: -.02em; }}
      .hero p {{ margin: 2px 0 0 0; font-size: 1.06rem; font-style: italic; }}
      .kpi-card {{
          background: {CARD};
          border: 1px solid rgba(80,80,80,.10);
          border-radius: 16px;
          padding: 14px 14px 11px 14px;
          min-height: 116px;
          box-shadow: 0 1px 0 rgba(0,0,0,.02);
      }}
      .kpi-value {{ font-size: 1.72rem; font-weight: 650; line-height: 1.05; color: {TEXT}; }}
      .kpi-label {{ font-size: .88rem; color: #4F514F; margin-top: 5px; }}
      .kpi-delta {{ font-size: .76rem; color: {ACCENT}; margin-top: 7px; }}
      div[data-testid="stVerticalBlockBorderWrapper"] {{
          background: rgba(242,239,232,.90);
          border-radius: 16px;
          border-color: rgba(80,80,80,.12) !important;
      }}
      .small-note {{ color: {MUTED}; font-size: .80rem; }}
      .brand {{ font-size: 1.35rem; font-weight: 750; letter-spacing: .03em; }}
      .brand-sub {{ font-size: .83rem; opacity: .72; margin-top: -4px; }}
      .sidebar-section {{ font-weight: 650; font-size: .93rem; margin-top: .55rem; }}
      .data-note {{
          background: rgba(255,255,255,.25); border-radius: 12px; padding: 10px 12px;
          font-size: .82rem; color: #444;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# NORMALIZATION
# =========================================================
def clean_text(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def numeric_series(series):
    text = series.astype("string").fillna("")
    text = text.str.replace(",", "", regex=False).str.replace("(", "-", regex=False).str.replace(")", "", regex=False)
    return pd.to_numeric(text, errors="coerce").fillna(0.0)
