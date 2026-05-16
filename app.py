"""
FindFirst — full stack in one file.
Runs a FastAPI heartbeat server in a background thread alongside Streamlit.
Volunteers ping /heartbeat from their devices; Streamlit reads the SQLite DB
to show live online status and inject it into AI assignment prompts.

Start:  streamlit run app.py
AI:     optional GROQ_API_KEY="gsk_..." for live Groq scoring/assignment.
Agent:  python agent.py --id V001 --server http://localhost:8000 --interval 30
"""

import streamlit as st
import streamlit.components.v1
import json, math, hashlib, sqlite3, threading, os, base64, socket, secrets, hmac, urllib.request, urllib.parse
from datetime import datetime, timedelta
from contextlib import contextmanager
from groq import Groq

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from streamlit_geolocation import streamlit_geolocation
    HAS_STREAMLIT_GEOLOCATION = True
except ImportError:
    HAS_STREAMLIT_GEOLOCATION = False

try:
    import folium
    from streamlit_folium import st_folium
    HAS_STREAMLIT_FOLIUM = True
except ImportError:
    HAS_STREAMLIT_FOLIUM = False

                                                                                 
try:
    import uvicorn
    from fastapi import FastAPI, Header
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

                                                                                 
st.set_page_config(
    page_title="FindFirst",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

ST_FRAGMENT = getattr(st, "fragment", None)
if ST_FRAGMENT is None:
    def ST_FRAGMENT(func=None, **kwargs):
        if func is None:
            return lambda f: f
        return func
CASES_REFRESH_INTERVAL = "5s"

def rerun_current_scope():
    try:
        st.rerun(scope="fragment")
    except Exception:
        st.rerun()

                                                                                 
               
                                                                                 
if "ui_theme" not in st.session_state:
    qp_theme = st.query_params.get("theme", "dark")
    st.session_state.ui_theme = qp_theme if qp_theme in ("light", "dark") else "dark"

APP_THEME = st.session_state.get("ui_theme", "light")
IS_DARK = APP_THEME == "dark"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800&family=Syne:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root{{
  --bg:{'#000000' if IS_DARK else '#F6F1E8'};
  --bg2:{'#000000' if IS_DARK else '#ECE5D8'};
  --surface:{'#000000' if IS_DARK else '#FFFCF5'};
  --panel:{'#000000' if IS_DARK else '#F4ECDF'};
  --card:{'#000000' if IS_DARK else '#FFFCF5'};
  --card-soft:{'#080808' if IS_DARK else '#EFE6D7'};
  --input-bg:{'#000000' if IS_DARK else '#FFFCF5'};
  --border:{'rgba(255,255,255,.11)' if IS_DARK else 'rgba(95,83,65,.12)'};
  --border2:{'rgba(255,255,255,.18)' if IS_DARK else 'rgba(95,83,65,.20)'};
  --input-border:{'rgba(255,255,255,.15)' if IS_DARK else 'rgba(95,83,65,.16)'};
  --focus-ring:{'rgba(110,173,122,.20)' if IS_DARK else 'rgba(78,138,96,.16)'};
  --text:{'#F2F1EA' if IS_DARK else '#1F211D'};
  --text2:{'#CDD4C8' if IS_DARK else '#4C5048'};
  --text3:{'#8F9B8D' if IS_DARK else '#6D7168'};
  --muted:{'#8F9B8D' if IS_DARK else '#7B776D'};
  --red:{'#D9825B' if IS_DARK else '#B95F42'};
  --red-strong:{'#E39166' if IS_DARK else '#9F4D36'};
  --red-dim:{'rgba(217,130,91,.16)' if IS_DARK else 'rgba(185,95,66,.11)'};
  --orange:{'#C9863A' if IS_DARK else '#A96835'};
  --orange-dim:{'rgba(201,134,58,.15)' if IS_DARK else 'rgba(169,104,53,.12)'};
  --yellow:{'#D6B85A' if IS_DARK else '#A9862B'};
  --yellow-dim:{'rgba(214,184,90,.15)' if IS_DARK else 'rgba(169,134,43,.12)'};
  --green:{'#6EAD7A' if IS_DARK else '#4E8A60'};
  --green-dim:{'rgba(110,173,122,.15)' if IS_DARK else 'rgba(78,138,96,.12)'};
  --blue:{'#6A95A8' if IS_DARK else '#4E7D93'};
  --blue-dim:{'rgba(106,149,168,.15)' if IS_DARK else 'rgba(78,125,147,.12)'};
  --shadow:{'0 16px 40px rgba(0,0,0,.28)' if IS_DARK else '0 12px 32px rgba(15,23,42,.06)'};
  --shadow-sm:{'0 8px 20px rgba(0,0,0,.18)' if IS_DARK else '0 4px 14px rgba(15,23,42,.04)'};
  --font-head:'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-body:'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
}}

*,*::before,*::after{{box-sizing:border-box;}}
html,body,.stApp{{font-family:var(--font-body)!important;}}
.stApp{{
  background:{'#000000' if IS_DARK else 'linear-gradient(180deg,var(--bg) 0%,var(--bg2) 100%)'};
  color:var(--text);
}}
#MainMenu,footer{{visibility:hidden;}}.stDeployButton{{display:none;}}
header{{visibility:visible!important;background:transparent!important;}}
header [data-testid="stToolbar"]{{visibility:visible!important;}}
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


.stTextInput>div,.stTextInput>div>div,.stTextArea>div,.stTextArea>div>div,
.stNumberInput>div,.stNumberInput>div>div{{
  background:transparent!important;border:none!important;box-shadow:none!important;
}}
.stTextInput [data-baseweb="input"],.stTextArea [data-baseweb="textarea"],
.stNumberInput [data-baseweb="input"]{{
  background:transparent!important;border:none!important;box-shadow:none!important;
}}


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
.missing-photo-context{{filter:saturate(.82) contrast(.96);}}
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
[data-testid="stFormSubmitButton"]>button:hover{{background:#9F4D36!important;color:white!important;}}
.live-clock{{font-family:var(--font-mono);font-weight:600;color:var(--text2);}}
.address-hint{{font-size:.72rem;color:var(--text3);margin-top:4px;}}


::placeholder{{color:var(--muted)!important;opacity:1!important;}}
input::placeholder,textarea::placeholder{{color:var(--muted)!important;opacity:1!important;font-style:italic!important;}}


.theme-toggle-wrap + div[data-testid="stHorizontalBlock"],
.theme-toggle-wrap [data-testid="stHorizontalBlock"]{{
  gap:6px!important;padding:5px!important;background:var(--card-soft)!important;
  border:1px solid var(--border)!important;border-radius:16px!important;margin-bottom:10px!important;
}}

[data-testid="stSidebar"] .theme-toggle-wrap + div [data-testid="stHorizontalBlock"]{{
  background:var(--card-soft)!important;border:1px solid var(--border)!important;
  border-radius:16px!important;padding:5px!important;gap:6px!important;
}}

[data-testid="stSidebar"] .stButton button[kind="primaryFormSubmit"],
[data-testid="stSidebar"] .stButton button[kind="primary"]{{
  background:var(--card)!important;color:var(--text)!important;border:1px solid var(--border2)!important;
  box-shadow:{'0 2px 10px rgba(0,0,0,.20)' if IS_DARK else '0 2px 8px rgba(15,23,42,.09)'}!important;
  font-size:.84rem!important;font-weight:700!important;border-radius:11px!important;
  padding:9px 10px!important;
}}

[data-testid="stSidebar"] .stButton button[kind="secondary"]{{
  background:transparent!important;color:var(--text3)!important;border:1px solid transparent!important;
  box-shadow:none!important;font-size:.84rem!important;font-weight:600!important;
  border-radius:11px!important;padding:9px 10px!important;
}}
[data-testid="stSidebar"] .stButton button[kind="secondary"]:hover{{
  background:var(--card)!important;color:var(--text2)!important;border-color:var(--border)!important;
}}


.stTextInput input,.stTextArea textarea,.stNumberInput input{{
  background:var(--input-bg)!important;color:var(--text)!important;
}}

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
  background:linear-gradient(135deg,var(--green),#5F9B6B)!important;color:#fff!important;
  border:none!important;border-radius:14px!important;min-height:46px!important;margin-top:0!important;
  font-weight:700!important;box-shadow:0 8px 20px rgba(22,163,74,.2)!important;
}}
.returned-panel-head + div[data-testid="stHorizontalBlock"] [data-testid="stButton"]>button[kind="primary"]:hover{{
  filter:brightness(1.04);transform:translateY(-1px);color:#fff!important;
}}


:root{{
  --bg:{'#000000' if IS_DARK else '#F6F1E8'};
  --bg2:{'#000000' if IS_DARK else '#ECE5D8'};
  --surface:{'#000000' if IS_DARK else '#FFFCF5'};
  --panel:{'#000000' if IS_DARK else '#F4ECDF'};
  --card:{'#000000' if IS_DARK else '#FFFCF5'};
  --card-soft:{'#080808' if IS_DARK else '#EFE6D7'};
  --input-bg:{'#000000' if IS_DARK else '#FFFCF5'};
  --border:{'#1F1F1F' if IS_DARK else '#D5C9B8'};
  --border2:{'#303030' if IS_DARK else '#BFAF99'};
  --input-border:{'#262626' if IS_DARK else '#D5C9B8'};
  --focus-ring:{'rgba(110,173,122,.20)' if IS_DARK else 'rgba(78,138,96,.16)'};
  --text:{'#F2F1EA' if IS_DARK else '#1F211D'};
  --text2:{'#CDD4C8' if IS_DARK else '#4C5048'};
  --text3:{'#8F9B8D' if IS_DARK else '#6D7168'};
  --muted:{'#8F9B8D' if IS_DARK else '#7B776D'};
  --red:{'#D9825B' if IS_DARK else '#B95F42'};
  --red-strong:{'#E39166' if IS_DARK else '#9F4D36'};
  --red-dim:{'rgba(217,130,91,.16)' if IS_DARK else 'rgba(185,95,66,.11)'};
  --orange:{'#C9863A' if IS_DARK else '#A96835'};
  --orange-dim:{'rgba(201,134,58,.15)' if IS_DARK else 'rgba(169,104,53,.12)'};
  --yellow:{'#D6B85A' if IS_DARK else '#A9862B'};
  --yellow-dim:{'rgba(214,184,90,.15)' if IS_DARK else 'rgba(169,134,43,.12)'};
  --green:{'#6EAD7A' if IS_DARK else '#4E8A60'};
  --green-dim:{'rgba(110,173,122,.15)' if IS_DARK else 'rgba(78,138,96,.12)'};
  --blue:{'#6A95A8' if IS_DARK else '#4E7D93'};
  --blue-dim:{'rgba(106,149,168,.15)' if IS_DARK else 'rgba(78,125,147,.12)'};
  --shadow:{'0 18px 44px rgba(0,0,0,.28)' if IS_DARK else '0 18px 44px rgba(10,10,10,.08)'};
  --shadow-sm:{'0 8px 24px rgba(0,0,0,.18)' if IS_DARK else '0 8px 24px rgba(10,10,10,.045)'};
  --font-head:'Syne', 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-body:'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}
.stApp{{
  background:{'#000000' if IS_DARK else 'linear-gradient(180deg,#F6F1E8 0%,#ECE5D8 100%)'}!important;
}}
[data-testid="stSidebar"]{{
  background:var(--panel)!important;
  border-right:1px solid var(--border)!important;
  box-shadow:{'none' if IS_DARK else '8px 0 32px rgba(10,10,10,.055)'}!important;
}}
.main .block-container{{max-width:1420px;}}
.page-header{{
  margin-bottom:26px;
  padding:18px 0 20px;
  border-bottom:1px solid var(--border);
}}
.page-title{{
  font-family:var(--font-head)!important;
  font-size:1.95rem;
  font-weight:800;
  letter-spacing:-.035em;
}}
.page-title span,.sidebar-logo-text span{{color:var(--red)!important;}}
.page-sub{{font-family:var(--font-mono);font-size:.78rem;color:var(--text3);}}
.stat-card{{
  border-radius:14px;
  border-color:var(--border);
  padding:18px 20px;
  box-shadow:none;
}}
.stat-card:hover{{box-shadow:var(--shadow-sm);}}
.stat-card::before{{height:3px;}}
.stat-label,.stat-trend{{font-family:var(--font-mono);}}
.stat-label{{font-size:.67rem;letter-spacing:.9px;}}
.case-card{{
  border-radius:14px;
  border-left:4px solid transparent;
  padding:17px 18px;
  box-shadow:none;
}}
.case-card::before{{display:none;}}
.case-card.critical{{border-left-color:var(--red);}}
.case-card.high{{border-left-color:var(--orange);}}
.case-card.medium{{border-left-color:var(--yellow);}}
.case-card.low{{border-left-color:var(--green);}}
.case-card:hover{{
  transform:translateY(-1px);
  box-shadow:var(--shadow-sm);
  border-top-color:var(--border2);
  border-right-color:var(--border2);
  border-bottom-color:var(--border2);
}}
.missing-photo{{
  width:78px;height:78px;border-radius:18px;
}}
.badge{{
  border-radius:999px;
  padding:5px 11px;
  font-family:var(--font-mono);
  font-size:.64rem;
  letter-spacing:.75px;
  font-weight:800;
}}
.vol-card,.form-card,.log-item{{
  border-radius:14px;
  box-shadow:none;
}}
.vol-card:hover,.log-item:hover{{box-shadow:var(--shadow-sm);}}
.vol-avatar{{border-radius:12px;}}
.section-head{{
  font-family:var(--font-head);
  font-size:1rem;
  text-transform:uppercase;
  letter-spacing:.035em;
}}
.sidebar-logo{{
  background:var(--panel)!important;
  padding:24px 20px 18px;
}}
.sidebar-logo-text{{
  font-family:var(--font-head);
  letter-spacing:-.045em;
}}
.side-section-label{{
  font-family:var(--font-mono);
  font-size:.62rem;
  letter-spacing:1.15px;
}}
.stButton>button{{
  border-radius:10px!important;
  box-shadow:none!important;
  font-weight:700!important;
}}
.stButton>button:hover{{
  box-shadow:var(--shadow-sm)!important;
}}
[data-testid="stSidebar"] .stButton>button:hover{{
  box-shadow:none!important;
}}
.stTextInput input,.stTextArea textarea,.stNumberInput input,
div[data-baseweb="select"]>div{{
  border-radius:10px!important;
  box-shadow:none!important;
}}
[data-testid="stNumberInput"] div[data-baseweb="input"],
.stNumberInput div[data-baseweb="input"]{{
  border-radius:10px!important;
  box-shadow:none!important;
}}
.streamlit-expanderHeader{{
  border-radius:10px!important;
  box-shadow:none!important;
}}
[data-testid="stFormSubmitButton"]>button{{
  border-radius:10px!important;
  background:var(--red)!important;
  box-shadow:0 10px 24px color-mix(in srgb,var(--red) 22%,transparent)!important;
}}
[data-testid="stFormSubmitButton"]>button:hover{{
  background:color-mix(in srgb,var(--red) 88%,#000 12%)!important;
}}


:root{{
  --bg:{'#000000' if IS_DARK else '#F6F1E8'};
  --bg2:{'#000000' if IS_DARK else '#ECE5D8'};
  --surface:{'#000000' if IS_DARK else '#FFFCF5'};
  --panel:{'#000000' if IS_DARK else '#F4ECDF'};
  --card:{'#000000' if IS_DARK else '#FFFCF5'};
  --card-soft:{'#080808' if IS_DARK else '#EFE6D7'};
  --input-bg:{'#000000' if IS_DARK else '#FFFCF5'};
  --border:{'#1F1F1F' if IS_DARK else '#D5C9B8'};
  --border2:{'#303030' if IS_DARK else '#BFAF99'};
  --text:{'#F2F1EA' if IS_DARK else '#1F211D'};
  --text2:{'#CDD4C8' if IS_DARK else '#4C5048'};
  --text3:{'#8F9B8D' if IS_DARK else '#6D7168'};
  --red:{'#D9825B' if IS_DARK else '#B95F42'};
  --red-strong:{'#E39166' if IS_DARK else '#9F4D36'};
  --red-dim:{'rgba(217,130,91,.16)' if IS_DARK else 'rgba(185,95,66,.11)'};
  --orange:{'#C9863A' if IS_DARK else '#A96835'};
  --orange-dim:{'rgba(201,134,58,.15)' if IS_DARK else 'rgba(169,104,53,.12)'};
  --yellow:{'#D6B85A' if IS_DARK else '#A9862B'};
  --yellow-dim:{'rgba(214,184,90,.15)' if IS_DARK else 'rgba(169,134,43,.12)'};
  --green:{'#6EAD7A' if IS_DARK else '#4E8A60'};
  --green-dim:{'rgba(110,173,122,.15)' if IS_DARK else 'rgba(78,138,96,.12)'};
  --blue:{'#6A95A8' if IS_DARK else '#4E7D93'};
  --blue-dim:{'rgba(106,149,168,.15)' if IS_DARK else 'rgba(78,125,147,.12)'};
  --shadow:{'0 18px 52px rgba(0,0,0,.32)' if IS_DARK else '0 18px 44px rgba(10,10,10,.08)'};
  --shadow-sm:{'0 10px 26px rgba(0,0,0,.20)' if IS_DARK else '0 8px 24px rgba(10,10,10,.045)'};
}}
.stApp{{
  background:{'#000000' if IS_DARK else 'linear-gradient(180deg,#F6F1E8 0%,#ECE5D8 100%)'}!important;
}}
.main .block-container{{
  padding:1.55rem 2rem 2.6rem!important;
  max-width:1280px!important;
}}
[data-testid="stSidebar"]{{
  background:var(--panel)!important;
  border-right:1px solid var(--border)!important;
}}
.sidebar-logo{{
  display:flex;
  align-items:center;
  gap:10px;
  padding:18px 18px 20px!important;
  min-height:72px;
  border-bottom:1px solid var(--border);
}}
.sidebar-logo-badge{{
  width:34px;height:34px;border-radius:999px;
  display:flex;align-items:center;justify-content:center;
  background:var(--red);
  color:{'#000000' if IS_DARK else '#FFFCF5'};
  font-family:var(--font-mono);
  font-weight:900;
  font-size:.78rem;
  box-shadow:0 0 0 1px color-mix(in srgb,var(--red) 30%,transparent);
  flex-shrink:0;
}}
.sidebar-logo-text{{
  font-size:1.15rem!important;
  line-height:1!important;
}}
.sidebar-logo-sub{{display:none;}}
.side-section-label{{
  margin:16px 14px 8px!important;
  color:var(--text3)!important;
}}
[data-testid="stSidebar"] .stButton>button{{
  min-height:42px!important;
  border-radius:12px!important;
  padding:.55rem .8rem!important;
  font-size:.9rem!important;
  color:var(--text2)!important;
  justify-content:flex-start!important;
}}
[data-testid="stSidebar"] .stButton>button:hover{{
  background:{'#080808' if IS_DARK else '#EFE6D7'}!important;
  color:var(--text)!important;
}}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[kind="primaryFormSubmit"]{{
  background:{'#000000' if IS_DARK else '#FFFCF5'}!important;
  border-color:{'#262626' if IS_DARK else '#D5C9B8'}!important;
  color:var(--text)!important;
}}
[data-testid="stSidebar"] .stButton button[kind="secondary"]{{
  color:var(--text3)!important;
}}
.sidebar-nav-photo{{
  width:42px;
  height:42px;
  border-radius:12px;
  object-fit:contain;
  display:block;
  border:1px solid var(--border);
  background:var(--card-soft);
  padding:9px;
  filter:{'invert(1) brightness(.94)' if IS_DARK else 'none'};
  box-shadow:0 6px 18px rgba(0,0,0,.18);
}}
.sidebar-nav-photo.active{{
  border-color:var(--red);
  filter:{'invert(1) brightness(1.02)' if IS_DARK else 'none'};
  box-shadow:0 0 0 2px var(--red-dim),0 8px 22px rgba(0,0,0,.24);
}}
[data-testid="stSidebar"] div[data-testid="column"]:has(.sidebar-nav-photo){{
  display:flex;
  align-items:center;
  justify-content:flex-end;
  padding-right:3px!important;
}}
[data-testid="stSidebar"] div[data-testid="column"]:has(.sidebar-nav-photo) + div[data-testid="column"]{{
  padding-left:0!important;
}}
[data-testid="stSidebar"] div[data-testid="column"]:has(.sidebar-nav-photo) + div[data-testid="column"] .stButton>button{{
  padding-left:.55rem!important;
  min-height:42px!important;
}}
.sidebar-nav-spacer{{
  height:3px;
}}
.theme-toggle-wrap + div[data-testid="stHorizontalBlock"],
[data-testid="stSidebar"] .theme-toggle-wrap + div [data-testid="stHorizontalBlock"]{{
  margin:0 14px 12px!important;
  border-radius:16px!important;
  padding:4px!important;
  background:{'#0A0A0A' if IS_DARK else '#EFE6D7'}!important;
  border:1px solid {'#262626' if IS_DARK else '#D5C9B8'}!important;
}}
.page-header{{
  padding:0 0 20px!important;
  margin-bottom:26px!important;
  border-bottom:none!important;
}}
.page-title{{
  font-size:2rem!important;
  line-height:1.05!important;
  letter-spacing:-.04em!important;
}}
.page-sub{{
  margin-top:8px!important;
  font-size:.76rem!important;
}}
.stats-row{{
  gap:16px!important;
  margin-bottom:24px!important;
}}
.stat-card{{
  min-height:116px;
  border-radius:16px!important;
  border:1px solid var(--border)!important;
  background:var(--card)!important;
  padding:18px!important;
}}
.stat-card::before{{
  height:2px!important;
  opacity:.95;
}}
.stat-num{{
  font-size:2rem!important;
  font-weight:700!important;
}}
.stat-label{{
  font-size:.68rem!important;
  letter-spacing:1.1px!important;
}}
.case-card{{
  background:var(--card)!important;
  border:1px solid var(--border)!important;
  border-left-width:4px!important;
  border-radius:18px!important;
  padding:19px 20px!important;
  margin-bottom:10px!important;
}}
.case-card.critical{{border-left-color:var(--red)!important;}}
.case-card.high{{border-left-color:var(--orange)!important;}}
.case-card.medium{{border-left-color:var(--yellow)!important;}}
.case-card.low{{border-left-color:var(--green)!important;}}
.case-card:hover{{
  box-shadow:0 0 0 1px color-mix(in srgb,var(--border2) 55%,transparent), var(--shadow-sm)!important;
}}
.missing-photo{{
  width:88px!important;
  height:88px!important;
  border-radius:18px!important;
  background:{'#080808' if IS_DARK else '#EFE6D7'}!important;
}}
.badge{{
  border-radius:999px!important;
  padding:5px 12px!important;
  font-size:.66rem!important;
  letter-spacing:.85px!important;
}}
.vol-card,.form-card,.log-item{{
  background:var(--card)!important;
  border-color:var(--border)!important;
  border-radius:18px!important;
}}
.vol-avatar{{
  width:50px!important;
  height:50px!important;
  border-radius:15px!important;
}}
.section-head{{
  margin-top:8px!important;
  font-size:1rem!important;
  letter-spacing:.055em!important;
}}
.stButton>button{{
  background:{'#000000' if IS_DARK else '#FFFCF5'}!important;
  border-color:{'#262626' if IS_DARK else '#D5C9B8'}!important;
  color:var(--text)!important;
  border-radius:13px!important;
  min-height:40px!important;
  padding:.52rem .85rem!important;
}}
.stButton>button:hover{{
  background:{'#080808' if IS_DARK else '#EFE6D7'}!important;
  border-color:{'#303030' if IS_DARK else '#BFAF99'}!important;
  transform:none!important;
}}
.case-card + div[data-testid="stHorizontalBlock"] .stButton>button,
.returned-panel-head + div[data-testid="stHorizontalBlock"] .stButton>button{{
  border-radius:13px!important;
  background:{'#000000' if IS_DARK else '#FFFCF5'}!important;
  border-color:{'#262626' if IS_DARK else '#D5C9B8'}!important;
}}
.stTextInput input,.stTextArea textarea,.stNumberInput input,
div[data-baseweb="select"]>div{{
  background:{'#000000' if IS_DARK else '#FFFCF5'}!important;
  border-color:{'#262626' if IS_DARK else '#D5C9B8'}!important;
  border-radius:13px!important;
  color:var(--text)!important;
}}
.stTabs [data-baseweb="tab-list"]{{
  background:{'#0A0A0A' if IS_DARK else '#EFE6D7'}!important;
  border:1px solid {'#262626' if IS_DARK else '#D5C9B8'}!important;
  border-radius:18px!important;
  padding:5px!important;
}}
.stTabs [data-baseweb="tab"]{{
  border-radius:13px!important;
  border-bottom:none!important;
}}
.stTabs [aria-selected="true"]{{
  background:{'#000000' if IS_DARK else '#FFFCF5'}!important;
  color:var(--text)!important;
}}
.log-item{{
  padding:18px!important;
}}
[data-testid="stFormSubmitButton"]>button{{
  background:var(--red)!important;
  color:{'#000000' if IS_DARK else '#FFFCF5'}!important;
  border-radius:14px!important;
  min-height:48px!important;
}}
.dash-risk-card{{
  background:rgba(201,134,58,.14);
  border:1px solid rgba(201,134,58,.24);
  border-radius:18px;
  padding:16px 18px;
  margin:8px 0 22px;
  color:var(--orange);
  font-family:var(--font-mono);
  font-size:.78rem;
}}
.dash-risk-title{{
  font-family:var(--font-body);
  font-size:.92rem;
  font-weight:800;
  color:var(--text);
  margin-bottom:3px;
}}
.dash-actions{{
  display:flex;
  align-items:center;
  gap:12px;
  margin:0 0 22px;
}}
.dash-actions-note{{
  font-family:var(--font-mono);
  color:var(--text3);
  font-size:.78rem;
  padding-top:10px;
}}
.dash-case-card{{
  background:var(--card);
  border:1px solid var(--border);
  border-left:4px solid var(--yellow);
  border-radius:18px;
  padding:20px;
  margin-bottom:0;
}}
.dash-case-card.critical{{border-left-color:var(--red);}}
.dash-case-card.high{{border-left-color:var(--orange);}}
.dash-case-card.medium{{border-left-color:var(--yellow);}}
.dash-case-card.low{{border-left-color:var(--green);}}
.dash-case-title{{
  font-family:var(--font-head);
  color:var(--text);
  font-size:1.08rem;
  font-weight:800;
  letter-spacing:-.015em;
}}
.dash-case-meta{{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-top:4px;
  color:var(--text3);
  font-family:var(--font-mono);
  font-size:.73rem;
}}
.dash-case-desc{{
  color:var(--text2);
  font-size:.86rem;
  line-height:1.45;
  margin:12px 0 12px;
}}
.dash-action-row{{
  background:var(--card);
  border:1px solid var(--border);
  border-top:none;
  border-radius:0 0 18px 18px;
  padding:12px 18px 14px;
  margin:-1px 0 18px;
}}
.dash-action-row + div[data-testid="stHorizontalBlock"]{{
  margin-top:-64px!important;
  padding:12px 18px 14px!important;
}}
.dash-action-row + div[data-testid="stHorizontalBlock"] .stButton>button{{
  background:{'#000000' if IS_DARK else '#FFFCF5'}!important;
  border-color:{'#262626' if IS_DARK else '#D5C9B8'}!important;
  border-radius:14px!important;
  min-height:38px!important;
}}
.dash-vol-card{{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:18px;
  padding:18px;
  margin-bottom:14px;
  display:flex;
  align-items:center;
  gap:14px;
}}
.dash-vol-card .vol-avatar{{
  width:52px!important;
  height:52px!important;
}}


@media (max-width: 900px){{
  .main .block-container{{
    padding:1rem .85rem 2rem!important;
    max-width:100%!important;
  }}
  .page-header{{
    display:block!important;
    margin-bottom:18px!important;
    padding-bottom:14px!important;
  }}
  .page-title{{
    font-size:1.62rem!important;
    line-height:1.12!important;
    overflow-wrap:anywhere;
  }}
  .page-sub{{
    font-size:.72rem!important;
  }}
  .stats-row{{
    display:grid!important;
    grid-template-columns:1fr 1fr!important;
    gap:10px!important;
  }}
  .stat-card{{
    min-height:96px!important;
    padding:14px!important;
  }}
  .stat-num{{
    font-size:1.55rem!important;
  }}
  .case-card,.dash-case-card,.vol-card,.form-card,.log-item{{
    border-radius:14px!important;
    padding:14px!important;
  }}
  .missing-photo{{
    width:64px!important;
    height:64px!important;
    border-radius:14px!important;
  }}
  .badge{{
    font-size:.58rem!important;
    padding:4px 8px!important;
    max-width:100%;
    white-space:normal;
  }}
  .section-head{{
    font-size:.86rem!important;
    gap:8px!important;
  }}
  .dash-actions{{
    display:grid!important;
    grid-template-columns:1fr!important;
    gap:8px!important;
  }}
  .dash-actions-note{{
    padding-top:0!important;
  }}
  [data-testid="stHorizontalBlock"]{{
    gap:.6rem!important;
  }}
  [data-testid="stHorizontalBlock"] > div{{
    min-width:0!important;
  }}
  .stButton>button,
  [data-testid="stFormSubmitButton"]>button{{
    min-height:44px!important;
    white-space:normal!important;
    padding:.58rem .7rem!important;
  }}
  .stTextInput input,.stTextArea textarea,.stNumberInput input,
  div[data-baseweb="select"]>div{{
    min-height:44px!important;
    font-size:.86rem!important;
  }}
  iframe{{
    max-width:100%!important;
  }}
}}

@media (max-width: 760px){{
  .main [data-testid="stHorizontalBlock"]{{
    flex-wrap:wrap!important;
  }}
  .main [data-testid="stHorizontalBlock"] > div{{
    flex:1 1 100%!important;
    width:100%!important;
    min-width:100%!important;
  }}
  .dash-case-card > div:first-child,
  .case-card > div:first-child{{
    flex-direction:column!important;
    align-items:stretch!important;
  }}
  .dash-case-card [style*="justify-content:space-between"],
  .case-card [style*="justify-content:space-between"]{{
    flex-direction:column!important;
    align-items:flex-start!important;
  }}
  .dash-case-meta{{
    display:grid!important;
    grid-template-columns:1fr!important;
    gap:6px!important;
    font-size:.69rem!important;
    overflow-wrap:anywhere;
  }}
  .dash-case-desc{{
    font-size:.82rem!important;
    overflow-wrap:anywhere;
  }}
  .dash-action-row{{
    display:none!important;
  }}
  .dash-action-row + div[data-testid="stHorizontalBlock"]{{
    margin-top:8px!important;
    padding:0!important;
    gap:8px!important;
  }}
  .dash-vol-card{{
    align-items:flex-start!important;
    flex-wrap:wrap!important;
  }}
  .dash-vol-card > div:last-child{{
    width:100%!important;
    align-items:flex-start!important;
    text-align:left!important;
  }}
  .dash-risk-card,
  .dash-actions-note,
  .stat-trend,
  .stat-label{{
    overflow-wrap:anywhere;
  }}
}}

@media (max-width: 600px){{
  .main .block-container{{
    padding:.75rem .65rem 1.6rem!important;
  }}
  .login-mobile-scope + div[data-testid="stHorizontalBlock"]{{
    display:block!important;
  }}
  .login-mobile-scope + div[data-testid="stHorizontalBlock"] > div{{
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    padding:0!important;
  }}
  .login-mobile-scope + div[data-testid="stHorizontalBlock"] > div:first-child,
  .login-mobile-scope + div[data-testid="stHorizontalBlock"] > div:last-child{{
    display:none!important;
  }}
  .login-hero{{
    padding:20px 0 18px!important;
  }}
  .login-hero-title{{
    font-size:2.05rem!important;
    line-height:1!important;
  }}
  .login-hero-sub{{
    font-size:.66rem!important;
    letter-spacing:1.1px!important;
  }}
  .stTabs [data-baseweb="tab-list"]{{
    width:100%!important;
    padding:4px!important;
    border-radius:16px!important;
  }}
  .stTabs [data-baseweb="tab"]{{
    flex:1 1 0!important;
    min-width:0!important;
    justify-content:center!important;
    font-size:.8rem!important;
    padding:.62rem .45rem!important;
    white-space:normal!important;
  }}
  [data-testid="stForm"]{{
    padding:0!important;
  }}
  .page-title{{
    font-size:1.38rem!important;
  }}
  .stats-row{{
    grid-template-columns:1fr!important;
  }}
  .case-card > div:first-child,
  .dash-case-card > div:first-child{{
    gap:10px!important;
  }}
  .dash-case-card,
  .case-card{{
    padding:13px!important;
  }}
  .missing-photo{{
    width:100%!important;
    height:132px!important;
    font-size:1.2rem!important;
  }}
  .vol-card{{
    gap:10px!important;
  }}
  .vol-avatar{{
    width:42px!important;
    height:42px!important;
    border-radius:12px!important;
  }}
  .dash-action-row + div[data-testid="stHorizontalBlock"]{{
    margin-top:0!important;
    padding:0!important;
  }}
  .dash-action-row{{
    margin-bottom:10px!important;
  }}
  [data-testid="stFileUploaderDropzone"],
  [data-testid="stFileUploadDropzone"],
  section[data-testid="stFileUploadDropzone"]>div{{
    min-width:0!important;
  }}
}}
</style>
""", unsafe_allow_html=True)

                                                                                 
                                                          
                                                                                 
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rescue_hb.db")
HB_TIMEOUT_MULT = 2.5                                                   
HB_DEFAULT_INTERVAL = 30             

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
            CREATE TABLE IF NOT EXISTS cases (
                case_id     TEXT PRIMARY KEY,
                payload     TEXT NOT NULL,
                created_at  TEXT,
                updated_at  TEXT
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
                vol_id      TEXT PRIMARY KEY,
                lat         REAL,
                lon         REAL,
                address     TEXT,
                updated_at  TEXT
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkins (
                checkin_id  TEXT PRIMARY KEY,
                payload     TEXT NOT NULL,
                created_at  TEXT
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS operational_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type  TEXT NOT NULL,
                payload     TEXT NOT NULL,
                created_at  TEXT
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS report_draft_locations (
                draft_id    TEXT PRIMARY KEY,
                lat         REAL NOT NULL,
                lon         REAL NOT NULL,
                updated_at  TEXT
            )""")

init_db()

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
        if lat is not None and lon is not None:
            conn.execute("""
                INSERT INTO volunteer_gps (vol_id,lat,lon,address,updated_at)
                VALUES (?,?,?,?,?)
                ON CONFLICT(vol_id) DO UPDATE SET
                  lat=excluded.lat,
                  lon=excluded.lon,
                  address=COALESCE(NULLIF(excluded.address,''), volunteer_gps.address),
                  updated_at=excluded.updated_at
            """, (vol_id, lat, lon, "", now))

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

def db_save_vol_gps(vol_id: str, lat: float, lon: float, address: str = ""):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO volunteer_gps (vol_id,lat,lon,address,updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(vol_id) DO UPDATE SET
              lat=excluded.lat,
              lon=excluded.lon,
              address=excluded.address,
              updated_at=excluded.updated_at
        """, (vol_id, lat, lon, address or "", now))

def db_get_vol_gps(vol_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT lat, lon, address, updated_at FROM volunteer_gps WHERE vol_id=?",
            (vol_id,)
        ).fetchone()
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
    if not token:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT username, expires_at FROM app_sessions WHERE token=?",
            (token,)
        ).fetchone()
    if not row:
        return None
    try:
        if datetime.fromisoformat(row["expires_at"]) < datetime.now():
            delete_session(token)
            return None
    except Exception:
        delete_session(token)
        return None
    return row["username"]

def delete_session(token: str):
    with get_db() as conn:
        conn.execute("DELETE FROM app_sessions WHERE token=?", (token,))

def delete_user_sessions(username: str):
    with get_db() as conn:
        conn.execute("DELETE FROM app_sessions WHERE username=?", (username,))

def db_save_checkin(checkin: dict):
    cid = checkin.get("id")
    if not cid:
        return
    payload = json.dumps(checkin, ensure_ascii=False)
    with get_db() as conn:
        conn.execute("""
            INSERT INTO checkins (checkin_id,payload,created_at)
            VALUES (?,?,?)
            ON CONFLICT(checkin_id) DO UPDATE SET
              payload=excluded.payload,
              created_at=excluded.created_at
        """, (cid, payload, checkin.get("timestamp") or datetime.now().isoformat()))

def db_get_checkins(limit: int = 200) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT payload FROM checkins ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    result = []
    for row in rows:
        try:
            result.append(json.loads(row["payload"]))
        except Exception:
            pass
    return result

def db_add_event(event_type: str, payload: dict):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO operational_events (event_type,payload,created_at)
            VALUES (?,?,?)
        """, (event_type, json.dumps(payload, ensure_ascii=False), now))

def db_get_events(event_type: str, limit: int = 100) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT payload FROM operational_events
            WHERE event_type=?
            ORDER BY id DESC
            LIMIT ?
        """, (event_type, limit)).fetchall()
    result = []
    for row in rows:
        try:
            result.append(json.loads(row["payload"]))
        except Exception:
            pass
    return result

def db_clear_events(event_type: str):
    with get_db() as conn:
        conn.execute("DELETE FROM operational_events WHERE event_type=?", (event_type,))

def add_notification(message: str):
    st.session_state.notifications.append(message)
    db_add_event("notification", {"message": message})

def add_ai_log(entry: dict):
    st.session_state.ai_log.append(entry)
    db_add_event("ai_log", entry)

def add_checkin(checkin: dict):
    st.session_state.checkins.append(checkin)
    db_save_checkin(checkin)

def sync_operational_state_from_db():
    st.session_state.checkins = db_get_checkins()
    st.session_state.notifications = [
        e.get("message", "") for e in reversed(db_get_events("notification", 80)) if e.get("message")
    ]
    st.session_state.ai_log = list(reversed(db_get_events("ai_log", 160)))

def clear_ai_log():
    st.session_state.ai_log = []
    db_clear_events("ai_log")

def db_save_report_location(draft_id: str, lat: float, lon: float):
    now = datetime.now().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO report_draft_locations (draft_id,lat,lon,updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(draft_id) DO UPDATE SET
              lat=excluded.lat,
              lon=excluded.lon,
              updated_at=excluded.updated_at
        """, (draft_id, lat, lon, now))

def db_get_report_location(draft_id: str):
    if not draft_id:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT lat, lon, updated_at FROM report_draft_locations WHERE draft_id=?",
            (draft_id,)
        ).fetchone()
    return dict(row) if row else None

def db_clear_report_location(draft_id: str):
    if not draft_id:
        return
    with get_db() as conn:
        conn.execute("DELETE FROM report_draft_locations WHERE draft_id=?", (draft_id,))

def ensure_report_draft_id():
    qp_draft = st.query_params.get("report_draft")
    has_query_point = bool(st.query_params.get("report_lat") and st.query_params.get("report_lon"))
    if "report_draft_id" not in st.session_state:
        st.session_state.report_draft_id = qp_draft or secrets.token_urlsafe(12)
    elif qp_draft and has_query_point and qp_draft != st.session_state.report_draft_id:
                                                                            
                                                                           
        st.session_state.report_draft_id = qp_draft
    return st.session_state.report_draft_id

def db_save_case(case: dict):
    cid = case.get("id")
    if not cid:
        return
    now = datetime.now().isoformat()
    payload = json.dumps(case, ensure_ascii=False)
    with get_db() as conn:
        conn.execute("""
            INSERT INTO cases (case_id,payload,created_at,updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(case_id) DO UPDATE SET
              payload=excluded.payload,
              updated_at=excluded.updated_at
        """, (cid, payload, case.get("created_at") or now, now))

def db_get_all_cases() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT payload FROM cases ORDER BY created_at ASC, case_id ASC").fetchall()
    cases = []
    for row in rows:
        try:
            cases.append(json.loads(row["payload"]))
        except Exception:
            pass
    return cases

def refresh_next_case_id():
    nums = []
    for case in st.session_state.get("cases", []):
        cid = case.get("id", "")
        if cid.startswith("C") and cid[1:].isdigit():
            nums.append(int(cid[1:]))
    st.session_state.next_case_id = max(nums, default=0) + 1

def sync_cases_from_db():
    """Load shared missing-person reports so every browser session sees the same cases."""
    stored_cases = db_get_all_cases()
    if stored_cases:
        st.session_state.cases = stored_cases
    elif st.session_state.get("cases"):
        for case in st.session_state.cases:
            db_save_case(case)
    elif "cases" not in st.session_state:
        st.session_state.cases = []
    refresh_next_case_id()

def refresh_shared_cases():
    sync_cases_from_db()
    sync_volunteer_assignments_from_cases()

def sync_volunteer_assignments_from_cases():
    active_assignments = {}
    for case in st.session_state.get("cases", []):
        if is_case_closed(case):
            continue
        assigned_ids = []
        if case.get("team_ids"):
            assigned_ids.extend(case.get("team_ids", []))
        elif case.get("assigned_to"):
            assigned_ids.append(case.get("assigned_to"))
        for vid in assigned_ids:
            active_assignments[vid] = case.get("id")

    for vol in st.session_state.get("volunteers", []):
        cid = active_assignments.get(vol.get("id"))
        if cid:
            vol["assigned"] = cid
            if vol.get("status") != "offline":
                vol["status"] = "busy"
        elif vol.get("assigned") and vol.get("assigned") not in active_assignments.values():
            vol["assigned"] = None
            if vol.get("status") == "busy":
                vol["status"] = "active"

                                                                                 
                                                       
                                                                                 
FASTAPI_PORT = int(os.getenv("FINDFIRST_API_PORT", "8000"))
_server_started = False

def _new_fastapi_app():
    return FastAPI(title="FindFirst Heartbeat", version="1.0")

def _fastapi_port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False

def _rescue_api_on_port(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=0.4) as resp:
            data = resp.read(300).decode("utf-8", "ignore")
        return "FindFirst Heartbeat" in data
    except Exception:
        return False

def _select_fastapi_port() -> bool:
    """Returns True when this process should start a server."""
    global FASTAPI_PORT
    preferred = FASTAPI_PORT
    for port in range(preferred, preferred + 20):
        if _rescue_api_on_port(port):
            FASTAPI_PORT = port
            return False
        if not _fastapi_port_open(port):
            FASTAPI_PORT = port
            return True
    return False

def _start_fastapi_server():
    """Launch FastAPI in a daemon thread. Called once per Streamlit process."""
    global _server_started
    if _server_started or not HAS_FASTAPI:
        return
    should_start = _select_fastapi_port()
    _server_started = True
    if not should_start:
        return

    fapi = _new_fastapi_app()
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

    class CasePayload(BaseModel):
        case: dict

    class ReportLocationPayload(BaseModel):
        draft_id: str
        lat: float
        lon: float

    @fapi.get("/")
    def root():
        return {"service": "FindFirst Heartbeat", "time": datetime.now().isoformat()}

    @fapi.post("/heartbeat")
    def heartbeat(p: HBPayload, x_forwarded_for: Optional[str] = Header(None)):
        db_upsert_heartbeat(
            p.volunteer_id, p.source or "agent",
            p.interval_sec or HB_DEFAULT_INTERVAL,
            p.device_id, x_forwarded_for or "unknown",
            p.lat, p.lon, p.field_status
        )
        return {"ok": True, "volunteer_id": p.volunteer_id, "received_at": datetime.now().isoformat()}

    @fapi.post("/report-location")
    def report_location(p: ReportLocationPayload):
        db_save_report_location(p.draft_id, p.lat, p.lon)
        return {"ok": True, "draft_id": p.draft_id, "lat": p.lat, "lon": p.lon, "updated_at": datetime.now().isoformat()}

    @fapi.get("/report-location/{draft_id}")
    def report_location_get(draft_id: str):
        loc = db_get_report_location(draft_id)
        if not loc:
            from fastapi import HTTPException
            raise HTTPException(404, "Draft location not found")
        return loc

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

    @fapi.get("/cases")
    def cases_all():
        return {"cases": db_get_all_cases(), "fetched_at": datetime.now().isoformat()}

    @fapi.post("/cases")
    def cases_create(p: CasePayload):
        db_save_case(p.case)
        return {"ok": True, "case_id": p.case.get("id"), "updated_at": datetime.now().isoformat()}

    @fapi.get("/cases/{case_id}")
    def cases_one(case_id: str):
        for case in db_get_all_cases():
            if case.get("id") == case_id:
                return case
        from fastapi import HTTPException
        raise HTTPException(404, "Case not found")

    def _run():
        uvicorn.run(fapi, host="0.0.0.0", port=FASTAPI_PORT, log_level="error")

    t = threading.Thread(target=_run, daemon=True)
    t.start()

                                                                                      
if HAS_FASTAPI:
    _start_fastapi_server()

                                                                                 
                                           
                                                                                 

def sync_online_status():
    """Merge DB heartbeat data into st.session_state.volunteers."""
    live = db_get_all_statuses()
    saved_gps = db_get_all_vol_gps()
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
            else:
                gps = saved_gps.get(vol["id"])
                if gps and gps.get("lat") is not None and gps.get("lon") is not None:
                    vol["lat"], vol["lon"] = gps["lat"], gps["lon"]
                    if gps.get("address"):
                        vol["address"] = gps["address"]
                                                                  
            if rec["online_status"] == "offline" and vol["status"] == "active":
                vol["status"] = "offline"
        else:
            vol.setdefault("online_status", "unknown")
            gps = saved_gps.get(vol["id"])
            if gps and gps.get("lat") is not None and gps.get("lon") is not None:
                vol["lat"], vol["lon"] = gps["lat"], gps["lon"]
                if gps.get("address"):
                    vol["address"] = gps["address"]

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
        f'<span data-hb-badge="1" data-vol-id="{vol.get("id","")}" data-status="{os_}" '
        f'data-last="{lhb or ""}" data-interval="{vol.get("hb_interval", HB_DEFAULT_INTERVAL) or HB_DEFAULT_INTERVAL}" '
        f'data-source="{src_icon}" style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{bg};border:1px solid {border};border-radius:6px;'
        f'padding:2px 8px;font-size:.67rem;font-family:var(--font-mono);color:{color}">'
        f'<span data-hb-dot="1" class="online-dot {os_}"></span><span data-hb-label="1">{src_icon} {label}{ago}</span></span>'
    )

def inject_heartbeat_badge_js():
    """Keep online/offline age badges fresh without waiting for a Streamlit rerun."""
    streamlit.components.v1.html(f"""
    <script>
    (function(){{
      if (window.parent.__rescueHeartbeatBadges) return;
      window.parent.__rescueHeartbeatBadges = true;
      const API = "http://localhost:{FASTAPI_PORT}/status";
      const COLORS = {{
        online:  {{fg:"var(--green)", bg:"var(--green-dim)", border:"rgba(34,216,122,.25)"}},
        offline: {{fg:"var(--red-strong)", bg:"var(--red-dim)", border:"rgba(255,59,59,.25)"}},
        unknown: {{fg:"var(--text3)", bg:"var(--card-soft)", border:"rgba(100,112,120,.15)"}}
      }};
      const sourceIcon = {{agent:"📡", browser:"🌐", checkin:"📋"}};
      let latest = {{}};

      function ageText(delta){{
        if (!Number.isFinite(delta)) return "";
        if (delta < 120) return delta + "s";
        if (delta < 7200) return Math.floor(delta / 60) + "m";
        return Math.floor(delta / 3600) + "h";
      }}
      function computedStatus(rec, originalStatus, interval){{
        if (!rec.last) return originalStatus || "unknown";
        const delta = Math.max(0, Math.floor((Date.now() - Date.parse(rec.last)) / 1000));
        if (delta > interval * {HB_TIMEOUT_MULT}) return "offline";
        return rec.status === "offline" ? "offline" : "online";
      }}
      function paint(el, status, text){{
        const c = COLORS[status] || COLORS.unknown;
        el.style.color = c.fg;
        el.style.background = c.bg;
        el.style.borderColor = c.border;
        const dot = el.querySelector("[data-hb-dot]");
        if (dot) dot.className = "online-dot " + status;
        const label = el.querySelector("[data-hb-label]");
        if (label) label.textContent = text;
      }}
      function updateBadges(){{
        const doc = window.parent.document;
        doc.querySelectorAll("[data-hb-badge]").forEach(function(el){{
          const id = el.dataset.volId;
          const rec = latest[id] || {{
            status: el.dataset.status || "unknown",
            last: el.dataset.last || "",
            source: el.dataset.source || ""
          }};
          const interval = parseFloat(el.dataset.interval || "30") || 30;
          const status = computedStatus(rec, rec.status, interval);
          let suffix = "";
          if (rec.last) {{
            const delta = Math.max(0, Math.floor((Date.now() - Date.parse(rec.last)) / 1000));
            suffix = " " + ageText(delta);
          }}
          const src = sourceIcon[rec.source] || rec.source || el.dataset.source || "";
          paint(el, status, (src ? src + " " : "") + status.toUpperCase() + suffix);
        }});
      }}
      async function poll(){{
        try {{
          const res = await fetch(API, {{cache:"no-store"}});
          if (!res.ok) return;
          const data = await res.json();
          (data.volunteers || []).forEach(function(v){{
            latest[v.volunteer_id] = {{
              status: v.online_status || "unknown",
              last: v.last_heartbeat || "",
              source: v.hb_source || ""
            }};
          }});
        }} catch (e) {{}}
        updateBadges();
      }}
      updateBadges();
      poll();
      setInterval(updateBadges, 1000);
      setInterval(poll, 5000);
    }})();
    </script>
    """, height=0)

def inject_cases_refresh_js():
    return

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

def persist_browser_gps_fix(vol: dict, lat: float, lon: float, accuracy: float | None = None, marker: str | None = None) -> dict | None:
    if not vol:
        return None
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    marker = marker or f"{vol.get('id')}:{lat:.6f}:{lon:.6f}"
    if st.session_state.get("_last_browser_gps_fix") == marker:
        return {
            "lat": lat,
            "lon": lon,
            "accuracy": accuracy,
            "address": vol.get("address") or f"Browser GPS {lat:.5f}, {lon:.5f}",
            "updated_at": vol.get("last_checkin") or datetime.now().isoformat(),
        }

    address = f"Browser GPS {lat:.5f}, {lon:.5f}"
    if accuracy is not None:
        try:
            address += f" (±{int(float(accuracy))}m)"
        except Exception:
            pass
    now = datetime.now().isoformat()
    vol["lat"] = lat
    vol["lon"] = lon
    vol["address"] = address
    vol["last_checkin"] = now
    db_save_vol_gps(vol["id"], lat, lon, address)
    db_upsert_heartbeat(vol["id"], "browser", HB_DEFAULT_INTERVAL, None, None, lat, lon, "📍 Browser GPS")
    st.session_state["_last_browser_gps_fix"] = marker
    return {"lat": lat, "lon": lon, "accuracy": accuracy, "address": address, "updated_at": now}

def read_browser_gps_query(vol: dict) -> dict | None:
    """Persist a browser GPS fix passed back from an embedded Streamlit component."""
    if not vol:
        return None
    if st.query_params.get("gps_vol") != vol.get("id"):
        return None
    try:
        lat = float(st.query_params.get("gps_lat", ""))
        lon = float(st.query_params.get("gps_lon", ""))
    except Exception:
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    try:
        accuracy = float(st.query_params.get("gps_acc", ""))
    except Exception:
        accuracy = None
    ts = st.query_params.get("gps_ts", "")
    marker = f"{vol.get('id')}:{lat:.6f}:{lon:.6f}:{ts}"
    return persist_browser_gps_fix(vol, lat, lon, accuracy, marker)

def read_streamlit_geolocation_fix(vol: dict) -> dict | None:
    """Use the native Streamlit geolocation component when installed."""
    if not vol or not HAS_STREAMLIT_GEOLOCATION:
        return None
    try:
        location = streamlit_geolocation()
    except Exception as exc:
        st.warning(f"Browser geolocation component failed: {exc}")
        return None
    if not location:
        return None
    lat = location.get("latitude", location.get("lat"))
    lon = location.get("longitude", location.get("lon"))
    accuracy = location.get("accuracy")
    if lat is None or lon is None:
        return None
    try:
        marker = f"{vol.get('id')}:{float(lat):.6f}:{float(lon):.6f}:{location.get('timestamp','component')}"
    except Exception:
        marker = None
    return persist_browser_gps_fix(vol, lat, lon, accuracy, marker)

def render_my_position_map(vol: dict, latest_gps: dict | None, gps_is_auto: bool, show_case_markers: bool = True):
    """Show the volunteer's current GPS context on a map."""
    center_lat = float((latest_gps or {}).get("lat") or vol.get("lat") or 50.45)
    center_lon = float((latest_gps or {}).get("lon") or vol.get("lon") or 30.52)
    map_id = f"mypos-map-{vol.get('id', 'vol')}-{center_lat:.5f}-{center_lon:.5f}".replace(".", "-").replace(":", "-")
    map_id_js = json.dumps(map_id)
    current_label = "Current GPS position" if gps_is_auto else "Waiting for browser GPS"
    current_color = "#6EAD7A" if gps_is_auto else "#8F9B8D"
    tile_url = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" if IS_DARK else "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
    case_points = []
    if show_case_markers:
        for case in st.session_state.get("cases", []):
            if is_case_closed(case):
                continue
            if case.get("lat") is None or case.get("lon") is None:
                continue
            label, cls = get_priority(compute_dynamic_risk(case)["effective"])
            color = {"critical": "#D9825B", "high": "#C9863A", "medium": "#D6B85A", "low": "#6EAD7A"}.get(cls, "#D9825B")
            case_points.append({
                "lat": float(case["lat"]),
                "lon": float(case["lon"]),
                "name": f"{case.get('id', '')} · {case.get('name', '')}",
                "label": label,
                "color": color,
                "location": case.get("location", "Map pin"),
                "radius_km": dynamic_search_radius_km(case),
            })
    payload = json.dumps(case_points, ensure_ascii=False)
    volunteer_name = json.dumps(vol.get("name", "Volunteer"), ensure_ascii=False)
    current_label_js = json.dumps(current_label, ensure_ascii=False)
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    streamlit.components.v1.html(f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body {{ margin:0; background:transparent; }}
    #{map_id} {{
      width:100%;
      height:320px;
      border-radius:16px;
      overflow:hidden;
      background:#000000;
      border:1px solid rgba(148,163,184,.22);
    }}
    .leaflet-container {{ background:#000000; font-family:Inter,system-ui,sans-serif; }}
    .map-chip {{
      position:absolute;
      z-index:500;
      left:14px;
      bottom:14px;
      background:rgba(0,0,0,.88);
      border:1px solid rgba(148,163,184,.28);
      border-radius:999px;
      padding:8px 12px;
      color:#F2F1EA;
      font:700 12px/1.2 Inter,system-ui,sans-serif;
      backdrop-filter:blur(10px);
    }}
  </style>
</head>
<body>
  <div id="{map_id}"><div class="map-chip">{'GPS locked' if gps_is_auto else 'Request location access above'}</div></div>
  <script>
    const center = [{center_lat:.6f}, {center_lon:.6f}];
    const cases = {payload};
    const map = L.map({map_id_js}, {{ center, zoom: 15, preferCanvas: true }});
    L.tileLayer("{tile_url}", {{
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      subdomains: "abcd",
      maxZoom: 19
    }}).addTo(map);
    L.circleMarker(center, {{
      radius: 12,
      color: "{current_color}",
      fillColor: "{current_color}",
      fillOpacity: .92,
      weight: 3
    }}).bindPopup("<b>" + {volunteer_name} + "</b><br>" + {current_label_js}).addTo(map);
    if ({str(gps_is_auto).lower()}) {{
      L.circle(center, {{
        radius: 80,
        color: "{current_color}",
        fillColor: "{current_color}",
        fillOpacity: .08,
        weight: 1
      }}).addTo(map);
    }}
    cases.forEach(function(c) {{
      L.circle([c.lat, c.lon], {{
        radius: Math.max(0, Number(c.radius_km || 0)) * 1000,
        color: c.color,
        fillColor: c.color,
        fillOpacity: .07,
        weight: 1.5,
        dashArray: "6 6"
      }}).bindPopup("<b>" + c.name + "</b><br>Search radius: " + c.radius_km + " km").addTo(map);
      L.circleMarker([c.lat, c.lon], {{
        radius: 8,
        color: c.color,
        fillColor: c.color,
        fillOpacity: .25,
        weight: 2,
        dashArray: "4"
      }}).bindPopup("<b>" + c.name + "</b><br>" + c.location + "<br>Risk: " + c.label + "<br>Search radius: " + c.radius_km + " km").addTo(map);
    }});
    const bounds = [center].concat(cases.map(c => [c.lat, c.lon]));
    if (bounds.length > 1) {{
      map.fitBounds(bounds, {{ padding:[34,34], maxZoom:13 }});
    }}
    setTimeout(function() {{ map.invalidateSize(); }}, 250);
  </script>
</body>
</html>""", height=340)

def browser_gps_permission_widget(vol_id: str):
    """Small browser-side permission flow for volunteer geolocation."""
    streamlit.components.v1.html(f"""
<div class="gps-permission">
  <div class="gps-copy">
    <div class="gps-title">Location permission required</div>
    <div class="gps-text">Click the button to open the browser's native location permission dialog.</div>
  </div>
  <button id="gps-enable" type="button">Request Location Access</button>
  <div id="gps-status">Waiting for permission request.</div>
</div>
<style>
  .gps-permission {{
    font-family: Inter, system-ui, -apple-system, Segoe UI, sans-serif;
    background:#000000;
    border:1px solid rgba(148,163,184,.22);
    border-radius:16px;
    padding:16px;
    display:grid;
    grid-template-columns:minmax(0,1fr) auto;
    gap:12px;
    align-items:center;
    color:#8F9B8D;
  }}
  .gps-title {{
    color:#F2F1EA;
    font-size:15px;
    font-weight:800;
    letter-spacing:.01em;
  }}
  .gps-text {{
    color:#8F9B8D;
    font-size:13px;
    margin-top:4px;
    line-height:1.35;
  }}
  #gps-enable {{
    border:1px solid rgba(255,255,255,.08);
    border-radius:12px;
    background:#D9825B;
    color:#000000;
    font-weight:800;
    padding:12px 18px;
    cursor:pointer;
    min-width:220px;
    box-shadow:0 14px 34px rgba(255,107,134,.24);
  }}
  #gps-enable:disabled {{
    opacity:.75;
    cursor:default;
  }}
  #gps-status {{
    grid-column:1 / -1;
    font-size:13px;
    line-height:1.35;
    color:#8F9B8D;
    background:rgba(2,6,23,.38);
    border:1px solid rgba(148,163,184,.14);
    border-radius:10px;
    padding:10px 12px;
  }}
  @media(max-width:640px){{
    .gps-permission {{ grid-template-columns:1fr; }}
    #gps-enable {{ width:100%; }}
  }}
</style>
<script>
(function(){{
  const btn = document.getElementById("gps-enable");
  const status = document.getElementById("gps-status");
  function setStatus(html, color){{
    status.innerHTML = html;
    if(color) status.style.color = color;
  }}
  async function readPermissionState(){{
    if (!navigator.permissions || !navigator.permissions.query) return;
    try {{
      const result = await navigator.permissions.query({{name:"geolocation"}});
      if (result.state === "denied") {{
        setStatus("Location is blocked for this site. Open site settings in the address bar and set Location to Allow, then reload.", "#D9825B");
      }} else if (result.state === "granted") {{
        setStatus("Location is already allowed. Click the button to refresh your GPS fix.", "#6EAD7A");
      }} else {{
        setStatus("Location permission is not decided yet. Click the button to show the native browser prompt.", "#8F9B8D");
      }}
      result.onchange = readPermissionState;
    }} catch(e) {{}}
  }}
  function sendFix(pos){{
    const lat = pos.coords.latitude.toFixed(6);
    const lon = pos.coords.longitude.toFixed(6);
    const acc = Math.round(pos.coords.accuracy || 0);
    setStatus("<b style='color:#6EAD7A'>GPS saved:</b> " + lat + ", " + lon + " (±" + acc + "m)", "#8F9B8D");
    btn.textContent = "GPS Active";
    btn.disabled = false;
    const params = new URLSearchParams(window.parent.location.search);
    params.set("page", "tracking");
    params.set("gps_vol", "{vol_id}");
    params.set("gps_lat", lat);
    params.set("gps_lon", lon);
    params.set("gps_acc", String(acc));
    params.set("gps_ts", String(Date.now()));
    window.parent.location.href = window.parent.location.pathname + "?" + params.toString();
  }}
  function fail(err){{
    btn.disabled = false;
    btn.textContent = "Retry Location Access";
    const message = err && err.message ? err.message : "permission denied or timed out";
    if (err && err.code === 1) {{
      setStatus("Location permission was denied. Use the browser address bar site settings to allow Location, then retry.", "#D9825B");
    }} else {{
      setStatus("Location unavailable: " + message, "#D6B85A");
    }}
  }}
  btn.addEventListener("click", function(){{
    if (!navigator.geolocation) {{
      setStatus("This browser does not support geolocation.", "#D9825B");
      return;
    }}
    btn.disabled = true;
    btn.textContent = "Requesting...";
    setStatus("Requesting native browser location permission...", "#8F9B8D");
    navigator.geolocation.getCurrentPosition(sendFix, fail, {{
      enableHighAccuracy: true,
      maximumAge: 0,
      timeout: 15000
    }});
  }});
  readPermissionState();
}})();
</script>
""", height=150)

                                                                                 
             
                                                                                 
client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None

                                                                                 
         
                                                                                 
DEFAULT_USERS = {
    "ivan":  {"password":"1234",  "role":"volunteer","name":"Ivan Petrov",    "skill":"Mountain Rescue",   "address":"Independence Square, Kyiv",      "lat":50.45,"lon":30.52,"id":"V001"},
    "sarah": {"password":"1234",  "role":"volunteer","name":"Sarah Mitchell", "skill":"Paramedic / Medic", "address":"Olympic Stadium, Kyiv",          "lat":50.43,"lon":30.55,"id":"V002"},
    "mike":  {"password":"1234",  "role":"volunteer","name":"Mike Torres",    "skill":"Dive Rescue",       "address":"Podil River Station, Kyiv",      "lat":50.47,"lon":30.48,"id":"V003"},
    "julia": {"password":"1234",  "role":"reporter", "name":"Julia Brown",    "id":None},
    "alex":  {"password":"1234",  "role":"reporter", "name":"Alex Chen",      "id":None},
    "admin": {"password":"admin", "role":"volunteer","name":"Admin",          "skill":"General Search",    "address":"Kyiv Central Station",          "lat":50.45,"lon":30.52,"id":"V004"},
}

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 210_000

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"

def password_is_hashed(value: str | None) -> bool:
    return bool(value and value.startswith(f"{PASSWORD_SCHEME}$"))

def verify_password(stored: str | None, provided: str) -> bool:
    if not stored:
        return False
    if not password_is_hashed(stored):
        return hmac.compare_digest(stored, provided or "")
    try:
        scheme, iterations, salt, expected = stored.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            (provided or "").encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def _init_users_table():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS app_users (
            username TEXT PRIMARY KEY,
            password TEXT, role TEXT, name TEXT,
            skill TEXT, address TEXT, lat REAL, lon REAL, vol_id TEXT,
            preferred_theme TEXT DEFAULT 'light'
        )""")
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(app_users)").fetchall()}
        if "preferred_theme" not in cols:
            conn.execute("ALTER TABLE app_users ADD COLUMN preferred_theme TEXT DEFAULT 'light'")
        for uname, u in DEFAULT_USERS.items():
            conn.execute("""INSERT OR IGNORE INTO app_users
                (username,password,role,name,skill,address,lat,lon,vol_id,preferred_theme)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (uname, hash_password(u["password"]), u["role"], u["name"],
                 u.get("skill"), u.get("address"), u.get("lat"), u.get("lon"), u.get("id"), "light"))

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

def verify_current_session_password(password: str) -> bool:
    user = st.session_state.get("current_user") or {}
    uname = user.get("username")
    if not uname:
        return False
    stored_user = get_users().get(uname)
    return bool(stored_user and verify_password(stored_user.get("password"), password))

def save_user(uname, u):
    password = u.get("password")
    if password and not password_is_hashed(password):
        password = hash_password(password)
    preferred_theme = u.get("preferred_theme") if u.get("preferred_theme") in ("light", "dark") else "light"
    with get_db() as conn:
        conn.execute("""INSERT OR REPLACE INTO app_users
            (username,password,role,name,skill,address,lat,lon,vol_id,preferred_theme)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (uname, password, u.get("role"), u.get("name"),
             u.get("skill"), u.get("address"), u.get("lat"), u.get("lon"), u.get("id"), preferred_theme))

def save_user_theme(uname: str, theme: str):
    if theme not in ("light", "dark"):
        return
    with get_db() as conn:
        conn.execute("UPDATE app_users SET preferred_theme=? WHERE username=?", (theme, uname))

def apply_theme_for_user(uname: str, user: dict):
    theme = user.get("preferred_theme") if user.get("preferred_theme") in ("light", "dark") else "light"
    st.session_state.ui_theme = theme
    st.query_params["theme"] = theme

def set_theme_action(theme: str):
    if theme not in ("light", "dark"):
        return
    st.session_state.ui_theme = theme
    st.query_params["theme"] = theme
    user = st.session_state.get("current_user") or {}
    uname = user.get("username")
    if uname:
        save_user_theme(uname, theme)
        st.session_state.current_user["preferred_theme"] = theme

def migrate_user_password_if_needed(uname: str, user: dict, plain_password: str):
    if not password_is_hashed(user.get("password")):
        upgraded = dict(user)
        upgraded["password"] = plain_password
        save_user(uname, upgraded)

def migrate_stored_plaintext_passwords():
    with get_db() as conn:
        rows = conn.execute("SELECT username,password FROM app_users").fetchall()
        for row in rows:
            password = row["password"]
            if password and not password_is_hashed(password):
                conn.execute(
                    "UPDATE app_users SET password=? WHERE username=?",
                    (hash_password(password), row["username"])
                )

def session_user(uname: str, user: dict) -> dict:
    public = {k: v for k, v in user.items() if k != "password"}
    return {"username": uname, **public}

migrate_stored_plaintext_passwords()

                                                                                 
         
                                                                                 
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

def clamp_score(value, low=0, high=100):
    return max(low, min(high, int(round(value))))

CLOSED_CASE_STATUSES = {"found", "closed", "unfound"}

def is_case_closed(case: dict) -> bool:
    return case.get("status") in CLOSED_CASE_STATUSES

def is_case_active(case: dict) -> bool:
    return not is_case_closed(case)

def case_missing_hours_now(case: dict) -> float:
    """Total missing time, including elapsed time since the report was created."""
    try:
        base_hours = float(case.get("time_missing") or 0)
    except Exception:
        base_hours = 0.0
    created_at = case.get("created_at")
    if created_at:
        try:
            elapsed = (datetime.now() - datetime.fromisoformat(created_at)).total_seconds() / 3600
            base_hours += max(0.0, elapsed)
        except Exception:
            pass
    return max(0.0, base_hours)

def dynamic_search_radius_km(case: dict) -> float:
    """Search area grows by 5 km for every 30 minutes the person is missing."""
    try:
        base_radius = float(case.get("search_radius_base_km") or case.get("search_radius_km") or 1.0)
    except Exception:
        base_radius = 1.0
    growth_steps = math.floor(case_missing_hours_now(case) * 2)
    return round(base_radius + growth_steps * 5.0, 1)

                                                                                
WEATHER_MODIFIERS = {
    "Clear":        {"Flood":0,  "Wildfire":8,  "Mountain / Forest":0,  "Urban Area":0,  "Missing Person":0,  "Other":0},
    "Rain":         {"Flood":20, "Wildfire":-5, "Mountain / Forest":12, "Urban Area":5,  "Missing Person":8,  "Other":5},
    "Storm":        {"Flood":35, "Wildfire":5,  "Mountain / Forest":25, "Urban Area":15, "Missing Person":20, "Other":15},
    "Snow":         {"Flood":12, "Wildfire":-8, "Mountain / Forest":30, "Urban Area":10, "Missing Person":22, "Other":18},
    "Fog":          {"Flood":8,  "Wildfire":0,  "Mountain / Forest":15, "Urban Area":10, "Missing Person":15, "Other":8},
    "Extreme Heat": {"Flood":5,  "Wildfire":40, "Mountain / Forest":12, "Urban Area":12, "Missing Person":10, "Other":5},
}
WEATHER_ICONS = {"Clear":"☀️","Rain":"🌧️","Storm":"⛈️","Snow":"❄️","Fog":"🌫️","Extreme Heat":"🔥"}
WEATHER_TTL_MINUTES = 20
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
WMO_WEATHER_LABELS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm with hail",
}

def classify_weather_snapshot(current: dict) -> str:
    code = int(current.get("weather_code") or 0)
    temp = float(current.get("temperature_2m") or 0)
    apparent = float(current.get("apparent_temperature") or temp)
    precipitation = float(current.get("precipitation") or 0)
    rain = float(current.get("rain") or 0)
    showers = float(current.get("showers") or 0)
    snowfall = float(current.get("snowfall") or 0)
    wind_gusts = float(current.get("wind_gusts_10m") or 0)
    wind_speed = float(current.get("wind_speed_10m") or 0)
    if apparent >= 35 or temp >= 37:
        return "Extreme Heat"
    if code in {95, 96, 99} or wind_gusts >= 70 or wind_speed >= 55:
        return "Storm"
    if code in {45, 48}:
        return "Fog"
    if code in {71, 73, 75, 77, 85, 86} or snowfall > 0:
        return "Snow"
    if code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82} or precipitation > 0 or rain > 0 or showers > 0:
        return "Rain"
    return "Clear"

def fallback_weather_snapshot(lat=None, lon=None, error: str | None = None) -> dict:
    return {
        "category": "Clear",
        "label": "Weather unavailable",
        "source": "fallback",
        "updated_at": datetime.now().isoformat(),
        "lat": lat,
        "lon": lon,
        "error": error or "Weather API unavailable",
    }

def fetch_open_meteo_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": f"{float(lat):.6f}",
        "longitude": f"{float(lon):.6f}",
        "current": ",".join([
            "temperature_2m", "apparent_temperature", "precipitation", "rain",
            "showers", "snowfall", "weather_code", "cloud_cover",
            "wind_speed_10m", "wind_gusts_10m", "is_day",
        ]),
        "timezone": "auto",
    }
    if HAS_REQUESTS:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=6)
        response.raise_for_status()
        payload = response.json()
    else:
        encoded = urllib.parse.urlencode(params)
        with urllib.request.urlopen(f"{OPEN_METEO_URL}?{encoded}", timeout=6) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    current = payload.get("current") or {}
    category = classify_weather_snapshot(current)
    code = int(current.get("weather_code") or 0)
    return {
        "category": category,
        "label": WMO_WEATHER_LABELS.get(code, f"WMO {code}"),
        "source": "Open-Meteo",
        "updated_at": datetime.now().isoformat(),
        "observed_at": current.get("time"),
        "lat": float(lat),
        "lon": float(lon),
        "weather_code": code,
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "precipitation_mm": current.get("precipitation"),
        "rain_mm": current.get("rain"),
        "snowfall_cm": current.get("snowfall"),
        "cloud_cover_pct": current.get("cloud_cover"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_gusts_kmh": current.get("wind_gusts_10m"),
        "is_day": current.get("is_day"),
    }

def weather_snapshot_stale(case: dict, max_age_minutes: int = WEATHER_TTL_MINUTES) -> bool:
    weather = case.get("weather") or {}
    if weather.get("category") not in WEATHER_MODIFIERS:
        return True
    if weather.get("source") == "fallback" or weather.get("label") == "Weather unavailable":
        return True
    try:
        updated = datetime.fromisoformat(weather.get("updated_at", ""))
        if datetime.now() - updated > timedelta(minutes=max_age_minutes):
            return True
    except Exception:
        return True
    try:
        if abs(float(weather.get("lat")) - float(case.get("lat"))) > 0.002:
            return True
        if abs(float(weather.get("lon")) - float(case.get("lon"))) > 0.002:
            return True
    except Exception:
        return True
    return False

def ensure_case_weather(case: dict, force: bool = False, persist: bool = False) -> dict:
    if case.get("lat") is None or case.get("lon") is None:
        weather = case.get("weather") or fallback_weather_snapshot()
        case["weather"] = weather
        return weather
    if not force and not weather_snapshot_stale(case):
        return case.get("weather") or fallback_weather_snapshot(case.get("lat"), case.get("lon"))
    try:
        weather = fetch_open_meteo_weather(case["lat"], case["lon"])
    except Exception as exc:
        previous = case.get("weather") or {}
        if previous.get("category") in WEATHER_MODIFIERS and previous.get("source") != "fallback":
            previous["error"] = str(exc)
            return previous
        weather = fallback_weather_snapshot(case.get("lat"), case.get("lon"), str(exc))
    case["weather"] = weather
    if persist and case.get("id"):
        db_save_case(case)
    return weather

def weather_badge_text(case: dict) -> str:
    weather = ensure_case_weather(case, persist=True)
    icon = WEATHER_ICONS.get(weather.get("category", "Clear"), "☀️")
    label = weather.get("label") or weather.get("category", "Clear")
    temp = weather.get("temperature_c")
    temp_part = f" · {float(temp):.0f}°C" if isinstance(temp, (int, float)) else ""
    source = weather.get("source", "weather")
    return f"{icon} {weather.get('category', 'Clear')} · {label}{temp_part} · {source}"

INCIDENT_BASE_RISK = {
    "Flood": 38,
    "Wildfire": 45,
    "Mountain / Forest": 38,
    "Urban Area": 24,
    "Missing Person": 30,
    "Other": 25,
}

LOCATION_RISK_RULES = [
    ("water nearby", 16, ["river", "lake", "pond", "canal", "harbor", "sea", "beach", "bridge", "dam", "waterfall", "flood", "riverside"], ["Dive Rescue"]),
    ("remote terrain", 14, ["forest", "woods", "mountain", "trail", "valley", "cliff", "cave", "ravine", "wilderness", "park"], ["Mountain Rescue", "Forest / Wilderness"]),
    ("fire fuel zone", 10, ["dry grass", "wildfire", "smoke", "burn", "brush", "campfire"], ["Firefighter"]),
    ("industrial hazard", 9, ["factory", "warehouse", "construction", "abandoned", "rail", "station", "tunnel", "substation"], ["General Search"]),
    ("traffic corridor", 8, ["highway", "road", "motorway", "parking", "intersection", "bus stop"], ["General Search"]),
    ("dense urban area", 5, ["mall", "market", "downtown", "metro", "subway", "apartment", "school", "stadium"], ["General Search"]),
]

CIRCUMSTANCE_RISK_RULES = [
    ("medical vulnerability", 18, ["diabetes", "diabetic", "insulin", "heart", "seizure", "epilepsy", "dementia", "alzheimer", "autism", "medication"], ["Paramedic / Medic"]),
    ("reported injury", 18, ["injured", "bleeding", "broken", "fall", "collapsed", "unconscious", "hypothermia", "heatstroke"], ["Paramedic / Medic"]),
    ("violence or coercion concern", 20, ["abduct", "kidnap", "violence", "threat", "attack", "domestic", "stalker"], ["General Search"]),
    ("lost communication", 8, ["phone off", "no signal", "battery dead", "not answering", "last call"], ["General Search"]),
    ("low visibility or exposure", 10, ["night", "dark", "storm", "snow", "fog", "cold", "heat", "rain"], ["General Search"]),
]

def get_time_risk():
    h=datetime.now().hour
    if 21<=h or h<5: return 20,"🌙 Night"
    if 5<=h<7 or 18<=h<21: return 10,"🌆 Dusk/Dawn"
    return 0,"☀️ Daytime"

def hours_missing_risk(hours):
    h=float(hours or 0)
    if h<=1: return 0
    if h<=3: return 4
    if h<=6: return 8
    if h<=12: return 14
    if h<=24: return 22
    if h<=48: return 30
    if h<=72: return 38
    return 45

def age_risk(age):
    a=int(age or 0)
    if a<=5: return 24, "very young child"
    if a<=11: return 18, "child"
    if a<=17: return 8, "teen"
    if a>=75: return 18, "elderly adult"
    if a>=60: return 14, "senior"
    return 0, "adult"

def _collect_rule_hits(text, rules):
    hits, points, skills = [], 0, []
    lower=(text or "").lower()
    for label, pts, keywords, needed in rules:
        if any(k in lower for k in keywords):
            hits.append(label)
            points += pts
            skills.extend(needed)
    return hits, points, skills

def deterministic_case_risk(case):
    category=case.get("category","Other")
    weather_info=ensure_case_weather(case)
    weather=weather_info.get("category","Clear")
    base=INCIDENT_BASE_RISK.get(category, INCIDENT_BASE_RISK["Other"])
    weather_points=WEATHER_MODIFIERS.get(weather,{}).get(category,0)
    time_points,time_label=get_time_risk()
    missing_points=hours_missing_risk(case.get("time_missing",0))
    age_points, age_label=age_risk(case.get("age",0))
    text=f"{case.get('location','')} {case.get('description','')}"
    loc_hits, loc_points, loc_skills = _collect_rule_hits(text, LOCATION_RISK_RULES)
    circumstance_hits, circumstance_points, circumstance_skills = _collect_rule_hits(text, CIRCUMSTANCE_RISK_RULES)
    if case.get("location_source") != "map" and not (case.get("location") or "").strip():
        loc_hits.append("unknown last location")
        loc_points += 18
    elif case.get("location_source") != "map" and len((case.get("location") or "").strip()) < 8:
        loc_hits.append("vague last location")
        loc_points += 12
    if category=="Flood" and "water nearby" in loc_hits:
        loc_points += 8
        loc_hits.append("flood-water location match")
    if category=="Wildfire" and ("remote terrain" in loc_hits or "fire fuel zone" in loc_hits):
        loc_points += 10
        loc_hits.append("wildfire fuel/terrain match")
    if category=="Mountain / Forest" and "remote terrain" in loc_hits:
        loc_points += 8
        loc_hits.append("mountain/forest location match")
    raw=base+weather_points+time_points+missing_points+age_points+loc_points+circumstance_points
    score=clamp_score(raw,5,100)
    label,_=get_priority(score)
    spec=DISASTER_TEAMS.get(category, DISASTER_TEAMS["Other"])
    required=[]
    for skill in spec.get("required",[])+loc_skills+circumstance_skills+spec.get("preferred",[])[:1]:
        if skill and skill not in required:
            required.append(skill)
    if not required:
        required=["General Search"]
    factors=[
        f"{category} baseline +{base}",
        f"{weather} weather {weather_points:+d}",
        f"{case.get('time_missing',0)}h missing +{missing_points}",
        f"age {case.get('age',0)} ({age_label}) +{age_points}",
        f"{time_label} +{time_points}",
    ]
    factors.extend([f"location: {x}" for x in loc_hits])
    factors.extend([f"circumstance: {x}" for x in circumstance_hits])
    radius=1.0
    if category in ["Mountain / Forest","Flood","Wildfire"]:
        radius=2.5
    radius += min(8.0, float(case.get("time_missing") or 0) * 0.18)
    if "remote terrain" in loc_hits:
        radius += 1.5
    action = {
        "CRITICAL": "Dispatch immediately, form a multi-skill team, and start high-priority field search.",
        "HIGH": "Assign a team now and begin structured search from the last known location.",
        "MEDIUM": "Open active search, verify last-seen details, and monitor escalation triggers.",
        "LOW": "Log report, verify details, and keep volunteers on standby.",
    }[label]
    reasoning=(
        f"Risk is {score}/100 ({label}) from {category.lower()} baseline, "
        f"{weather.lower()} weather, {case.get('time_missing',0)} hours missing, "
        f"age {case.get('age',0)} ({age_label}), and last-location hazards: {', '.join(loc_hits) if loc_hits else 'none detected'}."
    )
    return {
        "priority_score": score,
        "reasoning": reasoning,
        "required_skills": required,
        "risk_factors": factors,
        "recommended_action": action,
        "estimated_search_radius_km": round(radius,1),
        "risk_breakdown": {
            "base_points": base,
            "weather": weather,
            "weather_points": weather_points,
            "time_of_day_label": time_label,
            "time_of_day_points": time_points,
            "hours_missing_points": missing_points,
            "age_points": age_points,
            "location_points": loc_points,
            "circumstance_points": circumstance_points,
            "raw_score": raw,
        }
    }

def rescore_legacy_cases():
    """Re-score old cases that were created before the deterministic risk model."""
    changed = False
    for case in st.session_state.get("cases", []):
        if case.get("risk_breakdown") or is_case_closed(case):
            continue
        assessed = deterministic_case_risk(case)
        case.update({
            "priority_score": assessed["priority_score"],
            "reasoning": assessed["reasoning"],
            "required_skills": assessed.get("required_skills", []),
            "risk_factors": assessed.get("risk_factors", []),
            "recommended_action": assessed.get("recommended_action", ""),
            "search_radius_km": assessed.get("estimated_search_radius_km", 2),
            "search_radius_base_km": assessed.get("estimated_search_radius_km", 2),
            "risk_breakdown": assessed.get("risk_breakdown", {}),
        })
        db_save_case(case)
        changed = True
    if changed:
        refresh_next_case_id()

def compute_dynamic_risk(case):
    weather_info=ensure_case_weather(case, persist=True)
    weather=weather_info.get("category","Clear")
    w_mod=WEATHER_MODIFIERS.get(weather,{}).get(case.get("category","Other"),0)
    t_mod,t_label=get_time_risk()
    breakdown=case.get("risk_breakdown") or {}
    if breakdown:
        total=(w_mod-int(breakdown.get("weather_points",0)))+(t_mod-int(breakdown.get("time_of_day_points",0)))
    else:
        total=w_mod+t_mod
    effective=clamp_score(case["priority_score"]+total)
    eff_label,eff_cls=get_priority(effective)
    return {"weather":weather,"w_icon":WEATHER_ICONS.get(weather,""),"w_mod":w_mod,
            "t_mod":t_mod,"total":total,"effective":effective,
            "eff_label":eff_label,"eff_cls":eff_cls,"t_label":t_label}

                                                                                
DISASTER_TEAMS={
    "Flood":            {"icon":"🌊","required":["Dive Rescue"],"preferred":["Paramedic / Medic","General Search"],"size":3,"note":"Dive team + medic + support"},
    "Wildfire":         {"icon":"🔥","required":["Firefighter"],"preferred":["Paramedic / Medic","Mountain Rescue"],"size":4,"note":"Fire suppression + evacuation + medic"},
    "Mountain / Forest":{"icon":"⛰️","required":["Mountain Rescue"],"preferred":["K9 Handler","Paramedic / Medic"],"size":3,"note":"Alpine specialists + K9"},
    "Urban Area":       {"icon":"🏙️","required":["General Search"],"preferred":["Paramedic / Medic","K9 Handler"],"size":2,"note":"Search team + medic"},
    "Missing Person":   {"icon":"🔍","required":["General Search"],"preferred":["K9 Handler","Paramedic / Medic"],"size":2,"note":"Search + K9 tracker"},
    "Other":            {"icon":"🚨","required":[],"preferred":["General Search","Paramedic / Medic"],"size":2,"note":"General response team"},
}

SKILL_GROUPS = {
    "Dive Rescue": ["Dive Rescue"],
    "Firefighter": ["Firefighter"],
    "Mountain Rescue": ["Mountain Rescue", "Forest / Wilderness"],
    "Forest / Wilderness": ["Forest / Wilderness", "Mountain Rescue"],
    "K9 Handler": ["K9 Handler"],
    "Paramedic / Medic": ["Paramedic / Medic"],
    "General Search": ["General Search", "Forest / Wilderness", "Mountain Rescue", "K9 Handler"],
}

def skill_match_level(vol_skill: str, desired_skills: list[str]) -> int:
    """0 exact, 1 compatible, 2 weak/no match."""
    if not desired_skills:
        return 1
    if vol_skill in desired_skills:
        return 0
    compatible = set()
    for skill in desired_skills:
        compatible.update(SKILL_GROUPS.get(skill, [skill]))
    return 1 if vol_skill in compatible else 2

def _unique_roles(roles: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for role in roles:
        key = (role["label"], tuple(role.get("skills", [])))
        if key not in seen:
            seen.add(key)
            result.append(role)
    return result

def team_requirements_for_case(case: dict) -> list[dict]:
    """Build risk-aware role slots from incident type, AI skills, weather/time risk and vulnerability."""
    spec = DISASTER_TEAMS.get(case.get("category", "Other"), DISASTER_TEAMS["Other"])
    dr = compute_dynamic_risk(case)
    effective = dr["effective"]
    weather = dr["weather"]
    age = int(case.get("age") or 0)
    hours_missing = float(case.get("time_missing") or 0)

    roles = []
    for skill in spec["required"]:
        roles.append({"label": skill, "skills": [skill], "priority": "required"})
    for skill in case.get("required_skills", []):
        if skill in SKILL_GROUPS:
            roles.append({"label": skill, "skills": [skill], "priority": "ai"})
    for skill in spec["preferred"]:
        roles.append({"label": skill, "skills": [skill], "priority": "preferred"})

    if effective >= 65 or age < 12 or age >= 60:
        roles.append({"label": "Medical cover", "skills": ["Paramedic / Medic"], "priority": "risk"})
    if effective >= 85 or dr["total"] >= 20:
        roles.append({"label": "Search lead", "skills": ["General Search", "Mountain Rescue"], "priority": "risk"})
    if case.get("category") == "Wildfire" or weather == "Extreme Heat":
        roles.append({"label": "Fire suppression", "skills": ["Firefighter"], "priority": "risk"})
        roles.append({"label": "Evacuation medic", "skills": ["Paramedic / Medic"], "priority": "risk"})
    if case.get("category") == "Flood" or weather in ["Rain", "Storm"]:
        roles.append({"label": "Water rescue", "skills": ["Dive Rescue"], "priority": "risk"})
    if case.get("category") == "Mountain / Forest" or weather in ["Snow", "Fog"]:
        roles.append({"label": "Terrain search", "skills": ["Mountain Rescue", "Forest / Wilderness"], "priority": "risk"})
    if hours_missing >= 6:
        roles.append({"label": "Tracker", "skills": ["K9 Handler", "General Search"], "priority": "risk"})

    base_size = spec["size"]
    if effective >= 85:
        target_size = base_size + 1
    elif effective >= 65 or dr["total"] >= 15:
        target_size = base_size
    else:
        target_size = max(1, base_size - 1)
    target_size = min(5, max(1, target_size))

    roles = _unique_roles(roles)
    while len(roles) < target_size:
        roles.append({"label": "Support search", "skills": ["General Search", "Mountain Rescue", "Forest / Wilderness"], "priority": "support"})
    return roles[:target_size]

def volunteer_team_score(vol: dict, case: dict, role: dict) -> tuple:
    distance = haversine(vol["lat"], vol["lon"], case["lat"], case["lon"])
    match_level = skill_match_level(vol.get("skill", ""), role.get("skills", []))
    online_penalty = 0 if vol.get("online_status") == "online" else 8
    status_penalty = 0 if vol.get("status") == "active" else 100
    priority_penalty = {"required": 0, "ai": 3, "risk": 5, "preferred": 8, "support": 12}.get(role.get("priority"), 10)
    skill_penalty = [0, 15, 45][match_level]
    return (status_penalty + online_penalty + priority_penalty + skill_penalty + distance * 4, match_level, distance)

def build_team_for_case(case, available_vols):
    """Select a risk-aware team. Returns list of (vol, role_tag)."""
    roles = team_requirements_for_case(case)
    assigned = []
    remaining = [v for v in available_vols if v.get("status") == "active" and v.get("online_status") != "offline"]
    for role in roles:
        if not remaining:
            break
        best = min(remaining, key=lambda v: volunteer_team_score(v, case, role))
        score = volunteer_team_score(best, case, role)
        match_level, distance = score[1], score[2]
        match_label = ["skill match", "compatible skill", "nearest cover"][match_level]
        role_icon = {"required": "🔴", "ai": "🧠", "risk": "⚠️", "preferred": "🟡", "support": "🔵"}.get(role.get("priority"), "🔵")
        assigned.append((best, f"{role_icon} {role['label']} · {distance:.1f}km · {match_label}"))
        remaining = [v for v in remaining if v["id"] != best["id"]]
    return assigned

def assign_team_to_case(case: dict, team: list[tuple[dict, str]]):
    for vol, role in team:
        vol["status"] = "busy"
        vol["assigned"] = case["id"]
    case["assigned_to"] = team[0][0]["id"] if team else None
    case["team_ids"] = [vol["id"] for vol, _ in team]
    case["team_roles"] = {vol["id"]: role for vol, role in team}
    case["assignment_mode"] = "team" if len(team) > 1 else "single"
    case["status"] = "assigned" if team else case.get("status", "new")
    db_save_case(case)

def release_case_assignment(case: dict, new_status: str = "new"):
    assigned_ids = []
    if case.get("assigned_to"):
        assigned_ids.append(case["assigned_to"])
    assigned_ids.extend(case.get("team_ids", []))
    for vid in dict.fromkeys(assigned_ids):
        vol = next((v for v in st.session_state.volunteers if v["id"] == vid), None)
        if vol and vol.get("assigned") == case.get("id"):
            vol["status"] = "active"
            vol["assigned"] = None
    case["assigned_to"] = None
    case["team_ids"] = []
    case["team_roles"] = {}
    case["assignment_mode"] = None
    if is_case_active(case):
        case["status"] = new_status
    db_save_case(case)

def _case_by_id(case_id: str):
    return next((c for c in st.session_state.cases if c.get("id") == case_id), None)

def build_recommended_team_action(case_id: str):
    case = _case_by_id(case_id)
    if not case:
        return
    release_case_assignment(case)
    team = build_team_for_case(case, assignable_volunteers())
    if team:
        assign_team_to_case(case, team)
        detail = ", ".join(f"{v['name']} ({role})" for v, role in team)
        add_notification(f"[{datetime.now().strftime('%H:%M')}] 👥 Team → {case_id}: {', '.join(v['name'] for v,_ in team)}")
        add_ai_log({"time":datetime.now().strftime("%H:%M:%S"),"event":f"👥 Team built {case_id}","detail":detail,"score":None})

def release_team_action(case_id: str):
    case = _case_by_id(case_id)
    if not case:
        return
    release_case_assignment(case)
    add_notification(f"[{datetime.now().strftime('%H:%M')}] ↩️ Team released for {case_id}")

def manual_add_to_team_action(case_id: str, volunteer_key: str, role_key: str):
    case = _case_by_id(case_id)
    pick = st.session_state.get(volunteer_key)
    role_label = st.session_state.get(role_key, "Team support")
    if not case or not pick:
        return
    current_ids = list(dict.fromkeys(case.get("team_ids", []) or ([case.get("assigned_to")] if case.get("assigned_to") else [])))
    vol = next((v for v in st.session_state.volunteers if v["id"] == pick), None)
    if not vol:
        return
    vol["status"] = "busy"
    vol["assigned"] = case_id
    ids = list(dict.fromkeys(current_ids + [pick]))
    case["team_ids"] = ids
    case["assigned_to"] = ids[0]
    case["team_roles"] = dict(case.get("team_roles", {}) or {})
    case["team_roles"][pick] = f"✋ Manual · {role_label}"
    case["assignment_mode"] = "team" if len(ids) > 1 else "single"
    case["status"] = "assigned"
    db_save_case(case)
    add_notification(f"[{datetime.now().strftime('%H:%M')}] ✋ {vol['name']} manually added to {case_id}")

def manual_remove_from_team_action(case_id: str, remove_key: str):
    case = _case_by_id(case_id)
    remove_id = st.session_state.get(remove_key)
    if not case or not remove_id:
        return
    current_ids = list(dict.fromkeys(case.get("team_ids", []) or ([case.get("assigned_to")] if case.get("assigned_to") else [])))
    vol = next((v for v in st.session_state.volunteers if v["id"] == remove_id), None)
    if vol and vol.get("assigned") == case_id:
        vol["status"] = "active"
        vol["assigned"] = None
    ids = [vid for vid in current_ids if vid != remove_id]
    roles_map = dict(case.get("team_roles", {}) or {})
    roles_map.pop(remove_id, None)
    case["team_ids"] = ids
    case["team_roles"] = roles_map
    case["assigned_to"] = ids[0] if ids else None
    case["assignment_mode"] = "team" if len(ids) > 1 else "single" if ids else None
    case["status"] = "assigned" if ids else "new"
    db_save_case(case)
    add_notification(f"[{datetime.now().strftime('%H:%M')}] ✋ {remove_id} removed from {case_id}")

def open_page_action(page: str):
    st.session_state.active_page = page
    st.query_params["page"] = page

def close_case_found_action(case_id: str, actor_role: str = "volunteer", note_key: str | None = None):
    case = _case_by_id(case_id)
    if not case:
        return
    user = st.session_state.get("current_user", {})
    note = st.session_state.get(note_key, "") if note_key else ""
    default_note = "Reporter marked the person as returned / safe." if actor_role == "reporter" else "Marked found by volunteer."
    close_case_as_found(
        case,
        actor_name=user.get("name", "Reporter" if actor_role == "reporter" else "Volunteer"),
        actor_role=actor_role,
        note=note or default_note,
    )
    add_notification(f"[{datetime.now().strftime('%H:%M')}] ✅ Search closed for {case_id}")

def assign_ai_volunteer_action(case_id: str):
    case = _case_by_id(case_id)
    if not case:
        return
    available = assignable_volunteers()
    if not available:
        add_notification(f"[{datetime.now().strftime('%H:%M')}] ⚠️ No available volunteers for {case_id}")
        return
    res = ai_assign_volunteer(case, available)
    vol = next((v for v in st.session_state.volunteers if v["id"] == res.get("volunteer_id")), None)
    if not vol:
        add_notification(f"[{datetime.now().strftime('%H:%M')}] ⚠️ No reachable volunteer assigned for {case_id}")
        return
    vol["status"] = "busy"
    vol["assigned"] = case_id
    case["assigned_to"] = vol["id"]
    case["status"] = "assigned"
    db_save_case(case)
    add_notification(f"[{datetime.now().strftime('%H:%M')}] 🎯 {case_id} → {vol['name']}")

def join_team_action(case_id: str, volunteer_id: str):
    case = _case_by_id(case_id)
    my_vol = next((v for v in st.session_state.volunteers if v.get("id") == volunteer_id), None)
    if not case or not my_vol:
        return
    if not case.get("team_ids"):
        case["team_ids"] = [case["assigned_to"]] if case.get("assigned_to") else []
    case.setdefault("team_roles", {})
    if case.get("assigned_to") and case["assigned_to"] not in case["team_roles"]:
        case["team_roles"][case["assigned_to"]] = "🔴 Lead responder"
    suggested = build_team_for_case(case, [my_vol])
    role = suggested[0][1] if suggested else "🔵 Support search"
    my_vol["status"] = "busy"
    my_vol["assigned"] = case_id
    case["team_ids"].append(my_vol["id"])
    case["team_ids"] = list(dict.fromkeys(case["team_ids"]))
    case["team_roles"][my_vol["id"]] = role
    case["assignment_mode"] = "team"
    db_save_case(case)
    add_notification(f"[{datetime.now().strftime('%H:%M')}] ➕ {my_vol['name']} joined team for {case_id}")
    add_ai_log({"time":datetime.now().strftime("%H:%M:%S"),"event":f"➕ Team member joined {case_id}","detail":f"{my_vol['name']} · {role}","score":None})

def set_volunteer_status_action(vol_id: str, status: str):
    vol = next((v for v in st.session_state.volunteers if v.get("id") == vol_id), None)
    if not vol:
        return
    vol["status"] = status
    if status == "offline":
        db_set_offline(vol_id)

def team_names_for_case(case: dict) -> list[str]:
    names = []
    for tid in case.get("team_ids", []):
        vol = next((v for v in st.session_state.volunteers if v["id"] == tid), None)
        if vol:
            names.append(vol["name"])
    return names

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

CASE_CONTEXT_PHOTOS = {
    "Flood": "https://picsum.photos/seed/findfirst-flood-water/320/320",
    "Wildfire": "https://picsum.photos/seed/findfirst-wildfire-field/320/320",
    "Mountain / Forest": "https://picsum.photos/seed/findfirst-mountain-forest/320/320",
    "Urban Area": "https://picsum.photos/seed/findfirst-urban-search/320/320",
    "Missing Person": "https://picsum.photos/seed/findfirst-search-path/320/320",
    "Other": "https://picsum.photos/seed/findfirst-rescue-field/320/320",
}

COMMONS_FILE_BASE = "https://commons.wikimedia.org/wiki/Special:Redirect/file/"
NAV_PHOTO_FILES = {
    "dashboard": "Font Awesome 5 solid tachometer-alt.svg",
    "my_missions": "Font Awesome 5 solid bullseye.svg",
    "all_cases": "Font Awesome 5 solid folder-open.svg",
    "teams": "Font Awesome 5 solid users.svg",
    "volunteers": "Font Awesome 5 solid user-friends.svg",
    "tracking": "Font Awesome 5 solid map-marker-alt.svg",
    "ai_log": "Font Awesome 5 solid robot.svg",
    "report_case": "Font Awesome 5 solid clipboard-list.svg",
    "my_cases": "Font Awesome 5 solid folder-open.svg",
}

def commons_file_url(filename: str, width: int = 96) -> str:
    return f"{COMMONS_FILE_BASE}{urllib.parse.quote(filename)}?width={width}"

def nav_photo_url(page_id: str) -> str:
    return commons_file_url(NAV_PHOTO_FILES.get(page_id, NAV_PHOTO_FILES["dashboard"]))

def case_photo_html(case: dict) -> str:
    uploaded = case.get("photo_data_url")
    if uploaded:
        return f'<img class="missing-photo" src="{uploaded}" alt="Missing person photo">'
    category = case.get("category", "Other")
    url = CASE_CONTEXT_PHOTOS.get(category, CASE_CONTEXT_PHOTOS["Other"])
    return f'<img class="missing-photo missing-photo-context" src="{url}" alt="{category} context photo" loading="lazy">'



                                                                               
                                                                       
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
                                                                                        
    h = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    lat_offset = ((h % 2000) - 1000) / 100000                 
    lon_offset = (((h // 2000) % 2000) - 1000) / 100000
    return default[0] + lat_offset, default[1] + lon_offset

def get_report_map_selection():
    draft_id = ensure_report_draft_id()
    qp_draft = st.query_params.get("report_draft")
    try:
        lat = float(st.query_params.get("report_lat", ""))
        lon = float(st.query_params.get("report_lon", ""))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            if qp_draft and qp_draft != draft_id:
                draft_id = qp_draft
                st.session_state.report_draft_id = qp_draft
            st.session_state.report_map_point = (lat, lon)
            st.session_state.report_selected_lat = lat
            st.session_state.report_selected_lon = lon
            st.session_state.report_lat = lat
            st.session_state.report_lon = lon
            if draft_id:
                db_save_report_location(draft_id, lat, lon)
            return lat, lon
    except Exception:
        pass
    map_state = st.session_state.get(f"report_location_map_{draft_id}") if draft_id else None
    clicked = (map_state or {}).get("last_clicked") if isinstance(map_state, dict) else None
    if clicked and clicked.get("lat") is not None and clicked.get("lng") is not None:
        try:
            lat = float(clicked["lat"])
            lon = float(clicked["lng"])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                st.session_state.report_map_point = (lat, lon)
                st.session_state.report_selected_lat = lat
                st.session_state.report_selected_lon = lon
                db_save_report_location(draft_id, lat, lon)
                return lat, lon
        except Exception:
            pass
    if draft_id:
        loc = db_get_report_location(draft_id)
        if loc:
            lat, lon = float(loc["lat"]), float(loc["lon"])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                st.session_state.report_map_point = (lat, lon)
                return lat, lon
    for key in ("report_selected_lat", "report_lat"):
        paired_key = "report_selected_lon" if key == "report_selected_lat" else "report_lon"
        if key in st.session_state and paired_key in st.session_state:
            try:
                lat = float(st.session_state[key])
                lon = float(st.session_state[paired_key])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    st.session_state.report_map_point = (lat, lon)
                    return lat, lon
            except Exception:
                pass
    saved = st.session_state.get("report_map_point")
    if saved:
        try:
            lat, lon = float(saved[0]), float(saved[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                st.session_state.report_selected_lat = lat
                st.session_state.report_selected_lon = lon
                return lat, lon
        except Exception:
            st.session_state.pop("report_map_point", None)
    return None

def clear_report_map_selection():
    st.session_state.pop("report_map_point", None)
    st.session_state.pop("report_selected_lat", None)
    st.session_state.pop("report_selected_lon", None)
    st.session_state.pop("report_lat", None)
    st.session_state.pop("report_lon", None)
    db_clear_report_location(st.session_state.get("report_draft_id"))
    keep_params = {k: v for k, v in st.query_params.items() if k not in {"report_lat", "report_lon", "report_draft"}}
    st.query_params.clear()
    for k, v in keep_params.items():
        st.query_params[k] = v

def render_report_location_picker():
    draft_id = ensure_report_draft_id()
    selected = get_report_map_selection()
    center_lat, center_lon = selected or DEFAULT_CENTER
    st.markdown(
        '<div class="address-hint">Click the last known point on the map. The selected coordinates are saved before the report is submitted.</div>',
        unsafe_allow_html=True,
    )
    if HAS_STREAMLIT_FOLIUM:
        fmap = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=13 if selected else 11,
            tiles=None,
            control_scale=True,
        )
        folium.TileLayer(
            "OpenStreetMap",
            name="OpenStreetMap",
            control=False,
        ).add_to(fmap)
        if selected:
            folium.Marker(
                [selected[0], selected[1]],
                tooltip="Selected last known point",
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(fmap)
        map_state = st_folium(
            fmap,
            key=f"report_location_map_{draft_id}",
            height=360,
            use_container_width=True,
            returned_objects=["last_clicked"],
        )
        clicked = (map_state or {}).get("last_clicked") if isinstance(map_state, dict) else None
        if clicked and clicked.get("lat") is not None and clicked.get("lng") is not None:
            try:
                lat = float(clicked["lat"])
                lon = float(clicked["lng"])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    st.session_state.report_map_point = (lat, lon)
                    st.session_state.report_selected_lat = lat
                    st.session_state.report_selected_lon = lon
                    st.session_state.report_lat = lat
                    st.session_state.report_lon = lon
                    db_save_report_location(draft_id, lat, lon)
            except Exception:
                pass
        return

    marker_js = ""
    if selected:
        marker_js = f"setMarker({selected[0]:.6f}, {selected[1]:.6f}, false);"
    streamlit.components.v1.html(f"""<!DOCTYPE html><html><head>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
html,body,#report-map{{height:100%;margin:0;background:#000000;font-family:Inter,Arial,sans-serif}}
.hint{{position:absolute;z-index:999;top:10px;left:10px;right:10px;background:rgba(15,23,42,.92);color:#e5e7eb;border:1px solid rgba(148,163,184,.35);border-radius:8px;padding:8px 10px;font-size:12px;line-height:1.35}}
.coords{{font-family:monospace;color:#86efac}}
</style></head><body>
<div id="report-map"></div>
<div class="hint">Click the last known point on the map. <span id="coords" class="coords">{f'{selected[0]:.6f}, {selected[1]:.6f}' if selected else 'No point selected yet'}</span></div>
<script>
const map=L.map('report-map',{{center:[{center_lat:.6f},{center_lon:.6f}],zoom:{13 if selected else 11},preferCanvas:true}});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'&copy; OpenStreetMap'}}).addTo(map);
let marker=null;
function setMarker(lat,lon,save){{
  if(marker) marker.setLatLng([lat,lon]);
  else marker=L.marker([lat,lon],{{draggable:true}}).addTo(map);
  document.getElementById('coords').textContent=lat.toFixed(6)+', '+lon.toFixed(6);
  marker.on('dragend',function(e){{
    const p=e.target.getLatLng();
    persist(p.lat,p.lng);
  }});
  if(save) persist(lat,lon);
}}
function persist(lat,lon){{
  const params=new URLSearchParams(window.parent.location.search);
  params.set('report_lat',lat.toFixed(6));
  params.set('report_lon',lon.toFixed(6));
  params.set('report_draft','{draft_id}');
  params.set('page','report_case');
  const next=params.toString();
  const current=window.parent.location.search.replace(/^\\?/,'');
  if(current!==next){{
    document.getElementById('coords').textContent=lat.toFixed(6)+', '+lon.toFixed(6)+' · saving...';
    const target=window.parent.location.pathname+'?'+next+window.parent.location.hash;
    window.parent.location.href=target;
  }}
}}
map.on('click',function(e){{setMarker(e.latlng.lat,e.latlng.lng,true);}});
{marker_js}
</script></body></html>""", height=360)

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

                                                                                 
                    
                                                                                 
def init_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in=False; st.session_state.current_user=None
        token = st.query_params.get("session_token")
        if token:
            uname = get_session_user(token)
            if uname:
                user = get_users().get(uname)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.current_user = session_user(uname, user)
                    st.session_state.active_page = st.query_params.get("page", "dashboard")
                    st.session_state._session_token = token
                    apply_theme_for_user(uname, user)
    if "cases" not in st.session_state:
        st.session_state.cases=[]
    if "volunteers" not in st.session_state:
        st.session_state.volunteers=[
            {"id":"V001","name":"Ivan Petrov",   "address":"Independence Square, Kyiv", "lat":50.45,"lon":30.52,"status":"active","skill":"Mountain Rescue",   "assigned":None,"username":"ivan",  "online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None},
            {"id":"V002","name":"Sarah Mitchell","address":"Olympic Stadium, Kyiv",     "lat":50.43,"lon":30.55,"status":"active","skill":"Paramedic / Medic", "assigned":None,"username":"sarah", "online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None},
            {"id":"V003","name":"Mike Torres",   "address":"Podil River Station, Kyiv", "lat":50.47,"lon":30.48,"status":"active","skill":"Dive Rescue",       "assigned":None,"username":"mike","online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None},
            {"id":"V004","name":"Admin",         "address":"Kyiv Central Station",     "lat":50.45,"lon":30.52,"status":"active","skill":"General Search",    "assigned":None,"username":"admin", "online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None},
        ]
                                                                
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
    saved_gps = db_get_all_vol_gps()
    for vol in st.session_state.get("volunteers", []):
        gps = saved_gps.get(vol["id"])
        if gps and gps.get("lat") is not None and gps.get("lon") is not None:
            vol["lat"], vol["lon"] = gps["lat"], gps["lon"]
            if gps.get("address"):
                vol["address"] = gps["address"]
    if "notifications"  not in st.session_state: st.session_state.notifications=[]
    if "ai_log"         not in st.session_state: st.session_state.ai_log=[]
    if "next_case_id"   not in st.session_state: st.session_state.next_case_id=1
    if "active_page"    not in st.session_state: st.session_state.active_page="dashboard"
    if "checkins"       not in st.session_state: st.session_state.checkins=[]

init_state()
if st.session_state.get("logged_in") and st.session_state.get("current_user"):
    account_theme = st.session_state.current_user.get("preferred_theme")
    if account_theme in ("light", "dark") and account_theme != APP_THEME:
        st.session_state.ui_theme = account_theme
        st.query_params["theme"] = account_theme
        st.rerun()
sync_operational_state_from_db()

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
    refresh_next_case_id()

remove_default_demo_case()
sync_cases_from_db()
rescore_legacy_cases()
ensure_address_fields()
sync_volunteer_assignments_from_cases()
inject_live_clock_js()
inject_heartbeat_badge_js()

                                                                                 
              
                                                                                 
def ai_score_case(case):
    deterministic = deterministic_case_risk(case)
    prompt=f"""You are an AI search-and-rescue coordinator. Analyze the case and return JSON only.
CASE: Name:{case['name']}, Age:{case['age']}, Category:{case['category']}
Location:{case['location']}, Description:{case['description']}, Missing:{case['time_missing']}h
Return ONLY valid JSON (no markdown):
{{"priority_score":<0-100>,"reasoning":"<2-3 sentences>","required_skills":["<s1>"],"risk_factors":["<f1>"],"recommended_action":"<action>","estimated_search_radius_km":<num>}}"""
    try:
        if client:
            r=client.chat.completions.create(model="llama-3.3-70b-versatile",max_tokens=500,
                messages=[{"role":"user","content":prompt}])
            ai = parse_json(r.choices[0].message.content)
            if ai.get("reasoning"):
                deterministic["reasoning"] = f"{deterministic['reasoning']} AI note: {ai['reasoning']}"
            ai_skills = ai.get("required_skills") or []
            deterministic["required_skills"] = list(dict.fromkeys(deterministic["required_skills"] + ai_skills))
            ai_factors = ai.get("risk_factors") or []
            deterministic["risk_factors"] = deterministic["risk_factors"] + [
                f"AI: {f}" for f in ai_factors if f
            ]
    except Exception:
        pass
    return deterministic

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
        if client:
            r=client.chat.completions.create(model="llama-3.3-70b-versatile",max_tokens=350,
                messages=[{"role":"user","content":prompt}])
            return parse_json(r.choices[0].message.content)
    except Exception:
        pass
                                                                      
    eligible = [v for v in available_vols if v.get("online_status") != "offline"]
    if not eligible:
        return {"volunteer_id": None, "reason": "No reachable volunteers (all offline).",
                "message_to_volunteer": ""}
    online = [v for v in eligible if v.get("online_status") == "online"]
    pool = online if online else eligible
    best = min(pool, key=lambda v: haversine(v['lat'], v['lon'], case['lat'], case['lon']))
    return {"volunteer_id": best["id"], "reason": "Nearest available volunteer (AI fallback).",
            "message_to_volunteer": f"Assigned to {case['id']}. Proceed to {case['location']}."}

                                                                                 
            
                                                                                 
def show_login():
    st.markdown('<div class="login-mobile-scope"></div>', unsafe_allow_html=True)
    _,col,_=st.columns([1,2,1])
    with col:
        st.markdown("""<div class="login-hero" style="text-align:center;padding:40px 0 28px">
          <div class="login-hero-title" style="font-family:var(--font-head);font-size:2rem;font-weight:800;letter-spacing:-.5px;">
            Find<span style="color:var(--red-strong)">First</span></div>
          <div class="login-hero-sub" style="font-size:.72rem;color:var(--text3);text-transform:uppercase;letter-spacing:1.5px;margin-top:4px;">
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
                if user and verify_password(user.get("password"), password):
                    uname = username.lower().strip()
                    migrate_user_password_if_needed(uname, user, password)
                    st.session_state.logged_in=True
                    st.session_state.current_user=session_user(uname, user)
                    st.session_state.active_page="dashboard"
                    apply_theme_for_user(uname, user)
                    token = create_session(uname)
                    st.session_state._session_token = token
                    st.query_params["session_token"] = token
                    st.query_params["page"] = "dashboard"
                                                           
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
                                                                                      
                        if not any(v["id"]==nid for v in st.session_state.volunteers):
                            st.session_state.volunteers.append({"id":nid,"name":su_name.strip(),"address":vol_address.strip(),"lat":vol_lat,"lon":vol_lon,"status":"active","skill":vol_skill,"assigned":None,"username":uname,"online_status":"unknown","last_heartbeat":None,"hb_source":None,"device_id":None})
                        with get_db() as conn:
                            conn.execute("INSERT OR IGNORE INTO hb_status(volunteer_id,name,hb_interval,updated_at) VALUES(?,?,?,?)",(nid,su_name.strip(),HB_DEFAULT_INTERVAL,datetime.now().isoformat()))
                    else:
                        new_user={"password":su_pw,"role":"reporter","name":su_name.strip(),"id":None}
                    new_user["preferred_theme"] = st.session_state.get("ui_theme", "light")
                    save_user(uname, new_user)
                    st.session_state.logged_in=True
                    st.session_state.current_user=session_user(uname, new_user)
                    st.session_state.active_page="dashboard"
                    apply_theme_for_user(uname, new_user)
                    token = create_session(uname)
                    st.session_state._session_token = token
                    st.query_params["session_token"] = token
                    st.query_params["page"] = "dashboard"
                    st.rerun()


                                                                                 
         
                                                                                 
def show_sidebar():
    u=st.session_state.current_user; role=u["role"]
    with st.sidebar:
        st.markdown('<div class="sidebar-logo"><div class="sidebar-logo-badge">F</div><div><div class="sidebar-logo-text">Find<span>First</span></div><div class="sidebar-logo-sub">Operations Center</div></div></div>',unsafe_allow_html=True)
        st.markdown('<div class="side-section-label" style="margin-top:14px">Appearance</div>', unsafe_allow_html=True)
        cur_theme = st.session_state.get("ui_theme", "light")
        st.markdown('<div class="theme-toggle-wrap">', unsafe_allow_html=True)
        tb_col1, tb_col2 = st.columns(2)
        with tb_col1:
            light_active = cur_theme == "light"
            if st.button("☀️ Light", key="theme_light_btn", use_container_width=True,
                         type="primary" if light_active else "secondary"):
                if not light_active:
                    set_theme_action("light")
                    st.rerun()
        with tb_col2:
            dark_active = cur_theme == "dark"
            if st.button("🌙 Dark", key="theme_dark_btn", use_container_width=True,
                         type="primary" if dark_active else "secondary"):
                if not dark_active:
                    set_theme_action("dark")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="side-section-label">Weather Conditions</div>', unsafe_allow_html=True)
        active_weather = [
            ensure_case_weather(c)
            for c in st.session_state.get("cases", [])
            if is_case_active(c)
        ]
        if active_weather:
            weather_counts = {}
            for w in active_weather:
                cat = w.get("category", "Clear")
                weather_counts[cat] = weather_counts.get(cat, 0) + 1
            weather_line = " · ".join(
                f"{WEATHER_ICONS.get(cat, '☀️')} {cat} {count}"
                for cat, count in sorted(weather_counts.items())
            )
            st.markdown(
                f'<div style="background:var(--input-bg);border:1px solid var(--input-border);border-radius:8px;padding:12px 14px;font-size:.82rem;color:var(--text2);line-height:1.5">'
                f'<b>Auto from victim map pins</b><br>{weather_line}<br><span style="color:var(--text3);font-size:.72rem">Open-Meteo · updates every {WEATHER_TTL_MINUTES} min</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:var(--input-bg);border:1px solid var(--input-border);border-radius:8px;padding:12px 14px;font-size:.82rem;color:var(--text3);line-height:1.5">'
                'Weather is detected automatically from each missing person map point.</div>',
                unsafe_allow_html=True,
            )
        active_cases=sum(1 for c in st.session_state.cases if is_case_active(c))
        free_vols=sum(1 for v in st.session_state.volunteers if v["status"]=="active")
        online_vols=sum(1 for v in st.session_state.volunteers if v.get("online_status")=="online")
        s1,s2=st.columns(2)
        with s1: st.markdown(f'<div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center;margin:8px 0 4px"><div style="font-family:var(--font-mono);font-size:1.4rem;color:var(--red-strong);font-weight:500">{active_cases}</div><div style="font-size:.6rem;color:var(--text3);text-transform:uppercase;letter-spacing:.5px">Cases</div></div>',unsafe_allow_html=True)
        with s2: st.markdown(f'<div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center;margin:8px 0 4px"><div style="font-family:var(--font-mono);font-size:1.4rem;color:var(--green);font-weight:500">{online_vols}</div><div style="font-size:.6rem;color:var(--text3);text-transform:uppercase;letter-spacing:.5px">Online</div></div>',unsafe_allow_html=True)
        st.markdown('<div style="height:8px"></div>',unsafe_allow_html=True)
        if role=="volunteer":
            pages=[("dashboard","Dashboard"),("my_missions","My Missions"),
                   ("all_cases","All Cases"),("teams","Teams"),
                   ("volunteers","Volunteers"),
                   ("tracking","Tracking & Check-ins"),("ai_log","AI Log")]
        else:
            pages=[("dashboard","Dashboard"),("report_case","Report Missing"),("my_cases","My Reports")]
        for pid,label in pages:
            is_active=st.session_state.active_page==pid
            img_col, nav_col = st.columns([0.16, 1], gap=None)
            with img_col:
                active_class = " active" if is_active else ""
                st.markdown(
                    f'<img class="sidebar-nav-photo{active_class}" src="{nav_photo_url(pid)}" alt="{label} photo" loading="lazy">',
                    unsafe_allow_html=True,
                )
            with nav_col:
                if st.button(f"{'●' if is_active else '○'}  {label}",key=f"nav_{pid}",use_container_width=True):
                    st.session_state.active_page=pid
                    st.query_params["page"] = pid
                    st.rerun()
            st.markdown('<div class="sidebar-nav-spacer"></div>', unsafe_allow_html=True)
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
                                
            if u.get("role")=="volunteer" and u.get("id"):
                db_set_offline(u["id"])
            token = st.session_state.get("_session_token")
            if token:
                delete_session(token)
            st.query_params.clear()
            st.session_state.logged_in=False; st.session_state.current_user=None; st.rerun()


                                                                                 
                      
                                                                                 
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

    add_notification(
        f"[{now.strftime('%H:%M')}] ✅ {case['id']} closed — {case['name']} marked found by {actor_name}"
    )
    add_ai_log({
        "time": now.strftime("%H:%M:%S"),
        "event": f"✅ Closed {case['id']} by {actor_role}",
        "detail": f"{case['name']} marked as found/returned. Note: {case['found_note']}",
        "score": None
    })
    db_save_case(case)

def close_case_as_unfound(case, actor_name="Unknown", actor_role="volunteer", report=None):
    now = datetime.now()
    report = report or {}
    case["status"] = "unfound"
    case["unfound_at"] = now.isoformat()
    case["unfound_by"] = actor_name
    case["unfound_by_role"] = actor_role
    case["deceased_report"] = {
        "identity_confirmed_as": report.get("identity_confirmed_as", "").strip(),
        "recovery_location": report.get("recovery_location", "").strip(),
        "confirmed_by": report.get("confirmed_by", "").strip(),
        "condition": report.get("condition", "").strip(),
        "official_reference": report.get("official_reference", "").strip(),
        "notes": report.get("notes", "").strip(),
        "created_at": now.isoformat(),
    }

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

    case["assigned_to"] = None
    case["team_ids"] = []
    case["team_roles"] = {}
    case["assignment_mode"] = None

    add_notification(
        f"[{now.strftime('%H:%M')}] ⚫ {case['id']} closed as unfound by {actor_name}"
    )
    add_ai_log({
        "time": now.strftime("%H:%M:%S"),
        "event": f"⚫ Unfound closure {case['id']}",
        "detail": f"{case['name']} closed with deceased report. Confirmed by: {case['deceased_report']['confirmed_by']}",
        "score": None
    })
    db_save_case(case)

def submit_unfound_report(case_id: str, password_key: str, identity_key: str, location_key: str, confirmed_by_key: str, condition_key: str, reference_key: str, notes_key: str):
    case = _case_by_id(case_id)
    if not case or is_case_closed(case):
        return
    password = st.session_state.get(password_key, "")
    identity = st.session_state.get(identity_key, "")
    location = st.session_state.get(location_key, "")
    confirmed_by = st.session_state.get(confirmed_by_key, "")
    condition = st.session_state.get(condition_key, "")
    reference = st.session_state.get(reference_key, "")
    notes = st.session_state.get(notes_key, "")
    if not verify_current_session_password(password):
        st.session_state[f"unfound_error_{case_id}"] = "Session password is incorrect."
        return
    missing = []
    if not identity.strip():
        missing.append("identity")
    if not location.strip():
        missing.append("recovery location")
    if not confirmed_by.strip():
        missing.append("confirmed by")
    if not condition.strip():
        missing.append("condition")
    if missing:
        st.session_state[f"unfound_error_{case_id}"] = "Missing required fields: " + ", ".join(missing)
        return
    user = st.session_state.get("current_user", {})
    close_case_as_unfound(
        case,
        actor_name=user.get("name", "Operator"),
        actor_role=user.get("role", "operator"),
        report={
            "identity_confirmed_as": identity,
            "recovery_location": location,
            "confirmed_by": confirmed_by,
            "condition": condition,
            "official_reference": reference,
            "notes": notes,
        },
    )
    st.session_state[f"unfound_open_{case_id}"] = False
    st.session_state[f"unfound_error_{case_id}"] = ""

def render_unfound_form(case):
    if not is_case_active(case):
        return
    key = f"unfound_open_{case['id']}"
    if st.button("Unfound", key=f"open_unfound_{case['id']}", use_container_width=True):
        st.session_state[key] = not st.session_state.get(key, False)
    if not st.session_state.get(key, False):
        return
    error = st.session_state.get(f"unfound_error_{case['id']}", "")
    st.markdown(
        f"""<div style="background:var(--red-dim);border:1px solid color-mix(in srgb,var(--red) 28%,transparent);border-radius:14px;padding:14px 16px;margin:10px 0;color:var(--text2)">
          <div style="font-weight:800;color:var(--red);margin-bottom:4px">Deceased / Unfound Report</div>
          <div style="font-size:.78rem;color:var(--text3)">This action closes {case['id']} and releases assigned responders. Enter your current session password and complete the report.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    if error:
        st.error(error)
    with st.form(f"unfound_form_{case['id']}"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Current session password *", type="password", key=f"unfound_password_{case['id']}")
            st.text_input("Identity confirmed as *", value=f"{case.get('name','')}, {case.get('age','')} yrs", key=f"unfound_identity_{case['id']}")
            st.text_input("Recovery location *", value=case.get("location", ""), key=f"unfound_location_{case['id']}")
        with c2:
            st.text_input("Confirmed by *", placeholder="e.g. Medical examiner, police, team lead", key=f"unfound_confirmed_by_{case['id']}")
            st.selectbox("Condition *", ["Deceased - identity confirmed", "Deceased - pending official confirmation", "Remains located", "Other"], key=f"unfound_condition_{case['id']}")
            st.text_input("Official reference", placeholder="Case/ref number if available", key=f"unfound_reference_{case['id']}")
        st.text_area("Notes", placeholder="Circumstances, handoff details, restrictions, next steps...", height=90, key=f"unfound_notes_{case['id']}")
        st.form_submit_button(
            "Confirm Unfound Closure",
            use_container_width=True,
            on_click=submit_unfound_report,
            args=(
                case["id"],
                f"unfound_password_{case['id']}",
                f"unfound_identity_{case['id']}",
                f"unfound_location_{case['id']}",
                f"unfound_confirmed_by_{case['id']}",
                f"unfound_condition_{case['id']}",
                f"unfound_reference_{case['id']}",
                f"unfound_notes_{case['id']}",
            ),
        )


def reporter_found_action(case, user):
    """Reporter-only control: original reporter can close their own active case quickly."""
    if is_case_closed(case):
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
        st.button(
            "Close search",
            key=f"reporter_quick_found_{case['id']}",
            use_container_width=True,
            type="primary",
            on_click=close_case_found_action,
            args=(case["id"], "reporter", f"reporter_found_note_{case['id']}"),
        )

def render_case_card(case, show_actions=False, is_volunteer=False, reporter_user=None):
    label,cls=get_priority(case["priority_score"]); ts=time_since(case["created_at"])
    desc=(case.get("description") or "")[:120]
    desc_suffix="..." if len(case.get("description") or "")>120 else ""
    assigned_name="—"
    team_ids = case.get("team_ids", [])
    if team_ids:
        team_names = team_names_for_case(case)
        assigned_name = f"Team ({len(team_names)}): {', '.join(team_names)}" if team_names else "Team assigned"
    elif case.get("assigned_to"):
        vol=next((v for v in st.session_state.volunteers if v["id"]==case["assigned_to"]),None)
        if vol: assigned_name=vol["name"]
    status_map={"new":"🆕 New","scoring":"⏳ Scoring","assigned":"👥 Team Assigned" if team_ids else "👤 Assigned",
                "in_progress":"🔍 In Progress","found":"✅ Found","closed":"📁 Closed","unfound":"⚫ Unfound"}
    dr=compute_dynamic_risk(case)
    weather_text=weather_badge_text(case)
    eff_cls=dr["eff_cls"] if dr["total"]!=0 else cls
    eff_label=dr["eff_label"] if dr["total"]!=0 else label
    eff_score=dr["effective"] if dr["total"]!=0 else case["priority_score"]
    risk_color="var(--orange)" if dr["total"]>0 else "var(--green)"
    risk_html=f'<span style="font-size:.67rem;color:{risk_color};font-family:var(--font-mono)">{dr["w_icon"]} {dr["total"]:+d} pts</span>' if dr["total"]!=0 else ""
    spec=DISASTER_TEAMS.get(case.get("category","Other"),DISASTER_TEAMS["Other"])
    team_tag=f'<span style="font-size:.66rem;color:var(--text3)">{spec["icon"]} {spec["note"]}</span>'
    radius_km = dynamic_search_radius_km(case)
    photo_html=case_photo_html(case)
    st.markdown(f"""<div class="case-card {eff_cls}">
      <div style="display:flex;gap:14px;align-items:flex-start">
        {photo_html}
        <div style="flex:1;min-width:0">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:8px">
            <div style="min-width:0">
              <div style="font-family:var(--font-head);font-weight:700;font-size:1.05rem">{case['name']}, {case['age']} yrs</div>
              <div style="font-size:.78rem;color:var(--text2);display:flex;gap:14px;flex-wrap:wrap;margin-top:4px">
                <span>📍 {case['location']}</span><span>🕐 {ts}</span><span>⭕ {radius_km} km radius</span><span>⚠️ {case['category']}</span><span>{weather_text}</span><span>{team_tag}</span></div>
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
        ca,cb,cc,cd,_=st.columns([1,1,1,1,1.4])
        with ca:
            if is_case_active(case):
                st.button(
                    "✅ Found",
                    key=f"found_{case['id']}",
                    on_click=close_case_found_action,
                    args=(case["id"], "volunteer", None),
                )
        with cb:
            if case.get("status")=="new":
                st.button(
                    "👤 Assign AI",
                    key=f"assign_{case['id']}",
                    on_click=assign_ai_volunteer_action,
                    args=(case["id"],),
                )
        with cc:
            if case.get("status")=="new":
                st.button(
                    "👥 Smart Team",
                    key=f"team_{case['id']}",
                    on_click=build_recommended_team_action,
                    args=(case["id"],),
                )
        with cd:
            u = st.session_state.get("current_user")
            my_vol = None
            if u and u.get("role") == "volunteer":
                my_vol = next((v for v in st.session_state.volunteers if v.get("username") == u.get("username")), None)
            can_join = (
                my_vol
                and case.get("status") == "assigned"
                and is_case_active(case)
                and my_vol["id"] not in case.get("team_ids", [])
                and my_vol.get("status") == "active"
                and my_vol.get("online_status") != "offline"
            )
            if can_join:
                st.button(
                    "➕ Join Team",
                    key=f"join_{case['id']}_{my_vol['id']}",
                    on_click=join_team_action,
                    args=(case["id"], my_vol["id"]),
                )
    if reporter_user:
        reporter_found_action(case, reporter_user)
    if is_case_active(case):
        render_unfound_form(case)
    if case.get("reasoning"):
        with st.expander(f"🤖 AI Analysis · {case['id']}"):
            if dr["total"]!=0:
                w_str=f"{dr['w_mod']:+d}" if isinstance(dr.get("w_mod"), int) else str(dr.get("w_mod",0))
                t_str=f"{dr['t_mod']:+d}" if isinstance(dr.get("t_mod"), int) else str(dr.get("t_mod",0))
                dyn_color="var(--orange)" if dr["total"]>0 else "var(--green)"
                dyn_bg="var(--orange-dim)" if dr["total"]>0 else "var(--green-dim)"
                st.markdown(f"""<div style="background:{dyn_bg};border:1px solid rgba(249,115,22,.2);border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:.78rem;color:{dyn_color}">⚡ Dynamic risk: {dr['w_icon']} {dr['weather']} ({w_str}) · {dr['t_label']} ({t_str}) = {dr['total']:+d} pts → Effective: <b>{dr['effective']}/100 {dr['eff_label']}</b></div>""",unsafe_allow_html=True)
            st.markdown(f"**Reasoning:** {case.get('reasoning','')}")
            c1,c2=st.columns(2)
            with c1:
                if case.get('risk_factors'): st.markdown(f"**Risk Factors:** {', '.join(case['risk_factors'])}")
                if case.get('required_skills'): st.markdown(f"**Skills:** {', '.join(case['required_skills'])}")
            with c2:
                if case.get('recommended_action'): st.markdown(f"**Action:** {case['recommended_action']}")
                st.markdown(f"**Search radius:** {dynamic_search_radius_km(case)} km")
            team_ids=case.get("team_ids",[])
            if team_ids:
                st.markdown(f"**Assigned Team {spec['icon']}:**")
                roles = case.get("team_roles", {})
                for tid in team_ids:
                    vol = next((v for v in st.session_state.volunteers if v["id"]==tid), None)
                    if vol:
                        st.markdown(f"- **{vol['name']}** · {vol['skill']} · {roles.get(tid, 'Team member')}")
            else:
                req=", ".join(spec["required"]) or "Any"
                pref=", ".join(spec["preferred"][:2])
                st.markdown(f"**Recommended Team {spec['icon']}:** {spec['note']} · Required: {req} · Preferred: {pref} · Size: {spec['size']}")

def render_dashboard_case_card(case):
    label, cls = get_priority(case["priority_score"])
    ts = time_since(case["created_at"])
    dr = compute_dynamic_risk(case)
    eff_cls = dr["eff_cls"] if dr["total"] != 0 else cls
    eff_label = dr["eff_label"] if dr["total"] != 0 else label
    eff_score = dr["effective"] if dr["total"] != 0 else case["priority_score"]
    desc = (case.get("description") or "")[:150]
    desc_suffix = "..." if len(case.get("description") or "") > 150 else ""
    photo_html = case_photo_html(case)
    assigned_name = "Active"
    if case.get("team_ids"):
        names = team_names_for_case(case)
        assigned_name = f"Team ({len(names)})" if names else "Team assigned"
    elif case.get("assigned_to"):
        vol = next((v for v in st.session_state.volunteers if v["id"] == case["assigned_to"]), None)
        assigned_name = vol["name"] if vol else "Assigned"
    risk_delta = f'<span style="color:var(--orange);font-family:var(--font-mono);font-size:.72rem;font-weight:800">{dr["total"]:+d}</span>' if dr["total"] else ""
    radius_km = dynamic_search_radius_km(case)
    st.markdown(f"""<div class="dash-case-card {eff_cls}">
      <div style="display:flex;gap:18px;align-items:flex-start">
        {photo_html}
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px">
            <div>
              <div class="dash-case-title">{case['name']}, {case['age']}</div>
              <div class="dash-case-meta">
                <span>📍 {case['location']}</span>
                <span>🕐 {ts}</span>
                <span>⭕ {radius_km} km radius</span>
                <span>🏷️ {case['category']}</span>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
              <span class="badge badge-{eff_cls}">{eff_label} {eff_score}</span>{risk_delta}
            </div>
          </div>
          <div class="dash-case-desc">{desc}{desc_suffix}</div>
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <span class="badge badge-gray">{assigned_name}</span>
            <span class="badge badge-gray">{case['id']}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="dash-action-row"></div>""", unsafe_allow_html=True)

    ca, cb, cc, cd, ce = st.columns([1, 1, 1, 1, 1.6])
    with ca:
        if is_case_active(case):
            st.button("✓ Found", key=f"dash_found_{case['id']}", on_click=close_case_found_action, args=(case["id"], "volunteer", None))
    with cb:
        if case.get("status") == "new":
            st.button("♙ Assign AI", key=f"dash_assign_{case['id']}", on_click=assign_ai_volunteer_action, args=(case["id"],))
    with cc:
        if case.get("status") == "new":
            st.button("👥 Smart Team", key=f"dash_team_{case['id']}", on_click=build_recommended_team_action, args=(case["id"],))
    with cd:
        u = st.session_state.get("current_user")
        my_vol = next((v for v in st.session_state.volunteers if u and v.get("username") == u.get("username")), None)
        can_join = (
            my_vol
            and case.get("status") == "assigned"
            and is_case_active(case)
            and my_vol["id"] not in case.get("team_ids", [])
            and my_vol.get("status") == "active"
            and my_vol.get("online_status") != "offline"
        )
        if can_join:
            st.button("+ Join Team", key=f"dash_join_{case['id']}_{my_vol['id']}", on_click=join_team_action, args=(case["id"], my_vol["id"]))
    with ce:
        if case.get("reasoning"):
            with st.expander(f"AI Analysis · {case['id']}"):
                st.markdown(f"**Reasoning:** {case.get('reasoning','')}")
                if case.get("risk_factors"):
                    st.markdown(f"**Risk Factors:** {', '.join(case['risk_factors'])}")
                if case.get("required_skills"):
                    st.markdown(f"**Skills:** {', '.join(case['required_skills'])}")
    if is_case_active(case):
        render_unfound_form(case)

                                                                                 
                 
                                                                                 
@ST_FRAGMENT(run_every=CASES_REFRESH_INTERVAL)
def page_dashboard_volunteer():
    refresh_shared_cases()
    sync_online_status()
    u=st.session_state.current_user
                                                                   
    my_vol=next((v for v in st.session_state.volunteers if v.get("username")==u["username"]),None)
    if my_vol and HAS_FASTAPI:
        streamlit.components.v1.html(browser_ping_js(my_vol["id"]),height=0)

    active_c=[c for c in st.session_state.cases if is_case_active(c)]
    critical_c=[c for c in active_c if compute_dynamic_risk(c)["effective"]>=85]
    free_v=[v for v in st.session_state.volunteers if v["status"]=="active"]
    online_v=[v for v in st.session_state.volunteers if v.get("online_status")=="online"]
    found_total=sum(1 for c in st.session_state.cases if c.get("status")=="found")

    st.markdown(f"""<div class="page-header">
      <div><div class="page-title">Operations Dashboard</div>
        <div class="page-sub">{live_time_html('datetime')}</div></div>
      <span class="role-tag volunteer">🔵 Volunteer</span></div>""",unsafe_allow_html=True)

    st.markdown(f"""<div class="stats-row">
      <div class="stat-card red"><div class="stat-label">Active Cases</div><div class="stat-num">{len(active_c)}</div><div class="stat-trend">Requiring attention</div></div>
      <div class="stat-card orange"><div class="stat-label">Critical</div><div class="stat-num">{len(critical_c)}</div><div class="stat-trend">High priority</div></div>
      <div class="stat-card green"><div class="stat-label">Online Now</div><div class="stat-num">{len(online_v)}</div><div class="stat-trend">Available volunteers</div></div>
      <div class="stat-card blue"><div class="stat-label">Found Total</div><div class="stat-num">{found_total}</div><div class="stat-trend">Successfully resolved</div></div>
    </div>""",unsafe_allow_html=True)

                                
    t_mod,t_label=get_time_risk()
    risk_snapshots=[compute_dynamic_risk(c) for c in active_c]
    high_risk_cases=[c for c,dr in zip(active_c, risk_snapshots) if dr["total"]>=15]
    weather_labels=[]
    for dr in risk_snapshots:
        label=f"{dr['w_icon']} {dr['weather']}"
        if label not in weather_labels:
            weather_labels.append(label)
    weather_summary=", ".join(weather_labels[:3]) + ("…" if len(weather_labels)>3 else "")
    if risk_snapshots and (any(dr["w_mod"] != 0 for dr in risk_snapshots) or t_mod>0):
        is_severe=t_mod>=20 or any(dr["weather"] in ["Storm","Extreme Heat"] for dr in risk_snapshots)
        st.markdown(f'<div class="dash-risk-card"><div class="dash-risk-title">⚠ Elevated Risk Conditions</div>Weather: {weather_summary or "—"} | {t_label} active · Priority scores may be adjusted · {len(high_risk_cases)} elevated case(s)</div>',unsafe_allow_html=True)

    team_case = max(active_c, key=lambda c: compute_dynamic_risk(c)["effective"], default=None)
    team_col1, team_col2, team_col3 = st.columns([1, 1, 3])
    with team_col1:
        st.button(
            "🧩 Team Builder",
            key="dash_open_teams",
            use_container_width=True,
            on_click=open_page_action,
            args=("teams",),
        )
    with team_col2:
        available_for_team = assignable_volunteers()
        if team_case:
            st.button(
                "👥 Create Team",
                key="dash_create_team",
                use_container_width=True,
                disabled=not bool(available_for_team),
                on_click=build_recommended_team_action,
                args=(team_case["id"],),
            )
        else:
            st.button("👥 Create Team", key="dash_create_team", use_container_width=True, disabled=True)
    with team_col3:
        if team_case:
            dr = compute_dynamic_risk(team_case)
            st.markdown(f'<div class="dash-actions-note">{len(available_for_team)} volunteers available for assignment · next target <b style="color:var(--text2)">{team_case["id"]}</b> · risk {dr["effective"]}/100</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="dash-actions-note">Create Team activates when there is at least one active case.</div>', unsafe_allow_html=True)

    cl,cr=st.columns([3,2])
    with cl:
        st.markdown('<div class="section-head">🚨 Highest Priority Cases</div>',unsafe_allow_html=True)
        sorted_c=sorted(active_c,key=lambda c:compute_dynamic_risk(c)["effective"],reverse=True)
        if not sorted_c: st.markdown('<div class="empty-state"><div class="empty-icon">✅</div><div class="empty-text">No active cases</div></div>',unsafe_allow_html=True)
        for case in sorted_c[:4]: render_dashboard_case_card(case)
    with cr:
        st.markdown('<div class="section-head">👥 Team Status</div>',unsafe_allow_html=True)
        for vol in st.session_state.volunteers:
            os_=vol.get("online_status","unknown")
            sc={"online":"var(--green)","offline":"var(--red-strong)","unknown":"var(--text3)"}.get(os_,"var(--text3)")
            sl={"active":"Available","busy":"On Mission","offline":"Offline"}.get(vol["status"],vol["status"])
            initials=avatar_initials(vol["name"])
            ai=next((x for x in st.session_state.cases if x["id"]==vol.get("assigned")),None)
            ainfo=f'<div style="font-size:.7rem;color:var(--text2)">→ {ai["id"]}: {ai["name"]}</div>' if ai else ""
            st.markdown(f"""<div class="dash-vol-card">
              <div class="vol-avatar {vol['status']}">{initials}</div>
              <div style="flex:1;min-width:0">
                <div style="font-family:var(--font-head);font-weight:800;font-size:.98rem;color:var(--text)">{vol['name']}</div>
                <div style="font-family:var(--font-mono);font-size:.72rem;color:var(--text3)">{vol['skill']}</div>{ainfo}</div>
              <div style="text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:4px">
                <div class="badge badge-gray" style="color:{sc};border-color:var(--border)">● {sl}</div>
                {online_badge_html(vol)}</div></div>""",unsafe_allow_html=True)


@ST_FRAGMENT(run_every=CASES_REFRESH_INTERVAL)
def page_my_missions():
    refresh_shared_cases()
    sync_online_status()
    u=st.session_state.current_user
    my_vol=next((v for v in st.session_state.volunteers if v.get("username")==u["username"]),None)
    if my_vol and HAS_FASTAPI:
        streamlit.components.v1.html(browser_ping_js(my_vol["id"]),height=0)
    st.markdown(f"""<div class="page-header"><div><div class="page-title">My <span>Missions</span></div><div class="page-sub">Assigned to you</div></div><span class="role-tag volunteer">🔵 {u['name']}</span></div>""",unsafe_allow_html=True)
    if not my_vol: st.info("No volunteer profile found."); return
    my_cases=[
        c for c in st.session_state.cases
        if c.get("assigned_to")==my_vol["id"] or my_vol["id"] in c.get("team_ids", [])
    ]
    active_m=[c for c in my_cases if is_case_active(c)]
    done_m=[c for c in my_cases if is_case_closed(c)]
    sc={"active":"var(--green)","busy":"var(--yellow)","offline":"var(--red-strong)"}.get(my_vol["status"],"var(--text3)")
    st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
      <div style="width:52px;height:52px;border-radius:12px;background:var(--blue-dim);display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🧑‍🚒</div>
      <div style="flex:1"><div style="font-family:var(--font-head);font-weight:700;font-size:1.1rem">{my_vol['name']}</div>
        <div style="font-size:.78rem;color:var(--text2)">{my_vol['skill']}</div></div>
      <div style="text-align:right">
        <div style="font-size:.9rem;font-weight:600;color:{sc}">● {my_vol['status'].title()}</div>
        {online_badge_html(my_vol)}
        <div style="font-size:.72rem;color:var(--text3);margin-top:4px">{len(active_m)} active team missions</div></div></div>""",unsafe_allow_html=True)
    if active_m:
        st.markdown('<div class="section-head">🔴 Active</div>',unsafe_allow_html=True)
        for c in active_m: render_case_card(c,show_actions=True,is_volunteer=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-icon">🎯</div><div class="empty-text">No active missions assigned</div></div>',unsafe_allow_html=True)
    if done_m:
        st.markdown('<div class="section-head">✅ Completed</div>',unsafe_allow_html=True)
        for c in done_m: render_case_card(c)


@ST_FRAGMENT(run_every=CASES_REFRESH_INTERVAL)
def page_all_cases():
    refresh_shared_cases()
    sync_online_status()
    st.markdown("""<div class="page-header"><div><div class="page-title">All <span>Cases</span></div><div class="page-sub">Complete operations log</div></div></div>""",unsafe_allow_html=True)
    active_c=[c for c in st.session_state.cases if is_case_active(c)]
    closed_c=[c for c in st.session_state.cases if is_case_closed(c)]
    f1,f2,_=st.columns([1,1,3])
    with f1: fs=st.selectbox("Status",["All Active","Critical only","High+","Unassigned"])
    with f2: fc=st.selectbox("Type",["All types"]+list(set(c["category"] for c in st.session_state.cases)))
    filtered=active_c
    if fs=="Critical only": filtered=[c for c in filtered if compute_dynamic_risk(c)["effective"]>=85]
    elif fs=="High+": filtered=[c for c in filtered if compute_dynamic_risk(c)["effective"]>=65]
    elif fs=="Unassigned": filtered=[c for c in filtered if not c.get("assigned_to")]
    if fc!="All types": filtered=[c for c in filtered if c["category"]==fc]
    filtered=sorted(filtered,key=lambda c:compute_dynamic_risk(c)["effective"],reverse=True)
    st.markdown(f'<div style="font-size:.78rem;color:var(--text3);margin-bottom:12px">{len(filtered)} shown</div>',unsafe_allow_html=True)
    for case in filtered: render_case_card(case,show_actions=True,is_volunteer=True)
    if closed_c:
        with st.expander(f"📁 Closed ({len(closed_c)})"):
            for c in closed_c:
                l,cl=get_priority(c["priority_score"])
                st.markdown(f'<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:.82rem;color:var(--text3)">✅ <b style="color:var(--text2)">{c["id"]}</b> — {c["name"]}, {c["age"]} yrs · {c["location"]}</div>',unsafe_allow_html=True)


@ST_FRAGMENT(run_every=CASES_REFRESH_INTERVAL)
def page_teams():
    refresh_shared_cases()
    sync_online_status()
    st.markdown("""<div class="page-header"><div><div class="page-title">Team <span>Builder</span></div><div class="page-sub">Build one operational crew at a time from risk, distance, and capability</div></div></div>""",unsafe_allow_html=True)

    active_cases=[c for c in st.session_state.cases if is_case_active(c)]
    available=assignable_volunteers()
    online_free=[v for v in available if v.get("online_status")=="online"]
    st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 20px;margin-bottom:20px;display:flex;gap:20px;flex-wrap:wrap;font-family:var(--font-mono);font-size:.78rem">
      <span style="color:var(--text2)">Active cases: <b>{len(active_cases)}</b></span>
      <span style="color:var(--green)">Online free: <b>{len(online_free)}</b></span>
      <span style="color:var(--text3)">Eligible free: <b>{len(available)}</b></span>
      <span style="color:var(--text3);margin-left:auto">Auto build + manual override</span>
    </div>""", unsafe_allow_html=True)

    if not active_cases:
        st.markdown('<div class="empty-state"><div class="empty-icon">🧩</div><div class="empty-text">No active cases. Create a report first, then Team Builder will show recommended crews.</div></div>', unsafe_allow_html=True)
        return

    sorted_cases=sorted(active_cases, key=lambda c: compute_dynamic_risk(c)["effective"], reverse=True)
    selected_id=st.selectbox(
        "Incident",
        [c["id"] for c in sorted_cases],
        format_func=lambda cid: next(
            f"{c['id']} · {c['name']} · {c['category']} · risk {compute_dynamic_risk(c)['effective']}/100"
            for c in sorted_cases if c["id"]==cid
        ),
        label_visibility="collapsed",
        key="team_case_picker"
    )
    case=next(c for c in sorted_cases if c["id"]==selected_id)
    dr=compute_dynamic_risk(case)
    spec=DISASTER_TEAMS.get(case.get("category","Other"),DISASTER_TEAMS["Other"])
    roles=team_requirements_for_case(case)
    current_ids=list(dict.fromkeys(case.get("team_ids", []) or ([case.get("assigned_to")] if case.get("assigned_to") else [])))
    current_roles=case.get("team_roles", {}) or {}
    proposed=build_team_for_case(case, available)

    st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 18px;margin:16px 0">
      <div style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">
        <div>
          <div style="font-family:var(--font-head);font-size:1.1rem;font-weight:800">{case['id']} · {case['name']}</div>
          <div style="font-size:.8rem;color:var(--text3);margin-top:4px">📍 {case['location']} · {case['category']} · missing {case.get('time_missing',0)}h</div>
        </div>
        <div style="display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap">
          <span class="badge badge-{dr['eff_cls']}">Risk {dr['effective']}/100 · {dr['eff_label']}</span>
          <span class="badge badge-gray">{spec['icon']} {spec['note']}</span>
          <span class="badge badge-gray">Weather/time {dr['total']:+d}</span>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-head">Required Roles</div>', unsafe_allow_html=True)
    role_cols=st.columns(min(4, max(1, len(roles))))
    for idx, role in enumerate(roles):
        with role_cols[idx % len(role_cols)]:
            priority_color={"required":"var(--red-strong)","ai":"var(--blue)","risk":"var(--orange)","preferred":"var(--yellow)","support":"var(--text3)"}.get(role.get("priority"),"var(--text3)")
            skills=", ".join(role.get("skills", []))
            st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px;min-height:94px">
              <div style="font-size:.72rem;color:{priority_color};text-transform:uppercase;letter-spacing:.7px;font-weight:800">{role.get('priority','role')}</div>
              <div style="font-weight:700;margin-top:5px">{role['label']}</div>
              <div style="font-size:.74rem;color:var(--text3);margin-top:4px">{skills}</div>
            </div>""", unsafe_allow_html=True)

    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="section-head">Current Team</div>', unsafe_allow_html=True)
        if current_ids:
            for tid in current_ids:
                vol=next((v for v in st.session_state.volunteers if v["id"]==tid),None)
                if vol:
                    dist=haversine(vol["lat"],vol["lon"],case["lat"],case["lon"])
                    st.markdown(f"""<div class="vol-card" style="margin-bottom:8px">
                      <div class="vol-avatar {vol['status']}">{avatar_initials(vol['name'])}</div>
                      <div style="flex:1;min-width:0">
                        <div style="font-weight:700">{vol['name']} <span style="color:var(--text3);font-size:.75rem">· {vol['id']}</span></div>
                        <div style="font-size:.75rem;color:var(--text3)">{vol['skill']} · {dist:.1f}km</div>
                        <div style="font-size:.72rem;color:var(--text2);margin-top:3px">{current_roles.get(tid,'Team member')}</div>
                      </div>
                      {online_badge_html(vol)}
                    </div>""", unsafe_allow_html=True)
        else:
            st.info("No assigned team yet.")
    with c2:
        st.markdown('<div class="section-head">Recommended Crew</div>', unsafe_allow_html=True)
        if proposed:
            for vol,role in proposed:
                dist=haversine(vol["lat"],vol["lon"],case["lat"],case["lon"])
                already=" · already assigned" if vol["id"] in current_ids else ""
                st.markdown(f"""<div class="vol-card" style="margin-bottom:8px">
                  <div class="vol-avatar {vol['status']}">{avatar_initials(vol['name'])}</div>
                  <div style="flex:1;min-width:0">
                    <div style="font-weight:700">{vol['name']} <span style="color:var(--text3);font-size:.75rem">· {vol['id']}</span></div>
                    <div style="font-size:.75rem;color:var(--text3)">{vol['skill']} · {dist:.1f}km{already}</div>
                    <div style="font-size:.72rem;color:var(--text2);margin-top:3px">{role}</div>
                  </div>
                  {online_badge_html(vol)}
                </div>""", unsafe_allow_html=True)
        else:
            st.warning("No eligible free volunteers. Release another team or wait for volunteers to come online.")

    b1,b2,b3,_=st.columns([1,1,1,2])
    with b1:
        st.button(
            "Build Recommended Team" if not current_ids else "Rebuild Recommended",
            key=f"teams_build_{case['id']}",
            disabled=not bool(proposed),
            use_container_width=True,
            on_click=build_recommended_team_action,
            args=(case["id"],),
        )
    with b2:
        st.button(
            "Release Team",
            key=f"teams_release_{case['id']}",
            disabled=not bool(current_ids),
            use_container_width=True,
            on_click=release_team_action,
            args=(case["id"],),
        )
    with b3:
        st.button(
            "Open Case",
            key=f"teams_open_{case['id']}",
            use_container_width=True,
            on_click=open_page_action,
            args=("all_cases",),
        )

    st.markdown('<div class="section-head" style="margin-top:22px">Manual Override</div>', unsafe_allow_html=True)
    manual_pool=[
        v for v in st.session_state.volunteers
        if v["id"] not in current_ids and v.get("online_status")!="offline"
        and (not v.get("assigned") or v.get("assigned")==case["id"])
    ]
    m1,m2=st.columns(2)
    with m1:
        if manual_pool:
            add_key = f"manual_add_{case['id']}"
            role_key = f"manual_role_{case['id']}"
            st.selectbox(
                "Add volunteer",
                [v["id"] for v in manual_pool],
                format_func=lambda vid: next(
                    f"{v['id']} · {v['name']} · {v['skill']} · {haversine(v['lat'],v['lon'],case['lat'],case['lon']):.1f}km"
                    for v in manual_pool if v["id"]==vid
                ),
                key=add_key
            )
            st.selectbox(
                "Role",
                [r["label"] for r in roles]+["Team support"],
                key=role_key
            )
            st.button(
                "Add To Team",
                key=f"manual_add_btn_{case['id']}",
                use_container_width=True,
                on_click=manual_add_to_team_action,
                args=(case["id"], add_key, role_key),
            )
        else:
            st.caption("No eligible volunteers for manual add.")
    with m2:
        if current_ids:
            remove_key = f"manual_remove_{case['id']}"
            st.selectbox(
                "Remove member",
                current_ids,
                format_func=lambda vid: next((f"{v['id']} · {v['name']}" for v in st.session_state.volunteers if v["id"]==vid), vid),
                key=remove_key
            )
            st.button(
                "Remove From Team",
                key=f"manual_remove_btn_{case['id']}",
                use_container_width=True,
                on_click=manual_remove_from_team_action,
                args=(case["id"], remove_key),
            )
        else:
            st.caption("No current members to remove.")

    assigned_cases=[c for c in active_cases if c.get("team_ids") or c.get("assigned_to")]
    if assigned_cases:
        st.markdown('<div class="section-head" style="margin-top:22px">Active Team Overview</div>', unsafe_allow_html=True)
        for ac in assigned_cases:
            names=", ".join(team_names_for_case(ac)) or "Assigned"
            adr=compute_dynamic_risk(ac)
            st.markdown(f'<div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:8px;font-size:.82rem"><b>{ac["id"]}</b> · {ac["name"]} · <span style="color:var(--text3)">{names}</span> <span class="badge badge-{adr["eff_cls"]}" style="float:right">risk {adr["effective"]}</span></div>', unsafe_allow_html=True)


@ST_FRAGMENT
def page_volunteers():
    sync_online_status()
    st.markdown("""<div class="page-header"><div><div class="page-title">Volunteer <span>Registry</span></div><div class="page-sub">Team management & live online status</div></div></div>""",unsafe_allow_html=True)

                          
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
                    st.success(f"✅ {vn} added ({nid})"); rerun_current_scope()

    st.markdown("---")
    for vol in st.session_state.volunteers:
        os_=vol.get("online_status","unknown")
        sc={"active":"var(--green)","busy":"var(--yellow)","offline":"var(--red-strong)"}.get(vol["status"],"var(--text3)")
        sl={"active":"Available","busy":"On Mission","offline":"Offline"}.get(vol["status"],vol["status"])
        lhb=vol.get("last_heartbeat"); src=vol.get("hb_source") or ""; did=vol.get("device_id") or ""
        lhb_str=lhb[:16].replace("T"," ") if lhb else "Never"
        nearby=sorted([(haversine(vol["lat"],vol["lon"],c["lat"],c["lon"]),c["id"]) for c in st.session_state.cases if is_case_active(c)])
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
                st.button(
                    "Activate",
                    key=f"act_{vol['id']}",
                    on_click=set_volunteer_status_action,
                    args=(vol["id"], "active"),
                )
        elif vol["status"]=="active":
            with ca:
                st.button(
                    "Set Offline",
                    key=f"off_{vol['id']}",
                    on_click=set_volunteer_status_action,
                    args=(vol["id"], "offline"),
                )


@ST_FRAGMENT
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
        if st.button("🗑️ Clear Log"): clear_ai_log(); rerun_current_scope()


                                                                                 
                                                         
                                                                                 
def page_tracking():
    sync_online_status()
    u=st.session_state.current_user
    my_vol=next((v for v in st.session_state.volunteers if v.get("username")==u["username"]),None)
    gps_fix = read_browser_gps_query(my_vol) if my_vol else None
    if my_vol and HAS_FASTAPI:
        streamlit.components.v1.html(browser_ping_js(my_vol["id"]),height=0)

    st.markdown("""<div class="page-header"><div><div class="page-title">Field <span>Tracking</span></div>
      <div class="page-sub">Submit check-ins · live volunteer positions · heartbeat log</div></div></div>""",unsafe_allow_html=True)

                                                                                
    if my_vol:
        st.markdown('<div class="section-head">📍 My Position</div>',unsafe_allow_html=True)
        st.markdown("""<div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px 16px;margin-bottom:10px">
          <div style="font-weight:800;color:var(--text);font-size:.86rem">Browser Location Access</div>
          <div style="font-size:.74rem;color:var(--text3);margin-top:4px">Click the request button below. The browser will show its native location permission dialog when the app is opened on HTTPS or localhost. If access was blocked earlier, reset Location permission from the address bar.</div>
        </div>""", unsafe_allow_html=True)
        browser_gps_permission_widget(my_vol["id"])

        latest_gps = db_get_vol_gps(my_vol["id"])
        if gps_fix and gps_fix.get("lat") is not None and gps_fix.get("lon") is not None:
            latest_gps = {
                **(latest_gps or {}),
                "lat": float(gps_fix["lat"]),
                "lon": float(gps_fix["lon"]),
                "address": gps_fix.get("address") or f"Browser GPS {float(gps_fix['lat']):.5f}, {float(gps_fix['lon']):.5f}",
                "updated_at": gps_fix.get("updated_at") or datetime.now().isoformat(),
            }
        hb_source = db_get_all_statuses().get(my_vol["id"], {}).get("hb_source")
        gps_address = (latest_gps or {}).get("address", "")
        gps_is_auto = bool(latest_gps and (gps_address.startswith("Browser GPS") or hb_source in ["browser", "agent"]))
        if latest_gps:
            my_vol["lat"] = latest_gps["lat"]
            my_vol["lon"] = latest_gps["lon"]
            my_vol["address"] = latest_gps.get("address") or my_vol.get("address", "")
        status_text = "No browser GPS fix yet. Click Request Location Access and allow Location in the browser prompt."
        if latest_gps and gps_is_auto:
            ts = (latest_gps.get("updated_at") or "")[:19].replace("T", " ")
            acc_text = f" · accuracy ±{int(gps_fix['accuracy'])}m" if gps_fix and gps_fix.get("accuracy") is not None else ""
            status_text = f"Last GPS: {latest_gps['lat']:.5f}, {latest_gps['lon']:.5f}{acc_text} · {ts}"
        elif latest_gps:
            status_text = "Stored manual or legacy position is ignored. Check-in requires browser GPS."
        st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px 16px;margin-bottom:10px">
          <div style="font-family:var(--font-mono);font-size:.8rem;color:var(--text2)">📍 {status_text}</div>
          <div style="font-size:.72rem;color:var(--text3);margin-top:6px">Manual location entry is disabled. Check-ins use browser geolocation only.</div>
        </div>""", unsafe_allow_html=True)
        render_my_position_map(my_vol, latest_gps, gps_is_auto, show_case_markers=False)

        st.markdown('<div class="section-head">📍 Submit Check-In</div>',unsafe_allow_html=True)

        with st.form("checkin_form"):
            ci1,ci2=st.columns(2)
            with ci1:
                ci_status=st.selectbox("Field Status",["🟢 All clear — on patrol","🔍 Actively searching",
                    "🚨 Need backup","⚠️ Lost contact with team","🏥 Medical situation",
                    "✅ Target located","🔋 Low battery / heading back"])
            with ci2:
                ci_case=st.selectbox("Related Case (optional)",["—"]+[f"{c['id']} — {c['name']}" for c in st.session_state.cases if is_case_active(c)])
                ci_note=st.text_area("Notes to HQ",placeholder="Anything to report...",height=90)
            sub=st.form_submit_button("📡 Send Check-In",use_container_width=True)

        if sub:
            now=datetime.now()
            latest_gps = db_get_vol_gps(my_vol["id"])
            hb_source = db_get_all_statuses().get(my_vol["id"], {}).get("hb_source")
            gps_address = (latest_gps or {}).get("address", "")
            gps_is_auto = bool(latest_gps and (gps_address.startswith("Browser GPS") or hb_source in ["browser", "agent"]))
            if not gps_is_auto:
                st.warning("Request location access first, allow Location in the browser prompt, and wait for a GPS fix.")
                st.stop()
            ci_lat=float(latest_gps["lat"])
            ci_lon=float(latest_gps["lon"])
            ci_place = latest_gps.get("address") or f"Browser GPS {ci_lat:.5f}, {ci_lon:.5f}"
            ci={"id":f"CI{len(st.session_state.checkins)+1:04d}","vol_id":my_vol["id"],"vol_name":my_vol["name"],
                "username":u["username"],"address":ci_place,"lat":ci_lat,"lon":ci_lon,"status":ci_status,
                "area":ci_place,"case":ci_case if ci_case!="—" else None,
                "note":ci_note or "","timestamp":now.isoformat()}
            add_checkin(ci)
            my_vol["address"]=ci_place; my_vol["lat"]=ci_lat; my_vol["lon"]=ci_lon; my_vol["last_checkin"]=now.isoformat()
                                                               
            db_save_vol_gps(my_vol["id"],ci_lat,ci_lon,ci_place)
            db_upsert_heartbeat(my_vol["id"],"checkin",HB_DEFAULT_INTERVAL,None,None,ci_lat,ci_lon,ci_status)
            if any(kw in ci_status for kw in ["backup","Lost contact","Medical"]):
                add_notification(f"[{now.strftime('%H:%M')}] 🚨 DISTRESS — {my_vol['name']}: {ci_status}")
            st.success(f"✅ Check-in {ci['id']} sent at {now.strftime('%H:%M:%S')}"); st.rerun()

                                                                                
    st.markdown('<div class="section-head" style="margin-top:24px">🗺️ Live Positions</div>',unsafe_allow_html=True)
    map_bg = "#000000" if IS_DARK else "#F6F1E8"
    map_card = "#000000" if IS_DARK else "#FFFCF5"
    map_border = "#262626" if IS_DARK else "#D5C9B8"
    map_text = "#F2F1EA" if IS_DARK else "#1F211D"
    map_text2 = "#CDD4C8" if IS_DARK else "#4C5048"
    map_text3 = "#8F9B8D" if IS_DARK else "#6D7168"
    map_green, map_red, map_orange, map_yellow = "#6EAD7A", "#D9825B", "#C9863A", "#D6B85A"
    tile_url = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" if IS_DARK else "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"

    vol_markers=""; case_markers=""
    for vol in st.session_state.volunteers:
        os_=vol.get("online_status","unknown")
        color={"online":map_green,"offline":map_red,"unknown":map_text3}.get(os_,map_text3)
        lhb=vol.get("last_heartbeat"); ts=lhb[:16].replace("T"," ") if lhb else "No ping yet"
        popup=f"{vol['name']} | {vol['skill']}<br>Address: {vol.get('address','Unknown area')}<br>Status: {vol.get('field_status',vol['status'])}<br>Online: {os_}<br>Last ping: {ts}"
        fn=vol['name'].split()[0]
        vol_markers+=f"""L.circleMarker([{vol['lat']},{vol['lon']}],{{radius:10,color:'{color}',fillColor:'{color}',fillOpacity:.85,weight:2}}).bindPopup('<b>{popup}</b>').addTo(map);
L.marker([{vol['lat']},{vol['lon']}],{{icon:L.divIcon({{html:'<div style="color:#fff;font-size:9px;font-weight:700;white-space:nowrap;margin-top:14px;text-shadow:0 1px 3px #000">{fn}</div>',className:'',iconAnchor:[20,0]}})}}).addTo(map);\n"""
    for c in st.session_state.cases:
        if is_case_active(c):
            l,cl=get_priority(c["priority_score"])
            col={"critical":map_red,"high":map_orange,"medium":map_yellow,"low":map_green}.get(cl,map_red)
            radius_km = dynamic_search_radius_km(c)
            case_markers+=f"""L.circle([{c['lat']},{c['lon']}],{{radius:{radius_km * 1000:.1f},color:'{col}',fillColor:'{col}',fillOpacity:.07,weight:1.5,dashArray:'6 6'}}).bindPopup('<b>{c["id"]}: {c["name"]}</b><br>Search radius: {radius_km} km').addTo(map);
L.circleMarker([{c['lat']},{c['lon']}],{{radius:8,color:'{col}',fillColor:'{col}',fillOpacity:.3,weight:2,dashArray:'4'}}).bindPopup('<b>{c["id"]}: {c["name"]}</b><br>{c["location"]}<br>Priority: {l}<br>Search radius: {radius_km} km').addTo(map);\n"""

    map_html=f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>body{{margin:0;padding:0;background:{map_bg};}}#map{{width:100%;height:460px;border-radius:12px;}}
.leaflet-container{{background:{map_card}!important;}}</style></head><body>
<div id="map"></div><script>
var map=L.map('map',{{center:[50.45,30.52],zoom:12,preferCanvas:true}});
L.tileLayer('{tile_url}',
  {{attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:19}}).addTo(map);
{vol_markers}{case_markers}
var leg=L.control({{position:'bottomright'}});
leg.onAdd=function(){{var d=L.DomUtil.create('div');
d.style.cssText='background:{map_card};border:1px solid {map_border};border-radius:8px;padding:10px 14px;font-family:monospace;font-size:11px;color:{map_text2};line-height:2';
d.innerHTML='<b style="color:{map_text}">LEGEND</b><br><span style="color:{map_green}">●</span> Online &nbsp;<span style="color:{map_red}">●</span> Offline &nbsp;<span style="color:{map_text3}">●</span> Unknown<br>◌ Active case';return d;}};
leg.addTo(map);</script></body></html>"""
    streamlit.components.v1.html(map_html,height=490)

                                                                                
    st.markdown('<div class="section-head" style="margin-top:24px">📋 Heartbeat Log (DB)</div>',unsafe_allow_html=True)

    hb_tab1, hb_tab2 = st.tabs(["Check-In History", "Raw Heartbeat DB"])

    with hb_tab1:
        all_ci=list(reversed(st.session_state.checkins))
        if not all_ci:
            st.markdown('<div class="empty-state"><div class="empty-icon">📡</div><div class="empty-text">No check-ins yet.</div></div>',unsafe_allow_html=True)
        else:
            fv=st.selectbox("Filter",["All"]+list({c["vol_name"] for c in all_ci}),key="ci_filter")
            shown=all_ci if fv=="All" else [c for c in all_ci if c["vol_name"]==fv]
            for ci in shown[:25]:
                ts=ci["timestamp"][:16].replace("T"," ")
                distress=any(kw in ci["status"] for kw in ["backup","Lost contact","Medical"])
                bc="var(--red-strong)" if distress else "var(--border)"
                ct=f'<span class="badge badge-blue" style="margin-left:6px">{ci["case"].split(" — ")[0]}</span>' if ci.get("case") else ""
                nt=f'<div style="font-size:.75rem;color:var(--text3);margin-top:4px;font-style:italic">"{ci["note"]}"</div>' if ci["note"] else ""
                st.markdown(f"""<div style="background:var(--card);border:1px solid {bc};border-radius:10px;padding:12px 16px;margin-bottom:8px">
                  <div style="display:flex;justify-content:space-between">
                    <div><b style="font-size:.9rem">{ci['vol_name']}</b><span style="color:var(--text3);font-family:var(--font-mono);font-size:.7rem;margin-left:8px">{ci['id']}</span>{ct}
                      <div style="font-size:.82rem;margin-top:4px">{ci['status']}</div>
                      <div style="font-size:.73rem;color:var(--text3);margin-top:2px">📍 {ci.get('address', ci['area'])}</div>
                      {nt}</div>
                    <div style="font-family:var(--font-mono);font-size:.72rem;color:var(--text3);flex-shrink:0;margin-left:12px">{ts}</div></div></div>""",unsafe_allow_html=True)

    with hb_tab2:
                          
        if my_vol:
            log=db_get_log(my_vol["id"],limit=20)
            if log:
                st.markdown(f'<div style="font-size:.78rem;color:var(--text3);margin-bottom:10px">Last {len(log)} heartbeats for {my_vol["name"]} from SQLite DB</div>',unsafe_allow_html=True)
                for entry in log:
                    src_icon={"agent":"📡","browser":"🌐","checkin":"📋"}.get(entry.get("source",""),"📡")
                    st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:6px;font-family:var(--font-mono);font-size:.75rem;color:var(--text2);display:flex;justify-content:space-between">
                      <span>{src_icon} {entry.get('source','?')} · {entry.get('field_status','—')[:35]}</span>
                      <span style="color:var(--text3)">{entry.get('received_at','')[:16].replace('T',' ')}</span></div>""",unsafe_allow_html=True)
            else:
                st.info("No DB entries yet — send a check-in or run agent.py")
        if HAS_FASTAPI:
            st.markdown(f"""<div style="background:var(--green-dim);border:1px solid rgba(34,216,122,.2);border-radius:8px;padding:12px 16px;margin-top:12px;font-family:var(--font-mono);font-size:.78rem;color:var(--green)">
              📡 API endpoints available:<br>
              GET  http://localhost:{FASTAPI_PORT}/status — all volunteer statuses<br>
              GET  http://localhost:{FASTAPI_PORT}/summary — online/offline counts<br>
              POST http://localhost:{FASTAPI_PORT}/heartbeat — receive ping<br>
              GET  http://localhost:{FASTAPI_PORT}/log/{{vol_id}} — heartbeat history</div>""",unsafe_allow_html=True)


                                                                                 
                
                                                                                 
@ST_FRAGMENT(run_every=CASES_REFRESH_INTERVAL)
def page_dashboard_reporter():
    refresh_shared_cases()
    u=st.session_state.current_user
    my=[ c for c in st.session_state.cases if c.get("reported_by_user")==u["username"]]
    active_m=[c for c in my if is_case_active(c)]
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
        st.markdown(f'<div style="font-size:.82rem;color:var(--text2);line-height:2.2;font-family:var(--font-mono)">🟢 {fv} volunteers free &nbsp;·&nbsp; 🟡 {bv} on mission &nbsp;·&nbsp; 📡 {ov} online &nbsp;·&nbsp; 🚨 {sum(1 for c in st.session_state.cases if is_case_active(c))} active cases</div>',unsafe_allow_html=True)


def page_report_case():
    u=st.session_state.current_user
    st.markdown("""<div class="page-header"><div><div class="page-title">Report <span>Missing Person</span></div>
      <div class="page-sub">AI analyzes and dispatches immediately</div></div></div>""",unsafe_allow_html=True)
    st.markdown('<div class="section-head">📍 Last Seen Location</div>', unsafe_allow_html=True)
    render_report_location_picker()
    selected_point = get_report_map_selection()
    if selected_point:
        st.success(f"Map point selected: {selected_point[0]:.6f}, {selected_point[1]:.6f}")
        if st.button("Clear selected map point", key="clear_report_map_point"):
            clear_report_map_selection()
            st.rerun()
    else:
        st.warning("Select the last known point on the map before submitting the report.")

    with st.form("new_case_form",clear_on_submit=True):
        st.markdown("#### Person Details")
        c1,c2=st.columns(2)
        with c1:
            name=st.text_input("Full Name *",placeholder="John Smith")
            age=st.number_input("Age *",min_value=0,max_value=120,value=25)
            category=st.selectbox("Emergency Type *",["Flood","Wildfire","Mountain / Forest","Urban Area","Missing Person","Other"])
            photo_file=st.file_uploader("Photo of Missing Person",type=["png","jpg","jpeg","webp"],help="Upload a clear photo if available.")
            if photo_file:
                st.image(photo_file,caption="Uploaded photo preview",width=180)
        with c2:
            time_missing=st.number_input("Hours Missing *",min_value=0.0,max_value=168.0,value=1.0,step=0.5)
            phone=st.text_input("Your Phone",placeholder="+1-555-...")
        description=st.text_area("Circumstances *",placeholder="Where last seen, clothing, features...",height=110)
        submitted=st.form_submit_button("🤖 Submit & Run AI Analysis",use_container_width=True)
    selected_for_submit = get_report_map_selection()
    if not selected_for_submit:
        lat_state = st.session_state.get("report_selected_lat")
        lon_state = st.session_state.get("report_selected_lon")
        try:
            lat_state = float(lat_state)
            lon_state = float(lon_state)
            if -90 <= lat_state <= 90 and -180 <= lon_state <= 180:
                selected_for_submit = (lat_state, lon_state)
                st.session_state.report_map_point = selected_for_submit
        except Exception:
            selected_for_submit = None
    if submitted and name and description and selected_for_submit:
        cid=f"C{st.session_state.next_case_id:03d}"; st.session_state.next_case_id+=1
        lat, lon = selected_for_submit
        location_source = "map"
        location_label = f"Map pin {lat:.5f}, {lon:.5f}"
        photo_data_url=uploaded_image_to_data_url(photo_file)
        new_case={"id":cid,"name":name,"age":age,"category":category,
            "photo_data_url":photo_data_url,
            "location":location_label,"lat":lat,"lon":lon,"description":description,
            "location_source":location_source,
            "reporter":u["name"],"phone":phone or "—","time_missing":time_missing,
            "priority_score":50,"status":"scoring","assigned_to":None,
            "reported_by_user":u["username"],"created_at":datetime.now().isoformat()}
        prog=st.progress(0,text="🌦️ Fetching weather at last seen point...")
        ensure_case_weather(new_case, force=True)
        prog.progress(20,text="🤖 Analyzing risk with live location weather...")
        ai_result=ai_score_case(new_case)
        prog.progress(60,text="👥 Building response team...")
        new_case.update({"priority_score":ai_result["priority_score"],"reasoning":ai_result["reasoning"],
            "required_skills":ai_result.get("required_skills",[]),"risk_factors":ai_result.get("risk_factors",[]),
            "recommended_action":ai_result.get("recommended_action",""),
            "search_radius_km":ai_result.get("estimated_search_radius_km",2),
            "search_radius_base_km":ai_result.get("estimated_search_radius_km",2),
            "risk_breakdown":ai_result.get("risk_breakdown",{}),"status":"new"})
        add_ai_log({"time":datetime.now().strftime("%H:%M:%S"),
            "event":f"📊 Case {cid} scored","detail":ai_result["reasoning"],"score":ai_result["priority_score"]})
        available=assignable_volunteers()
        if available:
            team=build_team_for_case(new_case,available)
            if team:
                assign_team_to_case(new_case, team)
                names=", ".join(f"{v['name']} ({role})" for v,role in team)
                add_notification(f"[{datetime.now().strftime('%H:%M')}] 👥 Team → {cid}: {', '.join(v['name'] for v,_ in team)}")
                add_ai_log({"time":datetime.now().strftime("%H:%M:%S"),
                    "event":f"👥 Smart team assigned {cid}","detail":names,"score":None})
        db_save_case(new_case)
        st.session_state.cases.append(new_case)
        db_clear_report_location(st.session_state.get("report_draft_id"))
        st.session_state.report_draft_id = secrets.token_urlsafe(12)
        st.session_state.pop("report_map_point", None)
        st.session_state.pop("report_selected_lat", None)
        st.session_state.pop("report_selected_lon", None)
        st.session_state.pop("report_lat", None)
        st.session_state.pop("report_lon", None)
        keep_params = {k: v for k, v in st.query_params.items() if k not in {"report_lat", "report_lon", "report_draft"}}
        st.query_params.clear()
        for k, v in keep_params.items():
            st.query_params[k] = v
        refresh_next_case_id()
        prog.progress(100,text="✅ Done!")
        label,cls=get_priority(new_case["priority_score"])
        av=next((v for v in st.session_state.volunteers if v["id"]==new_case.get("assigned_to")),None)
        assigned_label = "No volunteer"
        if new_case.get("team_ids"):
            assigned_label = "👥 " + ", ".join(team_names_for_case(new_case))
        elif av:
            assigned_label = "👤 " + av["name"]
        st.success(f"✅ Case **{cid}** submitted")
        st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin:16px 0">
          <div style="font-family:var(--font-head);font-weight:700;margin-bottom:12px">AI Result</div>
          <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px">
            <span class="badge badge-{cls}">{label} ({new_case['priority_score']}/100)</span>
            <span class="badge badge-blue">{assigned_label}</span>
            <span class="badge badge-gray">{weather_badge_text(new_case)}</span>
          </div>
          <div style="font-size:.82rem;color:var(--text2);line-height:1.6">{ai_result['reasoning']}</div></div>""",unsafe_allow_html=True)
    elif submitted:
        missing = []
        if not name:
            missing.append("name")
        if not description:
            missing.append("circumstances")
        if not selected_for_submit:
            missing.append("map point")
        st.warning("Missing required fields: " + ", ".join(missing))


@ST_FRAGMENT(run_every=CASES_REFRESH_INTERVAL)
def page_my_cases_reporter():
    refresh_shared_cases()
    u=st.session_state.current_user
    st.markdown("""<div class="page-header"><div><div class="page-title">My <span>Reports</span></div></div>
      <span class="role-tag reporter">🟢 Reporter</span></div>""",unsafe_allow_html=True)
    my=[c for c in st.session_state.cases if c.get("reported_by_user")==u["username"]]
    if not my:
        st.markdown('<div class="empty-state"><div class="empty-icon">📁</div><div class="empty-text">No reports yet.</div></div>',unsafe_allow_html=True); return
    active=sorted([c for c in my if is_case_active(c)],key=lambda c:c["priority_score"],reverse=True)
    done=[c for c in my if is_case_closed(c)]
    if active:
        st.markdown('<div class="section-head">🔴 Active</div>',unsafe_allow_html=True)
        for c in active:
            render_case_card(c, reporter_user=u)
    if done:
        st.markdown('<div class="section-head">✅ Resolved</div>',unsafe_allow_html=True)
        for c in done: render_case_card(c)

                                                                                 
        
                                                                                 
if not st.session_state.logged_in:
    show_login()
else:
    show_sidebar()
    u=st.session_state.current_user; role=u["role"]; page=st.session_state.active_page
    if role=="volunteer":
        inject_cases_refresh_js()
        if page=="dashboard":     page_dashboard_volunteer()
        elif page=="my_missions": page_my_missions()
        elif page=="all_cases":   page_all_cases()
        elif page=="teams":       page_teams()
        elif page=="volunteers":  page_volunteers()
        elif page=="tracking":    page_tracking()
        elif page=="ai_log":      page_ai_log()
        else: page_dashboard_volunteer()
    else:
        if page=="dashboard":     page_dashboard_reporter()
        elif page=="report_case": page_report_case()
        elif page=="my_cases":    page_my_cases_reporter()
        else: page_dashboard_reporter()
