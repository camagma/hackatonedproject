"""
RescueAI — full stack in one file.
Runs a FastAPI heartbeat server in a background thread alongside Streamlit.
Volunteers ping /heartbeat from their devices; Streamlit reads the SQLite DB
to show live online status and inject it into AI assignment prompts.

Start:  GROQ_API_KEY="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" streamlit run app.py
Agent:  python agent.py --id V001 --server http://localhost:8000 --interval 30
"""

import streamlit as st
import streamlit.components.v1
import json, math, hashlib, sqlite3, threading, os, base64, secrets
from datetime import datetime, timedelta
from contextlib import contextmanager
from groq import Groq

# ── try to import FastAPI stack (optional — falls back gracefully) ─────────────
try:
    import uvicorn
    from fastapi import FastAPI, Header
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RescueAI",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "light"

APP_THEME = st.session_state.get("ui_theme", "light")
IS_DARK = APP_THEME == "dark"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root{{
  --bg:{'#0c1220' if IS_DARK else '#f6f8fc'};
  --bg2:{'#111827' if IS_DARK else '#eef2f9'};
  --surface:{'#1a2334' if IS_DARK else '#ffffff'};
  --panel:{'#131c2b' if IS_DARK else '#fafbfd'};
  --card:{'#182232' if IS_DARK else '#ffffff'};
  --card-soft:{'#1f2a3d' if IS_DARK else '#f3f6fb'};
  --input-bg:{'#1a2334' if IS_DARK else '#ffffff'};
  --border:{'rgba(148,163,184,.14)' if IS_DARK else 'rgba(15,23,42,.06)'};
  --border2:{'rgba(148,163,184,.22)' if IS_DARK else 'rgba(15,23,42,.10)'};
  --input-border:{'rgba(148,163,184,.20)' if IS_DARK else 'rgba(15,23,42,.08)'};
  --focus-ring:{'rgba(96,165,250,.22)' if IS_DARK else 'rgba(59,130,246,.14)'};
  --text:{'#f1f5f9' if IS_DARK else '#1e293b'};
  --text2:{'#cbd5e1' if IS_DARK else '#475569'};
  --text3:{'#94a3b8' if IS_DARK else '#64748b'};
  --muted:{'#64748b' if IS_DARK else '#94a3b8'};
  --red:{'#fb7185' if IS_DARK else '#e11d48'};
  --red-strong:{'#f43f5e' if IS_DARK else '#be123c'};
  --red-dim:{'rgba(251,113,133,.12)' if IS_DARK else '#fff1f3'};
  --orange:{'#fb923c' if IS_DARK else '#ea580c'};
  --orange-dim:{'rgba(251,146,60,.12)' if IS_DARK else '#fff7ed'};
  --yellow:{'#fbbf24' if IS_DARK else '#ca8a04'};
  --yellow-dim:{'rgba(251,191,36,.12)' if IS_DARK else '#fefce8'};
  --green:{'#4ade80' if IS_DARK else '#16a34a'};
  --green-dim:{'rgba(74,222,128,.12)' if IS_DARK else '#f0fdf4'};
  --blue:{'#60a5fa' if IS_DARK else '#2563eb'};
  --blue-dim:{'rgba(96,165,250,.14)' if IS_DARK else '#eff6ff'};
  --shadow:{'0 16px 40px rgba(0,0,0,.28)' if IS_DARK else '0 12px 32px rgba(15,23,42,.06)'};
  --shadow-sm:{'0 8px 20px rgba(0,0,0,.18)' if IS_DARK else '0 4px 14px rgba(15,23,42,.04)'};
  --font-head:'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-body:'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
}}

*,*::before,*::after{{box-sizing:border-box;}}
html,body,.stApp{{font-family:var(--font-body)!important;}}
.stApp{{
  background:{'linear-gradient(165deg,#0c1220 0%,#111827 48%,#0f172a 100%)' if IS_DARK else 'radial-gradient(ellipse 80% 50% at 0% -10%,rgba(37,99,235,.07),transparent),linear-gradient(180deg,var(--bg) 0%,var(--bg2) 100%)'};
  color:var(--text);
}}
#MainMenu,footer,header{{visibility:hidden;}}.stDeployButton{{display:none;}}
::-webkit-scrollbar{{width:7px;}}::-webkit-scrollbar-track{{background:var(--bg2);}}::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:999px;}}

[data-testid="stSidebar"]{{background:var(--panel)!important;border-right:1px solid var(--border)!important;box-shadow:{'none' if IS_DARK else '6px 0 28px rgba(15,23,42,.04)'};}}
[data-testid="stSidebar"]>div{{padding:0!important;}}
.main .block-container{{padding:2rem 2.5rem 3rem;max-width:1400px;}}

.stMarkdown,.stText,.stCaption,p,div,span{{color:inherit;}}
h1,h2,h3{{font-family:var(--font-head)!important;color:var(--text)!important;letter-spacing:-.03em;}}
hr{{border-color:var(--border)!important;}}
code{{background:var(--card-soft)!important;color:var(--text2)!important;border:1px solid var(--border);border-radius:7px;padding:1px 5px;}}

.stTextInput input,.stTextArea textarea,.stNumberInput input{{
  background:var(--input-bg)!important;border:1px solid var(--input-border)!important;border-radius:14px!important;color:var(--text)!important;
  font-family:var(--font-body)!important;font-size:.9rem!important;box-shadow:var(--shadow-sm)!important;
}}
.stTextInput input:focus,.stTextArea textarea:focus,.stNumberInput input:focus{{
  border-color:var(--blue)!important;box-shadow:0 0 0 4px var(--focus-ring)!important;outline:none!important;
}}
div[data-baseweb="input"]>div,
div[data-baseweb="base-input"],
.stTextInput>div>div>div,
.stTextArea>div>div>div,
.stNumberInput>div>div>div,
.stSelectbox>div>div,
.stDateInput>div>div>div,
.stTimeInput>div>div>div{{
  background:var(--input-bg)!important;border-color:var(--input-border)!important;border-radius:14px!important;
  box-shadow:var(--shadow-sm)!important;
}}
div[data-baseweb="input"]:focus-within>div,
div[data-baseweb="select"]:focus-within>div{{
  border-color:var(--blue)!important;box-shadow:0 0 0 4px var(--focus-ring)!important;
}}
.stTextInput div[data-baseweb="input"]>div,
.stTextArea div[data-baseweb="textarea"]>div,
.stNumberInput div[data-baseweb="input"]>div,
div[data-baseweb="select"]>div{{
  border:1px solid var(--input-border)!important;background:var(--input-bg)!important;
}}
.stSelectbox>div>div{{color:var(--text)!important;}}

/* Strip Streamlit/Baseweb dark wrappers around inputs */
.stTextInput>div,.stTextInput>div>div,.stTextArea>div,.stTextArea>div>div,
.stNumberInput>div,.stNumberInput>div>div{{
  background:transparent!important;border:none!important;box-shadow:none!important;
}}
.stTextInput [data-baseweb="input"],.stTextArea [data-baseweb="textarea"],
.stNumberInput [data-baseweb="input"]{{
  background:transparent!important;border:none!important;box-shadow:none!important;
}}

/* Number input container + stepper column */
[data-testid="stNumberInput"] div[data-baseweb="input"],
.stNumberInput div[data-baseweb="input"]{{
  background:var(--input-bg)!important;border:1px solid var(--input-border)!important;
  border-radius:14px!important;box-shadow:var(--shadow-sm)!important;overflow:hidden!important;
}}
[data-testid="stNumberInput"] div[data-baseweb="input"]>div,
.stNumberInput div[data-baseweb="input"]>div{{
  background:transparent!important;border:none!important;
}}
[data-testid="stNumberInput"] div[data-baseweb="input"]>div:last-child,
.stNumberInput div[data-baseweb="input"]>div:last-child{{
  background:var(--card-soft)!important;border-left:1px solid var(--input-border)!important;
}}

/* Number field +/- buttons */
[data-testid="stNumberInput"] button,
.stNumberInput button,
[data-testid="stNumberInput"] [data-baseweb="button"],
.stNumberInput [data-baseweb="button"]{{
  background:var(--card-soft)!important;color:var(--text2)!important;
  border:1px solid var(--input-border)!important;box-shadow:none!important;
}}
[data-testid="stNumberInput"] button:hover,
.stNumberInput button:hover{{
  background:var(--card)!important;color:var(--text)!important;border-color:var(--border2)!important;
}}
[data-testid="stNumberInput"] [data-baseweb="button-group"],
.stNumberInput [data-baseweb="button-group"]{{
  background:transparent!important;box-shadow:none!important;
}}

/* File uploader dropzone */
[data-testid="stFileUploader"],
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploadDropzone"],
section[data-testid="stFileUploadDropzone"]{{
  background:var(--card-soft)!important;
}}
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploadDropzone"],
section[data-testid="stFileUploadDropzone"]>div{{
  background:var(--card-soft)!important;
  border:1px dashed var(--border2)!important;border-radius:14px!important;
}}
[data-testid="stFileUploaderDropzone"] section,
[data-testid="stFileUploadDropzone"] section{{
  background:transparent!important;border:none!important;
}}
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploadDropzone"] small,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploadDropzone"] span{{
  color:var(--text3)!important;
}}
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploadDropzone"] button{{
  background:var(--card)!important;color:var(--blue)!important;
  border:1px solid var(--border2)!important;border-radius:10px!important;box-shadow:var(--shadow-sm)!important;
}}
[data-testid="stFileUploaderDropzone"] svg,
[data-testid="stFileUploadDropzone"] svg{{
  fill:var(--text3)!important;stroke:var(--text3)!important;
}}

.stApp{{color-scheme:{'dark' if IS_DARK else 'light'};}}

label,.stSelectbox label{{color:var(--text3)!important;font-size:.72rem!important;font-weight:600!important;text-transform:none!important;letter-spacing:.02em!important;}}

.stButton>button{{
  font-family:var(--font-body)!important;font-weight:600!important;border-radius:14px!important;border:1px solid var(--border)!important;
  background:var(--card)!important;color:var(--text2)!important;transition:all .18s ease!important;box-shadow:var(--shadow-sm)!important;
}}
.stButton>button:hover{{transform:translateY(-1px);border-color:var(--border2)!important;color:var(--text)!important;background:var(--card-soft)!important;}}
[data-testid="stSidebar"] .stButton>button{{
  background:transparent!important;border:none!important;box-shadow:none!important;color:var(--text2)!important;
  font-weight:600!important;padding:.55rem .75rem!important;
}}
[data-testid="stSidebar"] .stButton>button:hover{{
  background:var(--card-soft)!important;color:var(--text)!important;transform:none!important;
}}
.stTabs [data-baseweb="tab-list"]{{background:transparent!important;border-bottom:1px solid var(--border)!important;gap:6px;}}
.stTabs [data-baseweb="tab"]{{color:var(--text3)!important;font-family:var(--font-body)!important;font-weight:700!important;font-size:.86rem!important;border-bottom:2px solid transparent!important;border-radius:10px 10px 0 0;}}
.stTabs [aria-selected="true"]{{color:var(--red)!important;border-bottom-color:var(--red)!important;background:var(--red-dim)!important;}}
.stTabs [data-baseweb="tab-panel"]{{padding-top:1.5rem!important;}}
.streamlit-expanderHeader{{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:12px!important;color:var(--text2)!important;font-size:.84rem!important;box-shadow:var(--shadow-sm);}}
.streamlit-expanderContent{{background:var(--surface)!important;border:1px solid var(--border)!important;border-top:none!important;}}

.page-header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:28px;padding:22px 0 20px;border-bottom:1px solid var(--border);}}
.page-title{{font-family:var(--font-head);font-size:1.85rem;font-weight:800;letter-spacing:-.045em;line-height:1.08;color:var(--text);}}
.page-title span{{color:var(--red);}}
.page-sub{{font-size:.84rem;color:var(--text3);margin-top:7px;}}
.stats-row{{display:flex;gap:14px;margin-bottom:28px;}}
.stat-card{{flex:1;background:var(--card);border:1px solid var(--border);border-radius:20px;padding:20px 22px;position:relative;overflow:hidden;box-shadow:var(--shadow-sm);}}
.stat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;}}
.stat-card.red::before{{background:var(--red);}}.stat-card.orange::before{{background:var(--orange);}}.stat-card.green::before{{background:var(--green);}}.stat-card.blue::before{{background:var(--blue);}}
.stat-num{{font-family:var(--font-mono);font-size:2.1rem;font-weight:600;line-height:1;margin-bottom:7px;}}
.stat-card.red .stat-num{{color:var(--red);}}.stat-card.orange .stat-num{{color:var(--orange);}}.stat-card.green .stat-num{{color:var(--green);}}.stat-card.blue .stat-num{{color:var(--blue);}}
.stat-label{{font-size:.72rem;color:var(--text3);text-transform:uppercase;letter-spacing:.8px;font-weight:800;}}
.stat-trend{{font-size:.75rem;color:var(--text3);margin-top:7px;font-family:var(--font-mono);}}
.case-card{{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:18px 20px;margin-bottom:8px;position:relative;overflow:hidden;box-shadow:var(--shadow-sm);transition:all .16s ease;}}
.case-card:hover{{box-shadow:var(--shadow);transform:translateY(-1px);}}
.case-card::before{{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;}}
.case-card.critical::before{{background:var(--red);}}.case-card.high::before{{background:var(--orange);}}.case-card.medium::before{{background:var(--yellow);}}.case-card.low::before{{background:var(--green);}}
.missing-photo{{width:78px;height:78px;border-radius:18px;object-fit:cover;border:1px solid var(--border);background:var(--card-soft);box-shadow:var(--shadow-sm);flex-shrink:0;}}
.missing-photo-placeholder{{width:78px;height:78px;border-radius:18px;border:1px dashed var(--border2);background:var(--card-soft);display:flex;align-items:center;justify-content:center;color:var(--text3);font-size:1.55rem;flex-shrink:0;}}
.upload-preview-wrap{{background:var(--card-soft);border:1px solid var(--border);border-radius:16px;padding:10px;margin-top:8px;}}

.badge{{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:999px;font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.55px;}}
.badge-critical{{background:var(--red-dim);color:var(--red);border:1px solid color-mix(in srgb, var(--red) 24%, transparent);}}
.badge-high{{background:var(--orange-dim);color:var(--orange);border:1px solid color-mix(in srgb, var(--orange) 24%, transparent);}}
.badge-medium{{background:var(--yellow-dim);color:var(--yellow);border:1px solid color-mix(in srgb, var(--yellow) 24%, transparent);}}
.badge-low{{background:var(--green-dim);color:var(--green);border:1px solid color-mix(in srgb, var(--green) 24%, transparent);}}
.badge-blue{{background:var(--blue-dim);color:var(--blue);border:1px solid color-mix(in srgb, var(--blue) 24%, transparent);}}
.badge-gray{{background:var(--card-soft);color:var(--text3);border:1px solid var(--border);}}
.badge-online{{background:var(--green-dim);color:var(--green);border:1px solid color-mix(in srgb, var(--green) 24%, transparent);}}
.badge-offline{{background:var(--red-dim);color:var(--red);border:1px solid color-mix(in srgb, var(--red) 24%, transparent);}}
.badge-unknown{{background:var(--card-soft);color:var(--text3);border:1px solid var(--border);}}
.vol-card{{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:16px 18px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;gap:12px;box-shadow:var(--shadow-sm);}}
.vol-avatar{{width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.02rem;flex-shrink:0;font-family:var(--font-head);font-weight:800;}}
.vol-avatar.active{{background:var(--green-dim);color:var(--green);}}.vol-avatar.busy{{background:var(--orange-dim);color:var(--orange);}}.vol-avatar.offline{{background:var(--card-soft);color:var(--text3);}}
.notif-item{{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--blue);border-radius:14px;padding:12px 14px;margin-bottom:8px;font-family:var(--font-mono);font-size:.76rem;color:var(--text2);line-height:1.5;box-shadow:var(--shadow-sm);}}
.log-item{{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:14px 16px;margin-bottom:10px;box-shadow:var(--shadow-sm);}}
.section-head{{font-family:var(--font-head);font-size:1.12rem;font-weight:800;margin-bottom:16px;display:flex;align-items:center;gap:10px;color:var(--text);letter-spacing:-.02em;}}
.section-head::after{{content:'';flex:1;height:1px;background:var(--border);}}
.form-card{{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:24px;margin-bottom:20px;box-shadow:var(--shadow-sm);}}
.empty-state{{text-align:center;padding:60px 20px;color:var(--text3);}}
.empty-icon{{font-size:3rem;margin-bottom:12px;opacity:.55;}}.empty-text{{font-size:.9rem;}}
.sidebar-logo{{padding:24px 20px 16px;border-bottom:1px solid var(--border);margin-bottom:8px;background:linear-gradient(135deg,var(--panel) 0%,var(--card-soft) 100%);}}
.sidebar-logo-text{{font-family:var(--font-head);font-size:1.28rem;font-weight:800;color:var(--text);letter-spacing:-.04em;}}
.sidebar-logo-text span{{color:var(--red);}}
.sidebar-logo-sub{{font-size:.65rem;color:var(--text3);text-transform:uppercase;letter-spacing:1.15px;margin-top:3px;font-weight:800;}}
.side-section-label{{margin:16px 8px 8px;font-size:.65rem;color:var(--text3);text-transform:uppercase;letter-spacing:1px;font-weight:800;}}
.role-tag{{padding:5px 13px;border-radius:999px;font-size:.7rem;font-weight:800;text-transform:uppercase;letter-spacing:.8px;}}
.role-tag.volunteer{{background:var(--blue-dim);color:var(--blue);border:1px solid color-mix(in srgb, var(--blue) 22%, transparent);}}.role-tag.reporter{{background:var(--green-dim);color:var(--green);border:1px solid color-mix(in srgb, var(--green) 22%, transparent);}}

@keyframes hb-pulse{{0%{{opacity:1;}}50%{{opacity:.35;}}100%{{opacity:1;}}}}
.hb-live{{animation:hb-pulse 2s infinite;}}
.online-dot{{display:inline-block;width:7px;height:7px;border-radius:50%;flex-shrink:0;}}
.online-dot.online{{background:var(--green);box-shadow:0 0 6px color-mix(in srgb, var(--green) 50%, transparent);}}.online-dot.offline{{background:var(--red);}}.online-dot.unknown{{background:var(--text3);}}
[data-testid="stFormSubmitButton"]>button{{background:var(--red-strong)!important;color:white!important;width:100%;padding:.7rem!important;font-size:.9rem!important;border:none!important;box-shadow:0 10px 24px rgba(220,38,38,.22)!important;}}
[data-testid="stFormSubmitButton"]>button:hover{{background:#b91c1c!important;color:white!important;}}
.live-clock{{font-family:var(--font-mono);font-weight:600;color:var(--text2);}}
.address-hint{{font-size:.72rem;color:var(--text3);margin-top:4px;}}

/* ── Placeholder text visible in both themes ─────────────────── */
::placeholder{{color:var(--muted)!important;opacity:1!important;}}
input::placeholder,textarea::placeholder{{color:var(--muted)!important;opacity:1!important;font-style:italic!important;}}

/* ── Theme toggle buttons in sidebar ───────────────────────────── */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(.stButton){{
  gap:6px!important;padding:6px!important;background:var(--card-soft)!important;
  border:1px solid var(--border)!important;border-radius:16px!important;
  margin:8px 0 4px!important;
}}
/* Active (primary) theme button */
[data-testid="stSidebar"] .stButton button[kind="primaryFormSubmit"],
[data-testid="stSidebar"] .stButton button[kind="primary"]{{
  background:var(--card)!important;color:var(--text)!important;border:1px solid var(--border2)!important;
  box-shadow:{'0 2px 10px rgba(0,0,0,.20)' if IS_DARK else '0 2px 8px rgba(15,23,42,.09)'}!important;
  font-size:.84rem!important;font-weight:700!important;border-radius:11px!important;
  padding:9px 10px!important;
}}
/* Inactive (secondary) theme button */
[data-testid="stSidebar"] .stButton button[kind="secondary"]{{
  background:transparent!important;color:var(--text3)!important;border:1px solid transparent!important;
  box-shadow:none!important;font-size:.84rem!important;font-weight:600!important;
  border-radius:11px!important;padding:9px 10px!important;
}}
[data-testid="stSidebar"] .stButton button[kind="secondary"]:hover{{
  background:var(--card)!important;color:var(--text2)!important;border-color:var(--border)!important;
}}

/* ── Light-mode: force white/clean backgrounds on all inputs ─── */
.stTextInput input,.stTextArea textarea,.stNumberInput input{{
  background:var(--input-bg)!important;color:var(--text)!important;
}}
/* Selectbox dropdown text and background */
div[data-baseweb="select"] div[class*="ValueContainer"],
div[data-baseweb="select"] span,
div[data-baseweb="select"] input{{
  color:var(--text)!important;background:transparent!important;
}}
div[data-baseweb="popover"] [role="option"],
div[data-baseweb="popover"] li{{
  background:var(--surface)!important;color:var(--text)!important;
}}
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="popover"] li:hover{{
  background:var(--card-soft)!important;
}}

/* Reporter "returned" row — sits flush under case card */
.returned-panel-head{{
  font-size:.82rem;font-weight:700;color:var(--green);margin:4px 0 8px 0;
}}
.returned-panel-head + div[data-testid="stHorizontalBlock"]{{
  background:var(--green-dim)!important;border:1px solid color-mix(in srgb,var(--green) 20%,transparent)!important;
  border-radius:16px!important;padding:12px 14px 10px!important;margin-bottom:14px!important;
}}
.returned-panel-head + div[data-testid="stHorizontalBlock"] input{{
  background:var(--input-bg)!important;border-color:var(--input-border)!important;
}}
.returned-panel-head + div[data-testid="stHorizontalBlock"] [data-testid="stButton"]>button[kind="primary"]{{
  background:linear-gradient(135deg,var(--green),#22c55e)!important;color:#fff!important;
  border:none!important;border-radius:14px!important;min-height:46px!important;margin-top:0!important;
  font-weight:700!important;box-shadow:0 8px 20px rgba(22,163,74,.2)!important;
}}
.returned-panel-head + div[data-testid="stHorizontalBlock"] [data-testid="stButton"]>button[kind="primary"]:hover{{
  filter:brightness(1.04);transform:translateY(-1px);color:#fff!important;
}}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HEARTBEAT DATABASE  (SQLite, single file next to app.py)
# ═══════════════════════════════════════════════════════════════════════════════
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rescue_hb.db")
HB_TIMEOUT_MULT = 2.5       # mark offline after 2.5 × expected interval
HB_DEFAULT_INTERVAL = 30    # seconds

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hb_status (
                volunteer_id      TEXT PRIMARY KEY,
                name              TEXT,
                online_status     TEXT DEFAULT 'unknown',
                last_heartbeat    TEXT,
                hb_source         TEXT,
                hb_interval       INTEGER DEFAULT 30,
                device_id         TEXT,
                ip_address        TEXT,
                lat               REAL,
                lon               REAL,
                field_status      TEXT,
                updated_at        TEXT
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hb_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteer_id  TEXT,
                received_at   TEXT,
                source        TEXT,
                ip_address    TEXT,
                lat           REAL,
                lon           REAL,
                field_status  TEXT,
                device_id     TEXT
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_sessions (
                token      TEXT PRIMARY KEY,
                username   TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS volunteer_gps (
                vol_id     TEXT PRIMARY KEY,
                lat        REAL,
                lon        REAL,
                address    TEXT,
                updated_at TEXT
            )""")

init_db()

def db_save_vol_gps(vol_id: str, lat: float, lon: float, address: str = ""):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute("""INSERT OR REPLACE INTO volunteer_gps (vol_id, lat, lon, address, updated_at)
            VALUES (?,?,?,?,?)""", (vol_id, lat, lon, address, now))

def db_get_vol_gps(vol_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT lat, lon, address FROM volunteer_gps WHERE vol_id=?", (vol_id,)).fetchone()
    return dict(row) if row else None

def db_get_all_vol_gps() -> dict:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM volunteer_gps").fetchall()
    return {r["vol_id"]: dict(r) for r in rows}

SESSION_TTL_DAYS = 30

def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now()
    expires = now + timedelta(days=SESSION_TTL_DAYS)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO app_sessions (token, username, created_at, expires_at) VALUES (?,?,?,?)",
            (token, username, now.isoformat(), expires.isoformat())
        )
    return token

def get_session_user(token: str):
    """Returns username if token is valid and not expired, else None."""
    if not token:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT username, expires_at FROM app_sessions WHERE token=?", (token,)
        ).fetchone()
    if not row:
        return None
    if datetime.fromisoformat(row["expires_at"]) < datetime.now():
        delete_session(token)
        return None
    return row["username"]

def delete_session(token: str):
    with get_db() as conn:
        conn.execute("DELETE FROM app_sessions WHERE token=?", (token,))

def delete_user_sessions(username: str):
    with get_db() as conn:
        conn.execute("DELETE FROM app_sessions WHERE username=?", (username,))

def _compute_online(last_hb: str | None, interval: int) -> str:
    if not last_hb:
        return "unknown"
    try:
        cutoff = datetime.now() - timedelta(seconds=interval * HB_TIMEOUT_MULT)
        return "online" if datetime.fromisoformat(last_hb) >= cutoff else "offline"
    except Exception:
        return "unknown"

def db_upsert_heartbeat(vol_id: str, source: str, interval: int,
                         device_id: str | None, ip: str | None,
                         lat: float | None, lon: float | None,
                         field_status: str | None):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO hb_status
              (volunteer_id,name,online_status,last_heartbeat,hb_source,hb_interval,device_id,ip_address,lat,lon,field_status,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(volunteer_id) DO UPDATE SET
              online_status  = 'online',
              last_heartbeat = excluded.last_heartbeat,
              hb_source      = excluded.hb_source,
              hb_interval    = COALESCE(excluded.hb_interval, hb_interval),
              device_id      = COALESCE(excluded.device_id, device_id),
              ip_address     = excluded.ip_address,
              lat            = COALESCE(excluded.lat, lat),
              lon            = COALESCE(excluded.lon, lon),
              field_status   = COALESCE(excluded.field_status, field_status),
              updated_at     = excluded.updated_at
        """, (vol_id, vol_id, "online", now, source, interval, device_id, ip, lat, lon, field_status, now))
        conn.execute("""
            INSERT INTO hb_log (volunteer_id,received_at,source,ip_address,lat,lon,field_status,device_id)
            VALUES (?,?,?,?,?,?,?,?)
        """, (vol_id, now, source, ip, lat, lon, field_status, device_id))

def db_get_all_statuses() -> dict:
    """Returns {volunteer_id: {...}} with computed online_status."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM hb_status").fetchall()
    result = {}
    for r in rows:
        d = dict(r)
        d["online_status"] = _compute_online(d.get("last_heartbeat"), d.get("hb_interval") or HB_DEFAULT_INTERVAL)
        result[d["volunteer_id"]] = d
    return result

def db_get_log(vol_id: str, limit: int = 40):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM hb_log WHERE volunteer_id=? ORDER BY received_at DESC LIMIT ?",
            (vol_id, limit)).fetchall()
    return [dict(r) for r in rows]

def db_set_offline(vol_id: str):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE hb_status SET online_status='offline', updated_at=? WHERE volunteer_id=?",
                     (now, vol_id))

# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI HEARTBEAT SERVER  (runs in background thread)
# ═══════════════════════════════════════════════════════════════════════════════
FASTAPI_PORT = 8000
_server_started = False

def _start_fastapi_server():
    """Launch FastAPI in a daemon thread. Called once per Streamlit process."""
    global _server_started
    if _server_started or not HAS_FASTAPI:
        return
    _server_started = True

    fapi = FastAPI(title="RescueAI Heartbeat", version="1.0")
    fapi.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    class HBPayload(BaseModel):
        volunteer_id: str
        device_id:    Optional[str] = None
        lat:          Optional[float] = None
        lon:          Optional[float] = None
        field_status: Optional[str] = None
        interval_sec: Optional[int] = HB_DEFAULT_INTERVAL
        source:       Optional[str] = "agent"

    class RegPayload(BaseModel):
        volunteer_id: str
        name:         str
        interval_sec: Optional[int] = HB_DEFAULT_INTERVAL

    @fapi.get("/")
    def root():
        return {"service": "RescueAI Heartbeat", "time": datetime.now().isoformat()}

    @fapi.post("/heartbeat")
    def heartbeat(p: HBPayload, x_forwarded_for: Optional[str] = Header(None)):
        db_upsert_heartbeat(
            p.volunteer_id, p.source or "agent",
            p.interval_sec or HB_DEFAULT_INTERVAL,
            p.device_id, x_forwarded_for or "unknown",
            p.lat, p.lon, p.field_status
        )
        return {"ok": True, "volunteer_id": p.volunteer_id, "received_at": datetime.now().isoformat()}

    @fapi.post("/register")
    def register(d: RegPayload):
        now = datetime.now().isoformat()
        with get_db() as conn:
            conn.execute("""
                INSERT INTO hb_status (volunteer_id,name,hb_interval,updated_at)
                VALUES (?,?,?,?)
                ON CONFLICT(volunteer_id) DO UPDATE SET
                  name=excluded.name, hb_interval=excluded.hb_interval, updated_at=excluded.updated_at
            """, (d.volunteer_id, d.name, d.interval_sec, now))
        return {"ok": True}

    @fapi.get("/status")
    def status_all():
        return {"volunteers": list(db_get_all_statuses().values()),
                "fetched_at": datetime.now().isoformat()}

    @fapi.get("/status/{vol_id}")
    def status_one(vol_id: str):
        s = db_get_all_statuses()
        if vol_id not in s:
            from fastapi import HTTPException
            raise HTTPException(404, "Not found")
        return s[vol_id]

    @fapi.get("/log/{vol_id}")
    def log(vol_id: str, limit: int = 50):
        return {"volunteer_id": vol_id, "entries": db_get_log(vol_id, limit)}

    @fapi.post("/offline/{vol_id}")
    def force_offline(vol_id: str):
        db_set_offline(vol_id)
        return {"ok": True, "volunteer_id": vol_id}

    @fapi.get("/summary")
    def summary():
        statuses = [v["online_status"] for v in db_get_all_statuses().values()]
        return {"total": len(statuses), "online": statuses.count("online"),
                "offline": statuses.count("offline"), "unknown": statuses.count("unknown")}

    def _run():
        uvicorn.run(fapi, host="0.0.0.0", port=FASTAPI_PORT, log_level="error")

    t = threading.Thread(target=_run, daemon=True)
    t.start()

# Start server (Streamlit runs this file multiple times; the flag prevents duplicates)
if HAS_FASTAPI:
    _start_fastapi_server()

# ═══════════════════════════════════════════════════════════════════════════════
# HEARTBEAT HELPERS  (used by Streamlit UI)
# ═══════════════════════════════════════════════════════════════════════════════

def sync_online_status():
    """Merge DB heartbeat data into st.session_state.volunteers."""
    live = db_get_all_statuses()
    if not live:
        return
    for vol in st.session_state.volunteers:
        rec = live.get(vol["id"])
        if rec:
            vol["online_status"]    = rec["online_status"]
            vol["last_heartbeat"]   = rec.get("last_heartbeat")
            vol["hb_source"]        = rec.get("hb_source")
            vol["device_id"]        = rec.get("device_id")
            vol["ip_address"]       = rec.get("ip_address")
            if rec.get("field_status"):
                vol["field_status"] = rec["field_status"]
            if rec.get("lat") is not None and rec.get("lon") is not None:
                vol["lat"], vol["lon"] = rec["lat"], rec["lon"]
            # If server says offline → override operational status
            if rec["online_status"] == "offline" and vol["status"] == "active":
                vol["status"] = "offline"
        else:
            vol.setdefault("online_status", "unknown")

def assignable_volunteers():
    """Active volunteers who are not network-offline (safe for AI dispatch)."""
    sync_online_status()
    return [
        v for v in st.session_state.volunteers
        if v.get("status") == "active" and v.get("online_status") != "offline"
    ]

def next_volunteer_id() -> str:
    nums = []
    for v in st.session_state.volunteers:
        vid = v.get("id", "")
        if vid.startswith("V") and vid[1:].isdigit():
            nums.append(int(vid[1:]))
    return f"V{(max(nums, default=0) + 1):03d}"

def online_badge_html(vol: dict) -> str:
    """Compact inline badge showing online status + age of last ping."""
    os_ = vol.get("online_status", "unknown")
    lhb = vol.get("last_heartbeat")
    src = vol.get("hb_source", "")
    color   = {"online": "var(--green)", "offline": "var(--red-strong)", "unknown": "var(--text3)"}.get(os_, "var(--text3)")
    bg      = {"online": "var(--green-dim)", "offline": "var(--red-dim)", "unknown": "var(--card-soft)"}.get(os_, "var(--card-soft)")
    border  = {"online": "rgba(34,216,122,.25)", "offline": "rgba(255,59,59,.25)", "unknown": "rgba(100,112,120,.15)"}.get(os_, "transparent")
    label   = os_.upper()
    src_icon= {"agent": "📡", "browser": "🌐"}.get(src, "")
    ago     = ""
    if lhb:
        try:
            delta = int((datetime.now() - datetime.fromisoformat(lhb)).total_seconds())
            ago = f" {delta}s" if delta < 120 else f" {delta//60}m"
        except Exception:
            pass
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{bg};border:1px solid {border};border-radius:6px;'
        f'padding:2px 8px;font-size:.67rem;font-family:var(--font-mono);color:{color}">'
        f'<span class="online-dot {os_}"></span>{src_icon} {label}{ago}</span>'
    )

def browser_ping_js(vol_id: str) -> str:
    """JS injected into every volunteer page — pings /heartbeat with real GPS coords."""
    return f"""<script>
(function(){{
  const ID="{vol_id}", URL="http://localhost:{FASTAPI_PORT}/heartbeat";
  let lastLat=null, lastLon=null, gpsOk=false;
  function doGeoWatch(){{
    if(!navigator.geolocation)return;
    navigator.geolocation.watchPosition(
      function(pos){{ lastLat=pos.coords.latitude; lastLon=pos.coords.longitude; gpsOk=true; sendPing(); }},
      function(err){{ gpsOk=false; }},
      {{enableHighAccuracy:true, maximumAge:15000, timeout:10000}}
    );
  }}
  async function sendPing(){{
    const payload={{volunteer_id:ID, source:"browser", interval_sec:25,
      field_status:gpsOk?"📍 GPS live":"🌐 Online (no GPS)"}};
    if(lastLat!==null){{ payload.lat=lastLat; payload.lon=lastLon; }}
    try{{await fetch(URL,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(payload)}});}}catch(e){{}}
  }}
  doGeoWatch(); sendPing(); setInterval(sendPing,25000);
}})();
</script>"""

# ═══════════════════════════════════════════════════════════════════════════════
# GROQ CLIENT
# ═══════════════════════════════════════════════════════════════════════════════
client = Groq()

# ═══════════════════════════════════════════════════════════════════════════════
# USER DB
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULT_USERS = {
    "ivan":  {"password":"1234",  "role":"volunteer","name":"Ivan Petrov",    "skill":"Mountain Rescue",   "address":"Independence Square, Kyiv",      "lat":50.45,"lon":30.52,"id":"V001"},
    "sarah": {"password":"1234",  "role":"volunteer","name":"Sarah Mitchell", "skill":"Paramedic / Medic", "address":"Olympic Stadium, Kyiv",          "lat":50.43,"lon":30.55,"id":"V002"},
    "mike":  {"password":"1234",  "role":"volunteer","name":"Mike Torres",    "skill":"Dive Rescue",       "address":"Podil River Station, Kyiv",      "lat":50.47,"lon":30.48,"id":"V003"},
    "julia": {"password":"1234",  "role":"reporter", "name":"Julia Brown",    "id":None},
    "alex":  {"password":"1234",  "role":"reporter", "name":"Alex Chen",      "id":None},
    "admin": {"password":"admin", "role":"volunteer","name":"Admin",          "skill":"General Search",    "address":"Kyiv Central Station",          "lat":50.45,"lon":30.52,"id":"V004"},
}

def _init_users_table():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS app_users (
            username TEXT PRIMARY KEY,
            password TEXT, role TEXT, name TEXT,
            skill TEXT, address TEXT, lat REAL, lon REAL, vol_id TEXT
        )""")
        for uname, u in DEFAULT_USERS.items():
            conn.execute("""INSERT OR IGNORE INTO app_users
                (username,password,role,name,skill,address,lat,lon,vol_id)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (uname, u["password"], u["role"], u["name"],
                 u.get("skill"), u.get("address"), u.get("lat"), u.get("lon"), u.get("id")))

_init_users_table()

def get_users():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM app_users").fetchall()
    result = {}
    for r in rows:
        d = dict(r)
        uname = d.pop("username")
        d["id"] = d.pop("vol_id")
        result[uname] = d
    return result

def save_user(uname, u):
    with get_db() as conn:
        conn.execute("""INSERT OR REPLACE INTO app_users
            (username,password,role,name,skill,address,lat,lon,vol_id)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (uname, u.get("password"), u.get("role"), u.get("name"),
             u.get("skill"), u.get("address"), u.get("lat"), u.get("lon"), u.get("id")))

def delete_user(uname: str):
    """Delete user from DB, remove all sessions, remove from volunteers list in memory."""
    with get_db() as conn:
        conn.execute("DELETE FROM app_users WHERE username=?", (uname,))
    delete_user_sessions(uname)
    st.session_state.volunteers = [
        v for v in st.session_state.get("volunteers", [])
        if v.get("username") != uname
    ]

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def haversine(lat1,lon1,lat2,lon2):
    R=6371; phi1,phi2=math.radians(lat1),math.radians(lat2)
    dphi=math.radians(lat2-lat1); dlam=math.radians(lon2-lon1)
    a=math.sin(dphi/2)**2+math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

def get_priority(score):
    if score>=85: return "CRITICAL","critical"
    if score>=65: return "HIGH","high"
    if score>=40: return "MEDIUM","medium"
    return "LOW","low"

# ─── Weather & Time Risk ──────────────────────────────────────────────────────
WEATHER_MODIFIERS = {
    "Clear":        {"Flood":0,  "Wildfire":8,  "Mountain / Forest":0,  "Urban Area":0,  "Missing Person":0,  "Other":0},
    "Rain":         {"Flood":20, "Wildfire":-5, "Mountain / Forest":12, "Urban Area":5,  "Missing Person":8,  "Other":5},
    "Storm":        {"Flood":35, "Wildfire":5,  "Mountain / Forest":25, "Urban Area":15, "Missing Person":20, "Other":15},
    "Snow":         {"Flood":12, "Wildfire":-8, "Mountain / Forest":30, "Urban Area":10, "Missing Person":22, "Other":18},
    "Fog":          {"Flood":8,  "Wildfire":0,  "Mountain / Forest":15, "Urban Area":10, "Missing Person":15, "Other":8},
    "Extreme Heat": {"Flood":5,  "Wildfire":40, "Mountain / Forest":12, "Urban Area":12, "Missing Person":10, "Other":5},
}
WEATHER_ICONS = {"Clear":"☀️","Rain":"🌧️","Storm":"⛈️","Snow":"❄️","Fog":"🌫️","Extreme Heat":"🔥"}

def get_time_risk():
    h=datetime.now().hour
    if 21<=h or h<5: return 20,"🌙 Night"
    if 5<=h<7 or 18<=h<21: return 10,"🌆 Dusk/Dawn"
    return 0,"☀️ Daytime"

def compute_dynamic_risk(case):
    weather=st.session_state.get("weather_condition","Clear")
    w_mod=WEATHER_MODIFIERS.get(weather,{}).get(case.get("category","Other"),0)
    t_mod,t_label=get_time_risk()
    total=w_mod+t_mod
    effective=min(100,case["priority_score"]+total)
    eff_label,eff_cls=get_priority(effective)
    return {"weather":weather,"w_icon":WEATHER_ICONS.get(weather,""),"w_mod":w_mod,
            "t_mod":t_mod,"total":total,"effective":effective,
            "eff_label":eff_label,"eff_cls":eff_cls,"t_label":t_label}

# ─── Disaster Team Compositions ───────────────────────────────────────────────
DISASTER_TEAMS={
    "Flood":            {"icon":"🌊","required":["Dive Rescue"],"preferred":["Paramedic / Medic","General Search"],"size":3,"note":"Dive team + medic + support"},
    "Wildfire":         {"icon":"🔥","required":["Firefighter"],"preferred":["Paramedic / Medic","Mountain Rescue"],"size":4,"note":"Fire suppression + evacuation + medic"},
    "Mountain / Forest":{"icon":"⛰️","required":["Mountain Rescue"],"preferred":["K9 Handler","Paramedic / Medic"],"size":3,"note":"Alpine specialists + K9"},
    "Urban Area":       {"icon":"🏙️","required":["General Search"],"preferred":["Paramedic / Medic","K9 Handler"],"size":2,"note":"Search team + medic"},
    "Missing Person":   {"icon":"🔍","required":["General Search"],"preferred":["K9 Handler","Paramedic / Medic"],"size":2,"note":"Search + K9 tracker"},
    "Other":            {"icon":"🚨","required":[],"preferred":["General Search","Paramedic / Medic"],"size":2,"note":"General response team"},
}

def build_team_for_case(case, available_vols):
    """Select best volunteers by disaster type. Returns list of (vol, role_tag)."""
    spec=DISASTER_TEAMS.get(case.get("category","Other"),DISASTER_TEAMS["Other"])
    target=spec["size"]; assigned=[]; remaining=list(available_vols)
    for skill in spec["required"]:
        matches=[v for v in remaining if v["skill"]==skill]
        if matches:
            best=min(matches,key=lambda v:haversine(v['lat'],v['lon'],case['lat'],case['lon']))
            assigned.append((best,"🔴 Required")); remaining=[v for v in remaining if v["id"]!=best["id"]]
    for skill in spec["preferred"]:
        if len(assigned)>=target: break
        matches=[v for v in remaining if v["skill"]==skill]
        if matches:
            best=min(matches,key=lambda v:haversine(v['lat'],v['lon'],case['lat'],case['lon']))
            assigned.append((best,"🟡 Preferred")); remaining=[v for v in remaining if v["id"]!=best["id"]]
    while len(assigned)<target and remaining:
        best=min(remaining,key=lambda v:haversine(v['lat'],v['lon'],case['lat'],case['lon']))
        assigned.append((best,"🔵 Support")); remaining=[v for v in remaining if v["id"]!=best["id"]]
    return assigned

def time_since(dt_str):
    dt=datetime.fromisoformat(dt_str); delta=datetime.now()-dt
    h,rem=divmod(int(delta.total_seconds()),3600); m=rem//60
    return f"{h}h {m}m ago" if h>0 else f"{m}m ago"

def parse_json(raw):
    raw=raw.strip()
    if "```" in raw:
        parts=raw.split("```"); raw=parts[1] if len(parts)>1 else raw
        if raw.startswith("json"): raw=raw[4:]
    return json.loads(raw.strip())

def avatar_initials(name):
    p=name.split(); return (p[0][0]+(p[1][0] if len(p)>1 else "")).upper()

def uploaded_image_to_data_url(uploaded_file):
    """Convert Streamlit UploadedFile into an embeddable image string for cards."""
    if uploaded_file is None:
        return None
    file_bytes = uploaded_file.getvalue()
    mime = uploaded_file.type or "image/jpeg"
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


# ─── Address helpers ─────────────────────────────────────────────────────────
# The UI asks for addresses because real users do not know coordinates.
# Internally we still need coordinates for the map and distance-based dispatch.
ADDRESS_PRESETS = {
    "independence square, kyiv": (50.4501, 30.5234),
    "maidan nezalezhnosti, kyiv": (50.4501, 30.5234),
    "olympic stadium, kyiv": (50.4334, 30.5219),
    "podil river station, kyiv": (50.4721, 30.5226),
    "kyiv central station": (50.4412, 30.4882),
    "12 riverside st, springfield": (50.4600, 30.5300),
    "north riverbank, km 4": (50.4685, 30.5155),
    "south bridge, kyiv": (50.3948, 30.5975),
    "hydropark, kyiv": (50.4457, 30.5763),
    "bucharest old town": (44.4325, 26.1025),
}

DEFAULT_CENTER = (50.4501, 30.5234)

def geocode_address(address: str, default=DEFAULT_CENTER):
    """Offline demo geocoder: known demo addresses + deterministic fallback near the city center."""
    raw = (address or "").strip()
    key = raw.lower()
    if not key:
        return default
    if key in ADDRESS_PRESETS:
        return ADDRESS_PRESETS[key]
    for known, coords in ADDRESS_PRESETS.items():
        if known in key or key in known:
            return coords
    # Deterministic fallback: keeps demo markers stable without requiring paid API keys.
    h = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    lat_offset = ((h % 2000) - 1000) / 100000  # about ±1.1 km
    lon_offset = (((h // 2000) % 2000) - 1000) / 100000
    return default[0] + lat_offset, default[1] + lon_offset

def ensure_address_fields():
    defaults = {
        "V001": "Independence Square, Kyiv",
        "V002": "Olympic Stadium, Kyiv",
        "V003": "Podil River Station, Kyiv",
        "V004": "Kyiv Central Station",
    }
    for vol in st.session_state.get("volunteers", []):
        vol.setdefault("address", defaults.get(vol.get("id"), "Kyiv, Ukraine"))
        if vol.get("address") and ("lat" not in vol or "lon" not in vol):
            vol["lat"], vol["lon"] = geocode_address(vol["address"])
    for case in st.session_state.get("cases", []):
        case.setdefault("location", case.get("address", "Unknown location"))
        if "lat" not in case or "lon" not in case:
            case["lat"], case["lon"] = geocode_address(case.get("location", ""))

def live_time_html(mode="datetime"):
    initial = datetime.now().strftime("%B %d, %Y  %H:%M:%S" if mode == "datetime" else "%B %d, %Y")
    return f'<span class="live-clock" data-live-clock="{mode}">{initial}</span>'

def inject_live_clock_js():
    streamlit.components.v1.html("""
    <script>
    (function(){
      function pad(n){ return String(n).padStart(2,'0'); }
      function fmtDate(d){
        return d.toLocaleDateString('en-US', {month:'long', day:'2-digit', year:'numeric'});
      }
      function fmtDateTime(d){
        return fmtDate(d) + '  ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
      }
      function tick(){
        const doc = window.parent.document;
        doc.querySelectorAll('[data-live-clock]').forEach(function(el){
          const d = new Date();
          el.textContent = el.dataset.liveClock === 'date' ? fmtDate(d) : fmtDateTime(d);
        });
      }
      tick();
      setInterval(tick, 1000);
    })();
    </script>
    """, height=0)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════════════════════
def init_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.current_user = None
        # ── Restore session from token in query params ──
        token = st.query_params.get("session_token")
        if token:
            uname = get_session_user(token)
            if uname:
                user = get_users().get(uname)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"username": uname, **user}
                    saved_page = st.query_params.get("page", "dashboard")
                    st.session_state.active_page = saved_page
                    st.session_state._session_token = token
    if "cases" not in st.session_state:
        st.session_state.cases=[]
    if "volunteers" not in st.session_state:
        st.session_state.volunteers=[
            {"id":"V001","name":"Ivan Petrov",   "address":"Independence Square, Kyiv", "lat":50.45,"lon":30.52,"status":"active","skill":"Mountain Rescue",   "assigned":None,"username":"ivan",  "online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None},
            {"id":"V002","name":"Sarah Mitchell","address":"Olympic Stadium, Kyiv",     "lat":50.43,"lon":30.55,"status":"active","skill":"Paramedic / Medic", "assigned":None,"username":"sarah", "online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None},
            {"id":"V003","name":"Mike Torres",   "address":"Podil River Station, Kyiv", "lat":50.47,"lon":30.48,"status":"active","skill":"Dive Rescue",       "assigned":None,"username":"mike","online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None},
            {"id":"V004","name":"Admin",         "address":"Kyiv Central Station",     "lat":50.45,"lon":30.52,"status":"active","skill":"General Search",    "assigned":None,"username":"admin", "online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None},
        ]
        # Sync any extra volunteers who signed up (stored in DB)
        existing_ids = {v["id"] for v in st.session_state.volunteers}
        for uname, u in get_users().items():
            if u.get("role")=="volunteer" and u.get("id") and u["id"] not in existing_ids:
                st.session_state.volunteers.append({
                    "id":u["id"],"name":u["name"],"address":u.get("address",""),
                    "lat":u.get("lat",50.45),"lon":u.get("lon",30.52),
                    "status":"active","skill":u.get("skill","General Search"),
                    "assigned":None,"username":uname,"online_status":"unknown",
                    "last_heartbeat":None,"hb_source":None,"device_id":None})
                existing_ids.add(u["id"])
    if "notifications"  not in st.session_state: st.session_state.notifications=[]
    if "ai_log"         not in st.session_state: st.session_state.ai_log=[]
    if "next_case_id"   not in st.session_state: st.session_state.next_case_id=1
    if "active_page"    not in st.session_state: st.session_state.active_page="dashboard"
    # ── Restore volunteer GPS positions from DB ──
    saved_gps = db_get_all_vol_gps()
    for vol in st.session_state.volunteers:
        gps = saved_gps.get(vol["id"])
        if gps:
            vol["lat"] = gps["lat"]
            vol["lon"] = gps["lon"]
            if gps.get("address"):
                vol["address"] = gps["address"]

init_state()

def remove_default_demo_case():
    """Remove the old built-in demo case from existing sessions so the app starts at 0 real cases."""
    cases = st.session_state.get("cases", [])
    st.session_state.cases = [
        c for c in cases
        if not (
            c.get("id") == "C001"
            and c.get("name") == "Andrew Morris"
            and c.get("reported_by_user") == "julia"
            and "went missing during flooding" in (c.get("description") or "")
        )
    ]
    existing_ids = {c.get("id") for c in st.session_state.cases}
    for vol in st.session_state.get("volunteers", []):
        if vol.get("assigned") and vol.get("assigned") not in existing_ids:
            vol["assigned"] = None
            if vol.get("status") == "busy":
                vol["status"] = "active"
    nums = []
    for c in st.session_state.cases:
        cid = c.get("id", "")
        if cid.startswith("C") and cid[1:].isdigit():
            nums.append(int(cid[1:]))
    st.session_state.next_case_id = max(nums, default=0) + 1

remove_default_demo_case()
ensure_address_fields()
inject_live_clock_js()

# ═══════════════════════════════════════════════════════════════════════════════
# AI FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def ai_score_case(case):
    prompt=f"""You are an AI search-and-rescue coordinator. Analyze the case and return JSON only.
CASE: Name:{case['name']}, Age:{case['age']}({case['age_group']}), Category:{case['category']}
Location:{case['location']}, Description:{case['description']}, Missing:{case['time_missing']}h
Return ONLY valid JSON (no markdown):
{{"priority_score":<0-100>,"reasoning":"<2-3 sentences>","required_skills":["<s1>"],"risk_factors":["<f1>"],"recommended_action":"<action>","estimated_search_radius_km":<num>}}"""
    try:
        r=client.chat.completions.create(model="llama-3.3-70b-versatile",max_tokens=500,
            messages=[{"role":"user","content":prompt}])
        return parse_json(r.choices[0].message.content)
    except Exception:
        return {"priority_score":70,"reasoning":"Fallback score.","required_skills":["General Search"],
                "risk_factors":["Unknown"],"recommended_action":"Begin standard protocol.","estimated_search_radius_km":2}

def ai_assign_volunteer(case, available_vols):
    """Assignment prompt includes live online status — model never picks offline volunteers."""
    now=datetime.now().isoformat()
    def net_label(v):
        os_=v.get("online_status","unknown"); lhb=v.get("last_heartbeat")
        if os_=="online":
            try:
                delta=int((datetime.now()-datetime.fromisoformat(lhb)).total_seconds())
                return f"ONLINE ✅ (last ping {delta}s ago)"
            except Exception:
                return "ONLINE ✅"
        if os_=="offline": return "OFFLINE ⛔  DO NOT ASSIGN"
        return "UNKNOWN ⚠️  (no heartbeat — may be unreachable)"

    vols_info="\n".join(
        f"- ID:{v['id']} | {v['name']} | {v['skill']} | "
        f"dist:{haversine(v['lat'],v['lon'],case['lat'],case['lon']):.1f}km | "
        f"network:{net_label(v)}"
        for v in available_vols)

    prompt=f"""You are an AI search-and-rescue coordinator. Choose ONE best volunteer.

⚠️  STRICT RULE: NEVER assign a volunteer whose network status contains "OFFLINE" or "DO NOT ASSIGN".
Prefer ONLINE volunteers. Only fall back to UNKNOWN if no ONLINE volunteer exists.

CASE #{case['id']}: {case['name']}, {case['age']}yrs, {case['category']} @ {case['location']}
Priority: {case['priority_score']}/100 | Skills needed: {case.get('required_skills',[])}
Current time: {now}

VOLUNTEERS (with live network status):
{vols_info}

Return ONLY valid JSON (no markdown):
{{"volunteer_id":"<ID of chosen volunteer>","reason":"<mention network status + distance>","message_to_volunteer":"<direct dispatch message>"}}"""
    try:
        r=client.chat.completions.create(model="llama-3.3-70b-versatile",max_tokens=350,
            messages=[{"role":"user","content":prompt}])
        return parse_json(r.choices[0].message.content)
    except Exception:
        # manual fallback: never pick offline; prefer online, then unknown
        eligible = [v for v in available_vols if v.get("online_status") != "offline"]
        if not eligible:
            return {"volunteer_id": None, "reason": "No reachable volunteers (all offline).",
                    "message_to_volunteer": ""}
        online = [v for v in eligible if v.get("online_status") == "online"]
        pool = online if online else eligible
        best = min(pool, key=lambda v: haversine(v['lat'], v['lon'], case['lat'], case['lon']))
        return {"volunteer_id": best["id"], "reason": "Nearest available volunteer (AI fallback).",
                "message_to_volunteer": f"Assigned to {case['id']}. Proceed to {case['location']}."}

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def show_login():
    _,col,_=st.columns([1,2,1])
    with col:
        st.markdown("""<div style="text-align:center;padding:40px 0 28px">
          <div style="font-family:var(--font-head);font-size:2rem;font-weight:800;letter-spacing:-.5px;">
            Rescue<span style="color:var(--red-strong)">AI</span></div>
          <div style="font-size:.72rem;color:var(--text3);text-transform:uppercase;letter-spacing:1.5px;margin-top:4px;">
            Emergency Coordination Platform</div></div>""",unsafe_allow_html=True)
        tab_in,tab_up=st.tabs(["Sign In","Create Account"])

        with tab_in:
            with st.form("login_form"):
                username=st.text_input("Username",placeholder="your username")
                password=st.text_input("Password",type="password",placeholder="••••••••")
                st.markdown("""<div style="margin:14px 0 2px;font-size:.67rem;color:var(--text3);text-transform:uppercase;letter-spacing:.8px">Demo accounts (password: 1234)</div>
                <div style="font-family:var(--font-mono);font-size:.72rem;color:var(--text2);line-height:1.9;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 12px">
                  🔵 Volunteers: ivan · sarah · mike · admin<br>🟢 Reporters: julia · alex</div>""",unsafe_allow_html=True)
                sub=st.form_submit_button("Sign In →",use_container_width=True)
            if sub:
                user=get_users().get(username.lower().strip())
                if user and user["password"]==password:
                    st.session_state.logged_in=True
                    st.session_state.current_user={"username":username.lower().strip(),**user}
                    st.session_state.active_page="dashboard"
                    token = create_session(username.lower().strip())
                    st.session_state._session_token = token
                    st.query_params["session_token"] = token
                    # Register in heartbeat DB if volunteer
                    if user.get("role")=="volunteer" and user.get("id"):
                        with get_db() as conn:
                            conn.execute("""INSERT OR IGNORE INTO hb_status(volunteer_id,name,hb_interval,updated_at)
                                VALUES(?,?,?,?)""",(user["id"],user["name"],HB_DEFAULT_INTERVAL,datetime.now().isoformat()))
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with tab_up:
            with st.form("signup_form"):
                st.markdown('<div style="font-size:.78rem;color:var(--text2);margin-bottom:12px">Create a new account.</div>',unsafe_allow_html=True)
                su_name=st.text_input("Full Name *",placeholder="Jane Smith")
                su_user=st.text_input("Username *",placeholder="janesmith")
                su_pw  =st.text_input("Password *",type="password",placeholder="min 4 chars")
                su_pw2 =st.text_input("Confirm Password *",type="password",placeholder="repeat")
                su_role=st.selectbox("Role",["Reporter (report missing persons)","Volunteer (join search teams)"])
                vol_skill=None; vol_address=""
                if "Volunteer" in su_role:
                    vol_skill=st.selectbox("Specialization",["Mountain Rescue","Paramedic / Medic","Dive Rescue","K9 Handler","Forest / Wilderness","Firefighter","General Search"])
                    vol_address=st.text_input("Current address / area *",placeholder="e.g. Independence Square, Kyiv")
                    st.markdown('<div class="address-hint">Used for dispatch distance and map position. Map position is calculated automatically.</div>', unsafe_allow_html=True)
                reg=st.form_submit_button("Create Account →",use_container_width=True)
            if reg:
                users=get_users(); uname=su_user.lower().strip(); errs=[]
                if not su_name.strip(): errs.append("Full name required.")
                if not uname: errs.append("Username required.")
                if len(su_pw)<4: errs.append("Password min 4 chars.")
                if su_pw!=su_pw2: errs.append("Passwords don't match.")
                if uname in users: errs.append(f"Username '{uname}' taken.")
                if errs:
                    for e in errs: st.error(e)
                else:
                    is_vol="Volunteer" in su_role
                    if is_vol:
                        if not vol_address.strip():
                            st.error("Current address / area required for volunteers.")
                            return
                        nid=next_volunteer_id()
                        vol_lat, vol_lon = geocode_address(vol_address)
                        new_user={"password":su_pw,"role":"volunteer","name":su_name.strip(),"skill":vol_skill,"address":vol_address.strip(),"lat":vol_lat,"lon":vol_lon,"id":nid}
                        # Add to in-memory volunteers immediately (visible right away)
                        if not any(v["id"]==nid for v in st.session_state.volunteers):
                            st.session_state.volunteers.append({"id":nid,"name":su_name.strip(),"address":vol_address.strip(),"lat":vol_lat,"lon":vol_lon,"status":"active","skill":vol_skill,"assigned":None,"username":uname,"online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None})
                        with get_db() as conn:
                            conn.execute("INSERT OR IGNORE INTO hb_status(volunteer_id,name,hb_interval,updated_at) VALUES(?,?,?,?)",(nid,su_name.strip(),HB_DEFAULT_INTERVAL,datetime.now().isoformat()))
                    else:
                        new_user={"password":su_pw,"role":"reporter","name":su_name.strip(),"id":None}
                    save_user(uname, new_user)
                    st.session_state.logged_in=True
                    st.session_state.current_user={"username":uname,**new_user}
                    st.session_state.active_page="dashboard"
                    token = create_session(uname)
                    st.session_state._session_token = token
                    st.query_params["session_token"] = token
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def show_sidebar():
    u=st.session_state.current_user; role=u["role"]
    with st.sidebar:
        st.markdown('<div class="sidebar-logo"><div class="sidebar-logo-text">Rescue<span>AI</span></div><div class="sidebar-logo-sub">Operations Center</div></div>',unsafe_allow_html=True)
        st.markdown('<div class="side-section-label" style="margin-top:20px">Appearance</div>', unsafe_allow_html=True)
        cur_theme = st.session_state.get("ui_theme", "light")
        st.markdown('<div class="theme-toggle-wrap">', unsafe_allow_html=True)
        tb_col1, tb_col2 = st.columns(2)
        with tb_col1:
            light_active = cur_theme == "light"
            if st.button("☀️  Light", key="theme_light_btn", use_container_width=True,
                         type="primary" if light_active else "secondary"):
                if not light_active:
                    st.session_state.ui_theme = "light"; st.rerun()
        with tb_col2:
            dark_active = cur_theme == "dark"
            if st.button("🌙  Dark", key="theme_dark_btn", use_container_width=True,
                         type="primary" if dark_active else "secondary"):
                if not dark_active:
                    st.session_state.ui_theme = "dark"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:14px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="side-section-label">Weather Conditions</div>', unsafe_allow_html=True)
        weather_keys=list(WEATHER_ICONS.keys())
        cur_weather=st.session_state.get("weather_condition","Clear")
        w_idx=weather_keys.index(cur_weather) if cur_weather in weather_keys else 0
        new_weather=st.selectbox("Weather",weather_keys,index=w_idx,
            format_func=lambda w:f"{WEATHER_ICONS[w]} {w}",key="weather_select",label_visibility="collapsed")
        if new_weather!=cur_weather:
            st.session_state.weather_condition=new_weather; st.rerun()
        active_cases=sum(1 for c in st.session_state.cases if c.get("status") not in ["found","closed"])
        free_vols=sum(1 for v in st.session_state.volunteers if v["status"]=="active")
        online_vols=sum(1 for v in st.session_state.volunteers if v.get("online_status")=="online")
        s1,s2=st.columns(2)
        with s1: st.markdown(f'<div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center;margin:8px 0 4px"><div style="font-family:var(--font-mono);font-size:1.4rem;color:var(--red-strong);font-weight:500">{active_cases}</div><div style="font-size:.6rem;color:var(--text3);text-transform:uppercase;letter-spacing:.5px">Cases</div></div>',unsafe_allow_html=True)
        with s2: st.markdown(f'<div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center;margin:8px 0 4px"><div style="font-family:var(--font-mono);font-size:1.4rem;color:var(--green);font-weight:500">{online_vols}</div><div style="font-size:.6rem;color:var(--text3);text-transform:uppercase;letter-spacing:.5px">Online</div></div>',unsafe_allow_html=True)
        st.markdown('<div style="height:8px"></div>',unsafe_allow_html=True)
        if role=="volunteer":
            pages=[("dashboard","📡","Dashboard"),("my_missions","🎯","My Missions"),
                   ("all_cases","🗂️","All Cases"),("volunteers","👥","Volunteers"),
                   ("tracking","📡","GPS Tracking"),("ai_log","🤖","AI Log")]
            if u.get("username") == "admin":
                pages.append(("manage_users","🛠️","Manage Users"))
        else:
            pages=[("dashboard","📡","Dashboard"),("report_case","📋","Report Missing"),("my_cases","📁","My Reports")]
        for pid,icon,label in pages:
            is_active=st.session_state.active_page==pid
            if st.button(f"{'●' if is_active else '○'}  {icon}  {label}",key=f"nav_{pid}",use_container_width=True):
                st.session_state.active_page=pid
                st.query_params["page"]=pid
                st.rerun()
        if st.session_state.notifications:
            st.markdown('<div style="margin:16px 8px 6px;font-size:.65rem;color:var(--text3);text-transform:uppercase;letter-spacing:1px">Recent Dispatches</div>',unsafe_allow_html=True)
            for n in st.session_state.notifications[-3:][::-1]:
                st.markdown(f'<div class="notif-item">{n}</div>',unsafe_allow_html=True)
        st.markdown("<br>"*2,unsafe_allow_html=True)
        initials=avatar_initials(u["name"])
        rc="var(--blue)" if role=="volunteer" else "var(--green)"
        rb="var(--blue-dim)" if role=="volunteer" else "var(--green-dim)"
        st.markdown(f'<div style="border-top:1px solid var(--border);padding:14px 12px;display:flex;align-items:center;gap:10px"><div style="width:36px;height:36px;border-radius:9px;background:{rb};border:1px solid color-mix(in srgb, {rc} 28%, transparent);display:flex;align-items:center;justify-content:center;font-family:var(--font-head);font-weight:800;font-size:.85rem;color:{rc};flex-shrink:0">{initials}</div><div style="min-width:0"><div style="font-size:.85rem;font-weight:600">{u["name"]}</div><div style="font-size:.65rem;color:var(--text3);text-transform:uppercase;letter-spacing:.5px">{role}</div></div></div>',unsafe_allow_html=True)
        if st.button("Sign Out",use_container_width=True):
            # Mark offline in DB
            if u.get("role")=="volunteer" and u.get("id"):
                db_set_offline(u["id"])
            token = st.session_state.get("_session_token")
            if token:
                delete_session(token)
            st.query_params.clear()
            st.session_state.logged_in=False; st.session_state.current_user=None; st.rerun()
        # ── Delete own account ──
        is_demo = u.get("username") in {"ivan","sarah","mike","julia","alex","admin"}
        if not is_demo:
            with st.expander("⚠️ Delete my account"):
                st.warning("Permanently delete your account and sign out.")
                if st.button("🗑️ Delete my account", key="sidebar_self_delete", use_container_width=True):
                    st.session_state["confirm_self_delete"] = True
                if st.session_state.get("confirm_self_delete"):
                    st.error("This cannot be undone!")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Yes, delete", key="ssd_yes", use_container_width=True):
                            tok = st.session_state.get("_session_token")
                            if tok: delete_session(tok)
                            delete_user(u["username"])
                            st.query_params.clear()
                            st.session_state.logged_in = False
                            st.session_state.current_user = None
                            st.rerun()
                    with c2:
                        if st.button("Cancel", key="ssd_no", use_container_width=True):
                            st.session_state.pop("confirm_self_delete", None)
                            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED CARD RENDERER
# ═══════════════════════════════════════════════════════════════════════════════
def close_case_as_found(case, actor_name="Unknown", actor_role="reporter", note=""):
    """Close a case as found/returned and release assigned volunteer resources."""
    now = datetime.now()
    case["status"] = "found"
    case["found_at"] = now.isoformat()
    case["found_by"] = actor_name
    case["found_by_role"] = actor_role
    case["found_note"] = (note or "Person returned home / located safely.").strip()

    assigned_ids = []
    if case.get("assigned_to"):
        assigned_ids.append(case["assigned_to"])
    assigned_ids.extend(case.get("team_ids", []))
    assigned_ids = list(dict.fromkeys(assigned_ids))

    for vid in assigned_ids:
        v = next((x for x in st.session_state.volunteers if x["id"] == vid), None)
        if v:
            v["status"] = "active"
            v["assigned"] = None

    st.session_state.notifications.append(
        f"[{now.strftime('%H:%M')}] ✅ {case['id']} closed — {case['name']} marked found by {actor_name}"
    )
    st.session_state.ai_log.append({
        "time": now.strftime("%H:%M:%S"),
        "event": f"✅ Closed {case['id']} by {actor_role}",
        "detail": f"{case['name']} marked as found/returned. Note: {case['found_note']}",
        "score": None
    })


def reporter_found_action(case, user):
    """Reporter-only control: original reporter can close their own active case quickly."""
    if case.get("status") in ["found", "closed"]:
        return
    if case.get("reported_by_user") != user.get("username"):
        return

    st.markdown(
        '<div class="returned-panel-head">✅ Person returned — close this search</div>',
        unsafe_allow_html=True,
    )
    note_col, btn_col = st.columns([1.65, 1], gap="medium", vertical_alignment="center")
    with note_col:
        returned_note = st.text_input(
            "Details (optional)",
            placeholder="e.g. Returned home at 18:40, found near the station",
            key=f"reporter_found_note_{case['id']}",
            label_visibility="collapsed",
        )
    with btn_col:
        if st.button(
            "Close search",
            key=f"reporter_quick_found_{case['id']}",
            use_container_width=True,
            type="primary",
        ):
            close_case_as_found(
                case,
                actor_name=user.get("name", "Reporter"),
                actor_role="reporter",
                note=returned_note or "Reporter marked the person as returned / safe.",
            )
            st.success(f"Search for {case['name']} was closed. Volunteers were released.")
            st.rerun()

def render_case_card(case, show_actions=False, is_volunteer=False, reporter_user=None):
    label,cls=get_priority(case["priority_score"]); ts=time_since(case["created_at"])
    desc=(case.get("description") or "")[:120]
    desc_suffix="..." if len(case.get("description") or "")>120 else ""
    assigned_name="—"
    if case.get("assigned_to"):
        vol=next((v for v in st.session_state.volunteers if v["id"]==case["assigned_to"]),None)
        if vol: assigned_name=vol["name"]
    status_map={"new":"🆕 New","scoring":"⏳ Scoring","assigned":"👤 Assigned",
                "in_progress":"🔍 In Progress","found":"✅ Found","closed":"📁 Closed"}
    dr=compute_dynamic_risk(case)
    eff_cls=dr["eff_cls"] if dr["total"]>0 else cls
    eff_label=dr["eff_label"] if dr["total"]>0 else label
    eff_score=dr["effective"] if dr["total"]>0 else case["priority_score"]
    risk_html=f'<span style="font-size:.67rem;color:var(--orange);font-family:var(--font-mono)">{dr["w_icon"]} +{dr["total"]} pts</span>' if dr["total"]>0 else ""
    spec=DISASTER_TEAMS.get(case.get("category","Other"),DISASTER_TEAMS["Other"])
    team_tag=f'<span style="font-size:.66rem;color:var(--text3)">{spec["icon"]} {spec["note"]}</span>'
    photo=case.get("photo_data_url")
    photo_html=(
        f'<img class="missing-photo" src="{photo}" alt="Missing person photo">'
        if photo else '<div class="missing-photo-placeholder">👤</div>'
    )
    st.markdown(f"""<div class="case-card {eff_cls}">
      <div style="display:flex;gap:14px;align-items:flex-start">
        {photo_html}
        <div style="flex:1;min-width:0">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:8px">
            <div style="min-width:0">
              <div style="font-family:var(--font-head);font-weight:700;font-size:1.05rem">{case['name']}, {case['age']} yrs</div>
              <div style="font-size:.78rem;color:var(--text2);display:flex;gap:14px;flex-wrap:wrap;margin-top:4px">
                <span>📍 {case['location']}</span><span>🕐 {ts}</span><span>⚠️ {case['category']}</span><span>{team_tag}</span></div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:3px;flex-shrink:0">
              <span class="badge badge-{eff_cls}">● {eff_label} · {eff_score}</span>
              {risk_html}</div>
          </div>
          <div style="font-size:.82rem;color:var(--text3);line-height:1.5">{desc}{desc_suffix}</div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-top:10px;padding-top:8px;border-top:1px solid var(--border)">
            <div style="font-size:.78rem;color:var(--text2);font-family:var(--font-mono)">👤 {assigned_name} · {status_map.get(case.get('status','new'),case.get('status',''))}</div>
            <span class="badge badge-gray">{case['id']}</span>
          </div>
        </div>
      </div>
    </div>""",unsafe_allow_html=True)
    if show_actions and is_volunteer:
        ca,cb,cc,_=st.columns([1,1,1,2])
        with ca:
            if case.get("status") not in ["found","closed"]:
                if st.button("✅ Found",key=f"found_{case['id']}"):
                    case["status"]="found"
                    if case.get("assigned_to"):
                        v=next((x for x in st.session_state.volunteers if x["id"]==case["assigned_to"]),None)
                        if v: v["status"]="active"; v["assigned"]=None
                    for tid in case.get("team_ids",[]):
                        v=next((x for x in st.session_state.volunteers if x["id"]==tid),None)
                        if v and v["status"]=="busy": v["status"]="active"; v["assigned"]=None
                    st.session_state.notifications.append(f"[{datetime.now().strftime('%H:%M')}] ✅ {case['id']} closed — {case['name']} found!")
                    st.session_state.ai_log.append({"time":datetime.now().strftime("%H:%M:%S"),"event":f"✅ Closed {case['id']}","detail":f"{case['name']} found. Resources released.","score":None})
                    st.rerun()
        with cb:
            if case.get("status")=="new":
                if st.button("👤 Assign AI",key=f"assign_{case['id']}"):
                    available=assignable_volunteers()
                    if available:
                        with st.spinner("AI selecting..."):
                            res=ai_assign_volunteer(case,available)
                        vol=next((v for v in st.session_state.volunteers if v["id"]==res.get("volunteer_id")),None)
                        if vol:
                            vol["status"]="busy"; vol["assigned"]=case["id"]
                            case["assigned_to"]=vol["id"]; case["status"]="assigned"
                            st.session_state.notifications.append(f"[{datetime.now().strftime('%H:%M')}] 🎯 {case['id']} → {vol['name']}")
                            st.rerun()
                        else:
                            st.error("No reachable volunteer could be assigned (all offline or AI returned none).")
                    else:
                        st.error("No volunteers available (none active and online).")
        with cc:
            if case.get("status")=="new":
                if st.button("👥 Team",key=f"team_{case['id']}"):
                    available=assignable_volunteers()
                    if available:
                        team=build_team_for_case(case,available)
                        if team:
                            for vol,role in team:
                                vol["status"]="busy"; vol["assigned"]=case["id"]
                            case["assigned_to"]=team[0][0]["id"]
                            case["team_ids"]=[v["id"] for v,_ in team]
                            case["status"]="assigned"
                            names=", ".join(v["name"] for v,_ in team)
                            st.session_state.notifications.append(f"[{datetime.now().strftime('%H:%M')}] 👥 Team → {case['id']}: {names}")
                            st.session_state.ai_log.append({"time":datetime.now().strftime("%H:%M:%S"),"event":f"👥 Team assigned {case['id']}","detail":names,"score":None})
                            st.rerun()
                        else:
                            st.error("No volunteers available for team assignment.")
                    else:
                        st.error("No volunteers available.")
    if reporter_user:
        reporter_found_action(case, reporter_user)
    if case.get("reasoning"):
        with st.expander(f"🤖 AI Analysis · {case['id']}"):
            if dr["total"]>0:
                w_str=f"+{dr['w_mod']}" if dr['w_mod']>=0 else str(dr['w_mod'])
                t_str=f"+{dr['t_mod']}" if dr['t_mod']>0 else "0"
                st.markdown(f"""<div style="background:var(--orange-dim);border:1px solid rgba(249,115,22,.2);border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:.78rem;color:var(--orange)">⚡ Dynamic risk: {dr['w_icon']} {dr['weather']} ({w_str}) · {dr['t_label']} ({t_str}) = +{dr['total']} pts → Effective: <b>{dr['effective']}/100 {dr['eff_label']}</b></div>""",unsafe_allow_html=True)
            st.markdown(f"**Reasoning:** {case.get('reasoning','')}")
            c1,c2=st.columns(2)
            with c1:
                if case.get('risk_factors'): st.markdown(f"**Risk Factors:** {', '.join(case['risk_factors'])}")
                if case.get('required_skills'): st.markdown(f"**Skills:** {', '.join(case['required_skills'])}")
            with c2:
                if case.get('recommended_action'): st.markdown(f"**Action:** {case['recommended_action']}")
                if case.get('search_radius_km'): st.markdown(f"**Radius:** {case['search_radius_km']} km")
            team_ids=case.get("team_ids",[])
            if team_ids:
                team_names=[next((v["name"] for v in st.session_state.volunteers if v["id"]==tid),"?") for tid in team_ids]
                st.markdown(f"**Assigned Team {spec['icon']}:** {', '.join(team_names)}")
            else:
                req=", ".join(spec["required"]) or "Any"
                pref=", ".join(spec["preferred"][:2])
                st.markdown(f"**Recommended Team {spec['icon']}:** {spec['note']} · Required: {req} · Preferred: {pref} · Size: {spec['size']}")


# ═══════════════════════════════════════════════════════════════════════════════
# VOLUNTEER PAGES
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard_volunteer():
    sync_online_status()
    u=st.session_state.current_user
    # browser ping JS (keeps the logged-in volunteer marked online)
    my_vol=next((v for v in st.session_state.volunteers if v.get("username")==u["username"]),None)
    if my_vol and HAS_FASTAPI:
        streamlit.components.v1.html(browser_ping_js(my_vol["id"]),height=0)

    active_c=[c for c in st.session_state.cases if c.get("status") not in ["found","closed"]]
    critical_c=[c for c in active_c if c["priority_score"]>=85]
    free_v=[v for v in st.session_state.volunteers if v["status"]=="active"]
    online_v=[v for v in st.session_state.volunteers if v.get("online_status")=="online"]
    found_total=sum(1 for c in st.session_state.cases if c.get("status")=="found")

    st.markdown(f"""<div class="page-header">
      <div><div class="page-title">Operations <span>Dashboard</span></div>
        <div class="page-sub">Live overview · {live_time_html('datetime')}</div></div>
      <span class="role-tag volunteer">🔵 Volunteer</span></div>""",unsafe_allow_html=True)

    st.markdown(f"""<div class="stats-row">
      <div class="stat-card red"><div class="stat-num">{len(active_c)}</div><div class="stat-label">Active Cases</div><div class="stat-trend">{len(critical_c)} critical</div></div>
      <div class="stat-card orange"><div class="stat-num">{len(critical_c)}</div><div class="stat-label">Critical</div><div class="stat-trend">Immediate action</div></div>
      <div class="stat-card green"><div class="stat-num">{len(online_v)}</div><div class="stat-label">Online Now</div><div class="stat-trend">{len(free_v)} operationally free</div></div>
      <div class="stat-card blue"><div class="stat-num">{found_total}</div><div class="stat-label">Found Total</div><div class="stat-trend">All time resolved</div></div>
    </div>""",unsafe_allow_html=True)

    # Weather + time risk banner
    weather=st.session_state.get("weather_condition","Clear")
    t_mod,t_label=get_time_risk()
    w_icon=WEATHER_ICONS.get(weather,"")
    high_risk_cases=[c for c in active_c if compute_dynamic_risk(c)["total"]>=15]
    if weather!="Clear" or t_mod>0:
        is_severe=t_mod>=20 or weather in ["Storm","Extreme Heat"]
        risk_color="var(--red)" if is_severe else "var(--orange)"
        risk_bg="var(--red-dim)" if is_severe else "var(--orange-dim)"
        st.markdown(f'<div style="background:{risk_bg};border:1px solid rgba(249,115,22,.2);border-radius:8px;padding:10px 16px;margin-bottom:16px;font-size:.8rem;color:{risk_color}">⚡ <b>Dynamic Risk Active:</b> {w_icon} {weather} · {t_label} · {len(high_risk_cases)} case(s) with elevated effective priority</div>',unsafe_allow_html=True)
    # Server status banner
    if HAS_FASTAPI:
        st.markdown(f'<div style="background:var(--green-dim);border:1px solid rgba(34,216,122,.2);border-radius:8px;padding:10px 16px;margin-bottom:20px;font-size:.8rem;color:var(--green);font-family:var(--font-mono)">📡 Heartbeat server running on <b>:8000</b> · Field agent: <code>python agent.py --id {my_vol["id"] if my_vol else "V001"} --server http://localhost:8000</code></div>',unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:var(--red-dim);border:1px solid rgba(255,59,59,.2);border-radius:8px;padding:10px 16px;margin-bottom:20px;font-size:.8rem;color:var(--red-strong)">⚠️ Install <code>fastapi uvicorn</code> to enable heartbeat server.</div>',unsafe_allow_html=True)

    cl,cr=st.columns([3,2])
    with cl:
        st.markdown('<div class="section-head">🚨 Highest Priority Cases</div>',unsafe_allow_html=True)
        sorted_c=sorted(active_c,key=lambda c:c["priority_score"],reverse=True)
        if not sorted_c: st.markdown('<div class="empty-state"><div class="empty-icon">✅</div><div class="empty-text">No active cases</div></div>',unsafe_allow_html=True)
        for case in sorted_c[:4]: render_case_card(case,show_actions=True,is_volunteer=True)
    with cr:
        st.markdown('<div class="section-head">👥 Team Status</div>',unsafe_allow_html=True)
        for vol in st.session_state.volunteers:
            os_=vol.get("online_status","unknown")
            sc={"online":"var(--green)","offline":"var(--red-strong)","unknown":"var(--text3)"}.get(os_,"var(--text3)")
            sl={"active":"Available","busy":"On Mission","offline":"Offline"}.get(vol["status"],vol["status"])
            initials=avatar_initials(vol["name"])
            ai=next((x for x in st.session_state.cases if x["id"]==vol.get("assigned")),None)
            ainfo=f'<div style="font-size:.7rem;color:var(--text2)">→ {ai["id"]}: {ai["name"]}</div>' if ai else ""
            st.markdown(f"""<div class="vol-card">
              <div class="vol-avatar {vol['status']}">{initials}</div>
              <div style="flex:1;min-width:0">
                <div style="font-weight:600;font-size:.9rem">{vol['name']}</div>
                <div style="font-size:.75rem;color:var(--text3)">{vol['skill']}</div>{ainfo}</div>
              <div style="text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:4px">
                <div style="font-size:.78rem;font-weight:600;color:{sc}">● {sl}</div>
                {online_badge_html(vol)}</div></div>""",unsafe_allow_html=True)


def page_my_missions():
    sync_online_status()
    u=st.session_state.current_user
    my_vol=next((v for v in st.session_state.volunteers if v.get("username")==u["username"]),None)
    if my_vol and HAS_FASTAPI:
        streamlit.components.v1.html(browser_ping_js(my_vol["id"]),height=0)
    st.markdown(f"""<div class="page-header"><div><div class="page-title">My <span>Missions</span></div><div class="page-sub">Assigned to you</div></div><span class="role-tag volunteer">🔵 {u['name']}</span></div>""",unsafe_allow_html=True)
    if not my_vol: st.info("No volunteer profile found."); return
    my_cases=[c for c in st.session_state.cases if c.get("assigned_to")==my_vol["id"]]
    active_m=[c for c in my_cases if c.get("status") not in ["found","closed"]]
    done_m=[c for c in my_cases if c.get("status") in ["found","closed"]]
    sc={"active":"var(--green)","busy":"var(--yellow)","offline":"var(--red-strong)"}.get(my_vol["status"],"var(--text3)")
    st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
      <div style="width:52px;height:52px;border-radius:12px;background:var(--blue-dim);display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🧑‍🚒</div>
      <div style="flex:1"><div style="font-family:var(--font-head);font-weight:700;font-size:1.1rem">{my_vol['name']}</div>
        <div style="font-size:.78rem;color:var(--text2)">{my_vol['skill']}</div></div>
      <div style="text-align:right">
        <div style="font-size:.9rem;font-weight:600;color:{sc}">● {my_vol['status'].title()}</div>
        {online_badge_html(my_vol)}
        <div style="font-size:.72rem;color:var(--text3);margin-top:4px">{len(active_m)} active missions</div></div></div>""",unsafe_allow_html=True)
    if active_m:
        st.markdown('<div class="section-head">🔴 Active</div>',unsafe_allow_html=True)
        for c in active_m: render_case_card(c,show_actions=True,is_volunteer=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-icon">🎯</div><div class="empty-text">No active missions assigned</div></div>',unsafe_allow_html=True)
    if done_m:
        st.markdown('<div class="section-head">✅ Completed</div>',unsafe_allow_html=True)
        for c in done_m: render_case_card(c)


def page_all_cases():
    sync_online_status()
    st.markdown("""<div class="page-header"><div><div class="page-title">All <span>Cases</span></div><div class="page-sub">Complete operations log</div></div></div>""",unsafe_allow_html=True)
    active_c=[c for c in st.session_state.cases if c.get("status") not in ["found","closed"]]
    closed_c=[c for c in st.session_state.cases if c.get("status") in ["found","closed"]]
    f1,f2,_=st.columns([1,1,3])
    with f1: fs=st.selectbox("Status",["All Active","Critical only","High+","Unassigned"])
    with f2: fc=st.selectbox("Type",["All types"]+list(set(c["category"] for c in st.session_state.cases)))
    filtered=active_c
    if fs=="Critical only": filtered=[c for c in filtered if c["priority_score"]>=85]
    elif fs=="High+": filtered=[c for c in filtered if c["priority_score"]>=65]
    elif fs=="Unassigned": filtered=[c for c in filtered if not c.get("assigned_to")]
    if fc!="All types": filtered=[c for c in filtered if c["category"]==fc]
    filtered=sorted(filtered,key=lambda c:c["priority_score"],reverse=True)
    st.markdown(f'<div style="font-size:.78rem;color:var(--text3);margin-bottom:12px">{len(filtered)} shown</div>',unsafe_allow_html=True)
    for case in filtered: render_case_card(case,show_actions=True,is_volunteer=True)
    if closed_c:
        with st.expander(f"📁 Closed ({len(closed_c)})"):
            for c in closed_c:
                l,cl=get_priority(c["priority_score"])
                st.markdown(f'<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:.82rem;color:var(--text3)">✅ <b style="color:var(--text2)">{c["id"]}</b> — {c["name"]}, {c["age"]} yrs · {c["location"]}</div>',unsafe_allow_html=True)


def page_volunteers():
    sync_online_status()
    st.markdown("""<div class="page-header"><div><div class="page-title">Volunteer <span>Registry</span></div><div class="page-sub">Team management & live online status</div></div></div>""",unsafe_allow_html=True)

    # Summary online strip
    total=len(st.session_state.volunteers)
    n_online=sum(1 for v in st.session_state.volunteers if v.get("online_status")=="online")
    n_offline=sum(1 for v in st.session_state.volunteers if v.get("online_status")=="offline")
    n_unknown=total-n_online-n_offline
    st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 20px;margin-bottom:20px;display:flex;gap:24px;font-family:var(--font-mono);font-size:.8rem">
      <span style="color:var(--green)">● {n_online} online</span>
      <span style="color:var(--red-strong)">● {n_offline} offline</span>
      <span style="color:var(--text3)">● {n_unknown} unknown</span>
      <span style="color:var(--text3);margin-left:auto">last sync: {live_time_html('datetime')}</span></div>""",unsafe_allow_html=True)

    with st.expander("➕ Add Volunteer"):
        with st.form("add_vol"):
            c1,c2=st.columns(2)
            with c1:
                vn=st.text_input("Full Name")
                vs=st.selectbox("Skill",["Mountain Rescue","Paramedic / Medic","Dive Rescue","K9 Handler","Forest / Wilderness","Firefighter","General Search"])
            with c2:
                vaddr=st.text_input("Current address / area",placeholder="e.g. Hydropark, Kyiv")
                st.markdown('<div class="address-hint">No technical location numbers needed — the app converts the address internally.</div>', unsafe_allow_html=True)
            if st.form_submit_button("Add"):
                if vn and vaddr:
                    nid=next_volunteer_id()
                    vla, vlo = geocode_address(vaddr)
                    st.session_state.volunteers.append({"id":nid,"name":vn,"address":vaddr,"lat":vla,"lon":vlo,"status":"active","skill":vs,"assigned":None,"username":None,"online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None})
                    with get_db() as conn:
                        conn.execute("INSERT OR IGNORE INTO hb_status(volunteer_id,name,hb_interval,updated_at) VALUES(?,?,?,?)",(nid,vn,HB_DEFAULT_INTERVAL,datetime.now().isoformat()))
                    st.success(f"✅ {vn} added ({nid})"); st.rerun()

    st.markdown("---")
    for vol in st.session_state.volunteers:
        os_=vol.get("online_status","unknown")
        sc={"active":"var(--green)","busy":"var(--yellow)","offline":"var(--red-strong)"}.get(vol["status"],"var(--text3)")
        sl={"active":"Available","busy":"On Mission","offline":"Offline"}.get(vol["status"],vol["status"])
        lhb=vol.get("last_heartbeat"); src=vol.get("hb_source") or ""; did=vol.get("device_id") or ""
        lhb_str=lhb[:16].replace("T"," ") if lhb else "Never"
        nearby=sorted([(haversine(vol["lat"],vol["lon"],c["lat"],c["lon"]),c["id"]) for c in st.session_state.cases if c.get("status") not in ["found","closed"]])
        nearby_text=" · ".join(f"{d:.1f}km→{cid}" for d,cid in nearby[:3]) if nearby else "—"
        ai=next((x for x in st.session_state.cases if x["id"]==vol.get("assigned")),None)
        ainfo=f' · <b>{ai["id"]}</b>: {ai["name"]}' if ai else ""
        initials=avatar_initials(vol["name"])

        st.markdown(f"""<div class="vol-card" style="flex-direction:column;align-items:stretch;gap:10px">
          <div style="display:flex;align-items:center;gap:12px">
            <div class="vol-avatar {vol['status']}">{initials}</div>
            <div style="flex:1;min-width:0">
              <div style="font-weight:600">{vol['name']} <span style="color:var(--text3);font-size:.75rem">· {vol['id']}</span></div>
              <div style="font-size:.75rem;color:var(--text3)">{vol['skill']}</div></div>
            <div style="text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:5px">
              <div style="font-size:.8rem;font-weight:600;color:{sc}">● {sl}{ainfo}</div>
              {online_badge_html(vol)}</div></div>
          <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 12px;font-family:var(--font-mono);font-size:.72rem;color:var(--text3);display:grid;grid-template-columns:1fr 1fr;gap:6px">
            <span>🕐 Last ping: <b style="color:var(--text2)">{lhb_str}</b></span>
            <span>📡 Source: <b style="color:var(--text2)">{src or '—'}</b></span>
            <span>💻 Device: <b style="color:var(--text2)">{(did[:20]+'…') if len(did)>20 else did or '—'}</b></span>
            <span>⚡ Nearby: <b style="color:var(--text2)">{nearby_text}</b></span>
            <span>📍 <b style="color:var(--text2)">{vol.get('address','Unknown area')}</b></span></div></div>""",unsafe_allow_html=True)

        ca,cb,_=st.columns([1,1,4])
        if vol["status"]=="offline":
            with ca:
                if st.button("Activate",key=f"act_{vol['id']}"): vol["status"]="active"; st.rerun()
        elif vol["status"]=="active":
            with ca:
                if st.button("Set Offline",key=f"off_{vol['id']}"): vol["status"]="offline"; db_set_offline(vol["id"]); st.rerun()


def page_ai_log():
    st.markdown("""<div class="page-header"><div><div class="page-title">AI <span>Decision Log</span></div><div class="page-sub">Every AI action with online-status context</div></div></div>""",unsafe_allow_html=True)
    if not st.session_state.ai_log:
        st.markdown('<div class="empty-state"><div class="empty-icon">🤖</div><div class="empty-text">No AI decisions yet.</div></div>',unsafe_allow_html=True)
    else:
        for e in st.session_state.ai_log[::-1]:
            sb=""
            if e.get("score"):
                s=e["score"]; c="badge-critical" if s>=85 else "badge-high" if s>=65 else "badge-blue"
                sb=f'<span class="badge {c}">{s}/100</span>'
            st.markdown(f"""<div class="log-item">
              <div style="font-family:var(--font-mono);font-size:.72rem;color:var(--text3);margin-bottom:4px">[{e['time']}] {sb}</div>
              <div style="font-weight:600;font-size:.88rem;margin-bottom:4px">{e['event']}</div>
              <div style="font-size:.8rem;color:var(--text2);line-height:1.5">{e['detail']}</div></div>""",unsafe_allow_html=True)
    if st.session_state.ai_log:
        if st.button("🗑️ Clear Log"): st.session_state.ai_log=[]; st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TRACKING PAGE  (volunteer check-ins + live Leaflet map)
# ═══════════════════════════════════════════════════════════════════════════════
def page_tracking():
    sync_online_status()
    u = st.session_state.current_user
    my_vol = next((v for v in st.session_state.volunteers if v.get("username") == u["username"]), None)

    # Browser GPS ping (sends position to FastAPI heartbeat server)
    if my_vol and HAS_FASTAPI:
        streamlit.components.v1.html(browser_ping_js(my_vol["id"]), height=0)

    st.markdown("""<div class="page-header"><div><div class="page-title">Field <span>Tracking</span></div>
      <div class="page-sub">Live volunteer GPS positions · heartbeat status</div></div></div>""", unsafe_allow_html=True)

    # ── Manual GPS update for own position ────────────────────────────────────
    if my_vol:
        st.markdown('<div class="section-head">📍 My Position</div>', unsafe_allow_html=True)
        streamlit.components.v1.html(f"""
<div id="gps-bar" style="font-family:monospace;font-size:.78rem;background:var(--card,#fff);
  border:1px solid #ddd;border-radius:10px;padding:10px 14px;margin-bottom:8px;
  display:flex;align-items:center;gap:12px">
  <button id="gps-btn" onclick="startGPS()" style="background:#2563eb;color:#fff;
    border:none;border-radius:8px;padding:7px 16px;font-size:.8rem;font-weight:700;cursor:pointer">
    📍 Update my GPS
  </button>
  <span id="gps-status" style="color:#64748b">Click to send your current position to HQ</span>
</div>
<script>
function startGPS(){{
  var btn=document.getElementById('gps-btn');
  var status=document.getElementById('gps-status');
  btn.disabled=true; btn.textContent='⏳ Locating...'; status.textContent='Requesting GPS…';
  if(!navigator.geolocation){{ status.textContent='GPS not supported.'; btn.disabled=false; return; }}
  navigator.geolocation.getCurrentPosition(
    function(pos){{
      var lat=pos.coords.latitude.toFixed(6);
      var lon=pos.coords.longitude.toFixed(6);
      var acc=Math.round(pos.coords.accuracy);
      btn.textContent='✅ Position sent'; btn.style.background='#16a34a';
      status.innerHTML='<b style="color:#16a34a">📍 '+lat+', '+lon+'</b> (±'+acc+'m)';
      window.parent.postMessage({{type:'gps_fix',lat:parseFloat(lat),lon:parseFloat(lon),acc:acc}},'*');
    }},
    function(err){{
      btn.disabled=false; btn.textContent='📍 Retry';
      status.textContent='GPS error: '+err.message;
    }},
    {{enableHighAccuracy:true,timeout:15000,maximumAge:0}}
  );
}}
</script>""", height=70)

        col1, col2 = st.columns([3, 1])
        with col1:
            new_address = st.text_input("Current address / area", value=my_vol.get("address", ""),
                placeholder="e.g. North riverbank, km 4", key="gps_address_input")
        with col2:
            if st.button("💾 Save position", key="save_gps_btn", use_container_width=True):
                lat, lon = geocode_address(new_address or my_vol.get("address", ""))
                my_vol["address"] = new_address
                my_vol["lat"] = lat
                my_vol["lon"] = lon
                db_save_vol_gps(my_vol["id"], lat, lon, new_address)
                db_upsert_heartbeat(my_vol["id"], "manual", HB_DEFAULT_INTERVAL, None, None, lat, lon, "📍 Position updated")
                st.success("Position saved.")
                st.rerun()

    # ── Live map ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-head" style="margin-top:24px">🗺️ Live Positions</div>', unsafe_allow_html=True)
    map_bg    = "#1e1e1e" if IS_DARK else "#f5f7fb"
    map_card  = "#2d2d30" if IS_DARK else "#ffffff"
    map_border= "#3e3e42" if IS_DARK else "#dbe3ee"
    map_text  = "#f3f3f3" if IS_DARK else "#0f172a"
    map_text2 = "#cccccc" if IS_DARK else "#334155"
    map_text3 = "#9d9d9d" if IS_DARK else "#64748b"
    map_green, map_red, map_orange, map_yellow = "#22c55e", "#dc2626", "#f97316", "#eab308"
    tile_url  = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" if IS_DARK else "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"

    vol_markers = ""; case_markers = ""
    for vol in st.session_state.volunteers:
        os_ = vol.get("online_status", "unknown")
        color = {"online": map_green, "offline": map_red, "unknown": map_text3}.get(os_, map_text3)
        lhb = vol.get("last_heartbeat"); ts = lhb[:16].replace("T", " ") if lhb else "No ping yet"
        popup = f"{vol['name']} | {vol['skill']}<br>Address: {vol.get('address','Unknown')}<br>Status: {vol.get('field_status',vol['status'])}<br>Online: {os_}<br>Last ping: {ts}"
        fn = vol["name"].split()[0]
        vol_markers += f"""L.circleMarker([{vol['lat']},{vol['lon']}],{{radius:10,color:'{color}',fillColor:'{color}',fillOpacity:.85,weight:2}}).bindPopup('<b>{popup}</b>').addTo(map);
L.marker([{vol['lat']},{vol['lon']}],{{icon:L.divIcon({{html:'<div style="color:#fff;font-size:9px;font-weight:700;white-space:nowrap;margin-top:14px;text-shadow:0 1px 3px #000">{fn}</div>',className:'',iconAnchor:[20,0]}})}}).addTo(map);\n"""
    for c in st.session_state.cases:
        if c.get("status") not in ["found", "closed"]:
            l, cl = get_priority(c["priority_score"])
            col = {"critical": map_red, "high": map_orange, "medium": map_yellow, "low": map_green}.get(cl, map_red)
            case_markers += f"""L.circleMarker([{c['lat']},{c['lon']}],{{radius:8,color:'{col}',fillColor:'{col}',fillOpacity:.3,weight:2,dashArray:'4'}}).bindPopup('<b>{c["id"]}: {c["name"]}</b><br>{c["location"]}<br>Priority: {l}').addTo(map);\n"""

    map_html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>body{{margin:0;padding:0;background:{map_bg};}}#map{{width:100%;height:480px;border-radius:12px;}}
.leaflet-container{{background:{map_card}!important;}}</style></head><body>
<div id="map"></div><script>
var map=L.map('map',{{center:[50.45,30.52],zoom:12,preferCanvas:true}});
L.tileLayer('{tile_url}',{{attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:19}}).addTo(map);
{vol_markers}{case_markers}
var leg=L.control({{position:'bottomright'}});
leg.onAdd=function(){{var d=L.DomUtil.create('div');
d.style.cssText='background:{map_card};border:1px solid {map_border};border-radius:8px;padding:10px 14px;font-family:monospace;font-size:11px;color:{map_text2};line-height:2';
d.innerHTML='<b style="color:{map_text}">LEGEND</b><br><span style="color:{map_green}">●</span> Online &nbsp;<span style="color:{map_red}">●</span> Offline &nbsp;<span style="color:{map_text3}">●</span> Unknown<br>◌ Active case';return d;}};
leg.addTo(map);</script></body></html>"""
    streamlit.components.v1.html(map_html, height=510)

    # ── Heartbeat DB log ──────────────────────────────────────────────────────
    if my_vol:
        st.markdown('<div class="section-head" style="margin-top:24px">📡 Heartbeat Log</div>', unsafe_allow_html=True)
        log = db_get_log(my_vol["id"], limit=20)
        if log:
            st.markdown(f'<div style="font-size:.78rem;color:var(--text3);margin-bottom:10px">Last {len(log)} heartbeats for {my_vol["name"]}</div>', unsafe_allow_html=True)
            for entry in log:
                src_icon = {"agent": "📡", "browser": "🌐", "manual": "📍"}.get(entry.get("source", ""), "📡")
                st.markdown(f'''<div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:6px;font-family:var(--font-mono);font-size:.75rem;color:var(--text2);display:flex;justify-content:space-between">
                  <span>{src_icon} {entry.get("source","?")} · {(entry.get("field_status") or "—")[:35]}</span>
                  <span style="color:var(--text3)">{entry.get("received_at","")[:16].replace("T"," ")}</span></div>''', unsafe_allow_html=True)
        else:
            st.info("No heartbeats yet.")
        if HAS_FASTAPI:
            st.markdown(f'''<div style="background:var(--green-dim);border:1px solid rgba(34,216,122,.2);border-radius:8px;padding:12px 16px;margin-top:12px;font-family:var(--font-mono);font-size:.78rem;color:var(--green)">
              📡 API: POST http://localhost:{FASTAPI_PORT}/heartbeat &nbsp;·&nbsp; GET /status &nbsp;·&nbsp; GET /log/{{vol_id}}</div>''', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard_reporter():
    u=st.session_state.current_user
    my=[ c for c in st.session_state.cases if c.get("reported_by_user")==u["username"]]
    active_m=[c for c in my if c.get("status") not in ["found","closed"]]
    st.markdown(f"""<div class="page-header"><div><div class="page-title">My <span>Overview</span></div>
      <div class="page-sub">{live_time_html('date')}</div></div>
      <span class="role-tag reporter">🟢 Reporter</span></div>""",unsafe_allow_html=True)
    st.markdown(f"""<div class="stats-row">
      <div class="stat-card red"><div class="stat-num">{len(active_m)}</div><div class="stat-label">Active Reports</div><div class="stat-trend">Being searched</div></div>
      <div class="stat-card green"><div class="stat-num">{sum(1 for c in my if c.get('status')=='found')}</div><div class="stat-label">Found</div><div class="stat-trend">Resolved</div></div>
      <div class="stat-card blue"><div class="stat-num">{len(my)}</div><div class="stat-label">Total Reports</div><div class="stat-trend">All time</div></div>
    </div>""",unsafe_allow_html=True)
    if active_m:
        st.markdown('<div class="section-head">🔴 Your Active Reports</div>',unsafe_allow_html=True)
        for c in sorted(active_m,key=lambda x:x["priority_score"],reverse=True):
            render_case_card(c, reporter_user=u)
    else:
        st.markdown('<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-text">No active reports. Use "Report Missing" to submit.</div></div>',unsafe_allow_html=True)
    with st.expander("📡 System Status"):
        sync_online_status()
        fv=sum(1 for v in st.session_state.volunteers if v["status"]=="active")
        bv=sum(1 for v in st.session_state.volunteers if v["status"]=="busy")
        ov=sum(1 for v in st.session_state.volunteers if v.get("online_status")=="online")
        st.markdown(f'<div style="font-size:.82rem;color:var(--text2);line-height:2.2;font-family:var(--font-mono)">🟢 {fv} volunteers free &nbsp;·&nbsp; 🟡 {bv} on mission &nbsp;·&nbsp; 📡 {ov} online &nbsp;·&nbsp; 🚨 {sum(1 for c in st.session_state.cases if c.get("status") not in ["found","closed"])} active cases</div>',unsafe_allow_html=True)


def page_report_case():
    u=st.session_state.current_user
    st.markdown("""<div class="page-header"><div><div class="page-title">Report <span>Missing Person</span></div>
      <div class="page-sub">AI analyzes and dispatches immediately</div></div></div>""",unsafe_allow_html=True)
    with st.form("new_case_form",clear_on_submit=True):
        st.markdown("#### Person Details")
        c1,c2=st.columns(2)
        with c1:
            name=st.text_input("Full Name *",placeholder="John Smith")
            age=st.number_input("Age *",min_value=0,max_value=120,value=25)
            age_group=st.selectbox("Age Group",["Child (under 12)","Teen (12-17)","Adult (18-60)","Senior (60+)"])
            category=st.selectbox("Emergency Type *",["Flood","Wildfire","Mountain / Forest","Urban Area","Missing Person","Other"])
            photo_file=st.file_uploader("Photo of Missing Person",type=["png","jpg","jpeg","webp"],help="Upload a clear photo if available.")
            if photo_file:
                st.image(photo_file,caption="Uploaded photo preview",width=180)
        with c2:
            location=st.text_input("Last Known Address / Area *",placeholder="e.g. 12 Riverside St, Springfield")
            st.markdown('<div class="address-hint">Enter an address, landmark, or area. RescueAI calculates the map position automatically.</div>', unsafe_allow_html=True)
            time_missing=st.number_input("Hours Missing *",min_value=0.0,max_value=168.0,value=1.0,step=0.5)
            phone=st.text_input("Your Phone",placeholder="+1-555-...")
        description=st.text_area("Circumstances *",placeholder="Where last seen, clothing, features...",height=110)
        submitted=st.form_submit_button("🤖 Submit & Run AI Analysis",use_container_width=True)
    if submitted and name and location and description:
        cid=f"C{st.session_state.next_case_id:03d}"; st.session_state.next_case_id+=1
        lat, lon = geocode_address(location)
        photo_data_url=uploaded_image_to_data_url(photo_file)
        new_case={"id":cid,"name":name,"age":age,"age_group":age_group,"category":category,
            "photo_data_url":photo_data_url,
            "location":location,"lat":lat,"lon":lon,"description":description,
            "reporter":u["name"],"phone":phone or "—","time_missing":time_missing,
            "priority_score":50,"status":"scoring","assigned_to":None,
            "reported_by_user":u["username"],"created_at":datetime.now().isoformat()}
        prog=st.progress(0,text="🤖 Analyzing...")
        ai_result=ai_score_case(new_case)
        prog.progress(50,text="🎯 Finding volunteer...")
        new_case.update({"priority_score":ai_result["priority_score"],"reasoning":ai_result["reasoning"],
            "required_skills":ai_result.get("required_skills",[]),"risk_factors":ai_result.get("risk_factors",[]),
            "recommended_action":ai_result.get("recommended_action",""),
            "search_radius_km":ai_result.get("estimated_search_radius_km",2),"status":"new"})
        st.session_state.ai_log.append({"time":datetime.now().strftime("%H:%M:%S"),
            "event":f"📊 Case {cid} scored","detail":ai_result["reasoning"],"score":ai_result["priority_score"]})
        available=assignable_volunteers()
        if available:
            res=ai_assign_volunteer(new_case,available)
            vol=next((v for v in st.session_state.volunteers if v["id"]==res.get("volunteer_id")),None)
            if vol:
                vol["status"]="busy"; vol["assigned"]=cid
                new_case["assigned_to"]=vol["id"]; new_case["status"]="assigned"
                st.session_state.notifications.append(f"[{datetime.now().strftime('%H:%M')}] 🎯 {cid} → {vol['name']}: {res['message_to_volunteer'][:70]}...")
                st.session_state.ai_log.append({"time":datetime.now().strftime("%H:%M:%S"),
                    "event":f"👤 Assigned {cid} → {vol['name']} (online:{vol.get('online_status','?')})","detail":res["reason"],"score":None})
        st.session_state.cases.append(new_case); prog.progress(100,text="✅ Done!")
        label,cls=get_priority(new_case["priority_score"])
        av=next((v for v in st.session_state.volunteers if v["id"]==new_case.get("assigned_to")),None)
        st.success(f"✅ Case **{cid}** submitted")
        st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin:16px 0">
          <div style="font-family:var(--font-head);font-weight:700;margin-bottom:12px">AI Result</div>
          <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px">
            <span class="badge badge-{cls}">{label} ({new_case['priority_score']}/100)</span>
            {'<span class="badge badge-blue">👤 '+av["name"]+' '+online_badge_html(av)+'</span>' if av else '<span class="badge badge-gray">No volunteer</span>'}
          </div>
          <div style="font-size:.82rem;color:var(--text2);line-height:1.6">{ai_result['reasoning']}</div></div>""",unsafe_allow_html=True)
    elif submitted:
        st.warning("Fill in all required fields (*).")


def page_my_cases_reporter():
    u=st.session_state.current_user
    st.markdown("""<div class="page-header"><div><div class="page-title">My <span>Reports</span></div></div>
      <span class="role-tag reporter">🟢 Reporter</span></div>""",unsafe_allow_html=True)
    my=[c for c in st.session_state.cases if c.get("reported_by_user")==u["username"]]
    if not my:
        st.markdown('<div class="empty-state"><div class="empty-icon">📁</div><div class="empty-text">No reports yet.</div></div>',unsafe_allow_html=True); return
    active=sorted([c for c in my if c.get("status") not in ["found","closed"]],key=lambda c:c["priority_score"],reverse=True)
    done=[c for c in my if c.get("status") in ["found","closed"]]
    if active:
        st.markdown('<div class="section-head">🔴 Active</div>',unsafe_allow_html=True)
        for c in active:
            render_case_card(c, reporter_user=u)
    if done:
        st.markdown('<div class="section-head">✅ Resolved</div>',unsafe_allow_html=True)
        for c in done: render_case_card(c)

# ═══════════════════════════════════════════════════════════════════════════════
# MANAGE USERS PAGE  (admin only — username == "admin")
# ═══════════════════════════════════════════════════════════════════════════════
def page_manage_users():
    u = st.session_state.current_user
    st.markdown("""<div class="page-header"><div><div class="page-title">Manage <span>Accounts</span></div>
      <div class="page-sub">Delete users from the platform</div></div>
      <span class="role-tag">🛠️ Admin</span></div>""", unsafe_allow_html=True)

    all_users = get_users()
    DEFAULT_PROTECTED = {"ivan", "sarah", "mike", "julia", "alex", "admin"}

    if not all_users:
        st.info("No users found.")
        return

    for uname, udata in sorted(all_users.items()):
        is_self = uname == u["username"]
        is_protected = uname in DEFAULT_PROTECTED
        role_tag = "🔵 Volunteer" if udata.get("role") == "volunteer" else "🟢 Reporter"
        cols = st.columns([3, 1])
        with cols[0]:
            you_badge = '&nbsp; <span style="font-size:.72rem;color:var(--orange)">(you)</span>' if is_self else ""
            demo_badge = '&nbsp; <span style="font-size:.72rem;color:var(--text3)">[demo account]</span>' if is_protected else ""
            uname_display = udata.get("name", "?")
            st.markdown(
                f'<div style="background:var(--card);border:1px solid var(--border);border-radius:14px;'
                f'padding:14px 18px;margin-bottom:6px">'
                f'<span style="font-weight:700">{uname_display}</span> '
                f'<code style="font-size:.75rem">@{uname}</code> &nbsp; '
                f'<span style="font-size:.75rem;color:var(--text3)">{role_tag}</span>'
                f'{you_badge}{demo_badge}'
                f'</div>',
                unsafe_allow_html=True,
            )
        with cols[1]:
            if is_self or is_protected:
                st.button("🔒 Protected", key=f"del_{uname}", disabled=True, use_container_width=True)
            else:
                if st.button(f"🗑️ Delete", key=f"del_{uname}", use_container_width=True, type="secondary"):
                    st.session_state[f"confirm_delete_{uname}"] = True

        if st.session_state.get(f"confirm_delete_{uname}"):
            st.warning(f"⚠️ Delete **@{uname}** ({udata.get('name','?')})? This cannot be undone.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, delete", key=f"yes_{uname}", use_container_width=True):
                    delete_user(uname)
                    st.session_state.pop(f"confirm_delete_{uname}", None)
                    st.success(f"Account @{uname} deleted.")
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"no_{uname}", use_container_width=True):
                    st.session_state.pop(f"confirm_delete_{uname}", None)
                    st.rerun()


# ─── Self-delete (any user can delete their own account) ───────────────────────
def section_delete_own_account():
    u = st.session_state.current_user
    uname = u["username"]
    is_demo = uname in {"ivan", "sarah", "mike", "julia", "alex", "admin"}
    st.markdown("---")
    with st.expander("⚠️ Delete my account"):
        if is_demo:
            st.info("Demo accounts cannot be deleted.")
            return
        st.warning("This will permanently delete your account and sign you out.")
        if st.button("🗑️ Delete my account", key="self_delete_btn", use_container_width=True):
            st.session_state["confirm_self_delete"] = True
        if st.session_state.get("confirm_self_delete"):
            st.error("Are you sure? This cannot be undone.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, delete permanently", key="self_delete_yes", use_container_width=True):
                    token = st.session_state.get("_session_token")
                    if token:
                        delete_session(token)
                    delete_user(uname)
                    st.query_params.clear()
                    st.session_state.logged_in = False
                    st.session_state.current_user = None
                    st.rerun()
            with c2:
                if st.button("Cancel", key="self_delete_no", use_container_width=True):
                    st.session_state.pop("confirm_self_delete", None)
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    show_login()
else:
    show_sidebar()
    u=st.session_state.current_user; role=u["role"]; page=st.session_state.active_page
    if role=="volunteer":
        if page=="dashboard":     page_dashboard_volunteer()
        elif page=="my_missions": page_my_missions()
        elif page=="all_cases":   page_all_cases()
        elif page=="volunteers":  page_volunteers()
        elif page=="tracking":    page_tracking()
        elif page=="ai_log":      page_ai_log()
        elif page=="manage_users": page_manage_users()
        else: page_dashboard_volunteer()
    else:
        if page=="dashboard":     page_dashboard_reporter()
        elif page=="report_case": page_report_case()
        elif page=="my_cases":    page_my_cases_reporter()
        else: page_dashboard_reporter()
    # Delete own account option available on all pages via sidebar expander
    # (rendered inside sidebar by show_sidebar already if we wire it there)