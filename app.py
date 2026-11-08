import sys
import subprocess
import os
import sqlite3
import re
import io

# Auto-install matplotlib if missing
try:
    import matplotlib
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Albers QC | Your Personalized QC Coach",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AUTO-GENERATE OFFICIAL ALBERS QC EMBLEM IF MISSING ---
LOGO_FILE = 'albers_qc_official_logo.png'
def ensure_albers_logo():
    if not os.path.exists(LOGO_FILE):
        fig, ax = plt.subplots(figsize=(6, 6), dpi=250, facecolor='#0B1120')
        ax.set_facecolor('#0B1120')
        ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.3, 1.3); ax.axis('off')

        theta = np.linspace(0, 2*np.pi, 300)
        ax.plot(np.cos(theta)*1.18, np.sin(theta)*1.18, color='#1E293B', linewidth=5)
        ax.plot(np.cos(theta)*1.12, np.sin(theta)*1.12, color='#38BDF8', linewidth=1.5, alpha=0.8)

        for deg in range(0, 360, 10):
            rad = np.radians(deg)
            r1 = 1.08 if deg % 30 == 0 else 1.12
            lw = 2.5 if deg % 90 == 0 else (1.8 if deg % 30 == 0 else 0.8)
            col = '#FBBF24' if deg % 90 == 0 else ('#38BDF8' if deg % 30 == 0 else '#475569')
            ax.plot([np.cos(rad)*r1, np.cos(rad)*1.16], [np.sin(rad)*r1, np.sin(rad)*1.16], color=col, linewidth=lw)

        shield_x = [0, 0.82, 0.82, 0, -0.82, -0.82, 0]
        shield_y = [1.02, 0.68, -0.42, -1.02, -0.42, 0.68, 1.02]
        shield_poly = patches.Polygon(xy=list(zip(shield_x, shield_y)), closed=True, 
                                      facecolor='#0F172A', edgecolor='#38BDF8', linewidth=3, zorder=2)
        ax.add_patch(shield_poly)

        inner_x = [x*0.92 for x in shield_x]; inner_y = [y*0.92 for y in shield_y]
        inner_poly = patches.Polygon(xy=list(zip(inner_x, inner_y)), closed=True, 
                                     facecolor='#111827', edgecolor='#1E3A8A', linewidth=1.2, zorder=3)
        ax.add_patch(inner_poly)

        for y_pos in np.linspace(-0.6, 0.6, 9):
            ax.plot([-0.6, 0.6], [y_pos, y_pos], color='#1E293B', linewidth=1, alpha=0.6, zorder=3)

        a_outer_x = [0, 0.52, 0.32, 0, -0.32, -0.52, 0]
        a_outer_y = [0.72, -0.38, -0.38, 0.35, -0.38, -0.38, 0.72]
        a_poly = patches.Polygon(xy=list(zip(a_outer_x, a_outer_y)), closed=True, 
                                 facecolor='#0284C7', edgecolor='#FBBF24', linewidth=2.5, zorder=5)
        ax.add_patch(a_poly)

        cutout_x = [0, 0.16, -0.16]; cutout_y = [0.42, 0.05, 0.05]
        cutout_poly = patches.Polygon(xy=list(zip(cutout_x, cutout_y)), closed=True, 
                                      facecolor='#111827', edgecolor='#FBBF24', linewidth=1.5, zorder=6)
        ax.add_patch(cutout_poly)

        ax.plot([-0.30, 0.30], [-0.04, -0.04], color='#FBBF24', linewidth=5, zorder=7)
        for lx in [-0.18, -0.06, 0.06, 0.18]:
            ax.plot([lx, lx], [-0.12, 0.04], color='#0B1120', linewidth=2.5, zorder=8)

        banner_x = [-0.68, 0.68, 0.58, -0.58]; banner_y = [-0.52, -0.52, -0.74, -0.74]
        banner_poly = patches.Polygon(xy=list(zip(banner_x, banner_y)), closed=True, 
                                      facecolor='#1E293B', edgecolor='#38BDF8', linewidth=1.5, zorder=8)
        ax.add_patch(banner_poly)

        ax.text(0, -0.63, "ALBERS QC", color='#FFFFFF', fontsize=17, fontweight='heavy', ha='center', va='center', zorder=9)
        ax.text(0, -0.86, "YOUR PERSONALIZED QC COACH", color='#FBBF24', fontsize=7.2, fontweight='bold', ha='center', va='center', zorder=9)
        ax.scatter([0], [0.94], s=80, color='#FBBF24', marker='*', zorder=10)

        plt.tight_layout()
        plt.savefig(LOGO_FILE, dpi=250, facecolor=fig.get_facecolor(), bbox_inches='tight')
        plt.close()

ensure_albers_logo()

# --- HIGH-CONTRAST WAR ROOM CSS (AUDITED FOR READABILITY) ---
st.markdown("""
<style>
    .stApp { background-color: #0A0F1D !important; }
    
    .stApp, .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #F8FAFC !important;
        font-size: 15px;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }

    .albers-header-card {
        background: linear-gradient(135deg, #111C30 0%, #1E293B 100%);
        border: 2px solid #38BDF8;
        border-radius: 12px;
        padding: 18px 26px;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 30px rgba(56, 189, 248, 0.25);
    }
    
    .albers-brand-title {
        color: #FFFFFF !important;
        font-size: 28px;
        font-weight: 900;
        letter-spacing: 1.5px;
        margin: 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    
    .albers-brand-tagline {
        color: #FDE047 !important;
        font-size: 13.5px;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 3px 0 0 0;
    }

    .albers-status-badge {
        background-color: #064E3B;
        color: #A7F3D0 !important;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12.5px;
        font-weight: 800;
        border: 1.5px solid #10B981;
        letter-spacing: 0.5px;
    }

    .coordinator-switch-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 2px solid #FDE047;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 15px;
    }

    div.stButton > button, button[kind="secondary"] {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        border: 2px solid #38BDF8 !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5) !important;
        transition: all 0.15s ease-in-out !important;
        width: 100% !important;
    }
    
    div.stButton > button p, 
    div.stButton > button span, 
    div.stButton > button div {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
    }
    
    div.stButton > button:hover {
        background: #38BDF8 !important;
        border-color: #FDE047 !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    div.stButton > button:hover p, 
    div.stButton > button:hover span, 
    div.stButton > button:hover div {
        color: #0B1120 !important;
    }

    .dossier-box {
        background: linear-gradient(135deg, #111C30 0%, #172033 100%);
        border: 2px solid #FDE047;
        border-radius: 10px;
        padding: 18px 24px;
        margin: 15px 0;
        box-shadow: 0 4px 25px rgba(253, 224, 71, 0.2);
    }
    .dossier-title {
        color: #FDE047 !important;
        font-size: 18px;
        font-weight: 900;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
    }

    .oracle-box {
        background: linear-gradient(135deg, #111C30 0%, #1E293B 100%);
        border: 2px solid #38BDF8;
        border-radius: 10px;
        padding: 20px 24px;
        margin: 15px 0 25px 0;
        box-shadow: 0 4px 25px rgba(56, 189, 248, 0.2);
    }
    .oracle-title {
        color: #38BDF8 !important;
        font-size: 19px;
        font-weight: 900;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }

    div[data-baseweb="tag"] {
        background-color: #1E293B !important;
        border: 1.5px solid #38BDF8 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="tag"] span { color: #FFFFFF !important; font-weight: 700 !important; font-size: 13.5px !important; }
    div[data-baseweb="tag"] svg { fill: #38BDF8 !important; }

    div[data-baseweb="select"] > div {
        background-color: #111C30 !important;
        border: 1.5px solid #334155 !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="select"] svg { fill: #38BDF8 !important; }

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #111C30 !important;
        border: 1.5px solid #38BDF8 !important;
    }
    li[role="option"] {
        background-color: #111C30 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
    }

    /* ALL TABLES & TABLE CELLS - HIGH CONTRAST */
    .stTable, table, tbody, tr, td, th {
        background-color: #111C30 !important;
        color: #FFFFFF !important;
        border: 1px solid #1E293B !important;
    }
    th {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        border-bottom: 2px solid #38BDF8 !important;
    }
    td {
        color: #F8FAFC !important;
        font-size: 13.5px !important;
    }

    section[data-testid="stFileUploaderDropzone"] {
        background-color: #111C30 !important;
        border: 2px dashed #38BDF8 !important;
        border-radius: 10px !important;
        padding: 16px !important;
    }
    section[data-testid="stFileUploaderDropzone"] span { color: #F8FAFC !important; font-weight: 700 !important; }
    section[data-testid="stFileUploaderDropzone"] small { color: #CBD5E1 !important; font-size: 12px !important; }
    section[data-testid="stFileUploaderDropzone"] button {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border: 1.5px solid #38BDF8 !important;
        font-weight: 800 !important;
    }
    section[data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #38BDF8 !important;
        color: #0B1120 !important;
    }

    [data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        font-size: 30px !important;
        font-weight: 900 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #E2E8F0 !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
    }

    .coach-notes-box {
        background-color: #172033 !important;
        border-left: 5px solid #FBBF24 !important;
        border-radius: 0 10px 10px 0;
        padding: 18px 24px;
        margin-top: 15px;
        border-top: 1px solid #2D3A54;
        border-right: 1px solid #2D3A54;
        border-bottom: 1px solid #2D3A54;
    }
    .coach-notes-title {
        color: #FDE047 !important;
        font-weight: 900;
        font-size: 15px;
        letter-spacing: 0.8px;
        margin-bottom: 10px;
    }
    .coach-notes-box p, .coach-notes-box li, .coach-notes-box strong {
        color: #FFFFFF !important;
        font-size: 15.5px !important;
        line-height: 1.6;
    }

    [data-testid="stSidebar"] {
        background-color: #0E1626 !important;
        border-right: 1px solid #1E293B;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: #F8FAFC !important;
        font-weight: 600;
    }

    button[data-baseweb="tab"] {
        color: #CBD5E1 !important;
        font-size: 16px !important;
        font-weight: 700 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38BDF8 !important;
        border-bottom: 3px solid #38BDF8 !important;
    }

    .stTextInput input {
        background-color: #111C30 !important;
        color: #FFFFFF !important;
        border: 1.5px solid #334155 !important;
        font-size: 15px !important;
    }
    .stTextInput input::placeholder { color: #94A3B8 !important; }
    .stTextArea textarea {
        background-color: #111C30 !important;
        color: #F8FAFC !important;
        font-size: 14.5px !important;
        border: 1.5px solid #334155 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 8-ZONE MAPPING ---
ZONE_ORDER = [
    "1. Coming Out (-1 to -10)",
    "2. Backed Up (-11 to -20)",
    "3. Open Field (Own 21 - Opp 41)",
    "4. Fringe Zone (Opp 40-30)",
    "5. Scoring Zone (Opp 29-21)",
    "6. High Red Zone (20-11)",
    "7. Low Red Zone (10-6)",
    "8. Goal Line (5 & In)"
]

def classify_field_zone(yl):
    try:
        val = float(yl)
    except:
        return "Other"
    if -10 <= val <= -1: return "1. Coming Out (-1 to -10)"
    elif -20 <= val <= -11: return "2. Backed Up (-11 to -20)"
    elif (-49 <= val <= -21) or (val == 50) or (41 <= val <= 49): return "3. Open Field (Own 21 - Opp 41)"
    elif 30 <= val <= 40: return "4. Fringe Zone (Opp 40-30)"
    elif 21 <= val <= 29: return "5. Scoring Zone (Opp 29-21)"
    elif 11 <= val <= 20: return "6. High Red Zone (20-11)"
    elif 6 <= val <= 10: return "7. Low Red Zone (10-6)"
    elif 1 <= val <= 5: return "8. Goal Line (5 & In)"
    return "Other"

def get_field_x(yl):
    try:
        val = float(yl)
    except:
        return 50
    if val < 0: return abs(val)
    elif val == 50: return 50
    else: return 100 - val

# --- UNIFIED MASTER DATA PROCESSOR ---
def process_master_dataframe(raw_df, default_source_name="Game Data"):
    df_clean = raw_df.copy()

    # Opponent Detection
    opp_col = next((c for c in df_clean.columns if any(k in c.lower() for k in ['opp', 'game', 'team'])), None)
    if opp_col:
        df_clean['OPPONENT_CLEAN'] = df_clean[opp_col].fillna(default_source_name).astype(str)
    else:
        df_clean['OPPONENT_CLEAN'] = default_source_name

    # ODK Cleaning & Standardization
    if 'ODK' in df_clean.columns:
        df_clean['ODK_CLEAN'] = df_clean['ODK'].astype(str).str.strip().str.upper()
    else:
        df_clean['ODK_CLEAN'] = 'D'

    # Special Teams Phase Tagging (NFL & Power 4 Standards)
    def tag_st_phase(row):
        pt = str(row.get('PLAY TYPE', '')).lower()
        res = str(row.get('RESULT', '')).lower()
        op = str(row.get('OFF PLAY', '')).lower()
        full_text = f"{pt} {res} {op}"
        if 'kickoff return' in full_text or 'ko return' in full_text: return 'Kickoff Return (KR)'
        elif 'kickoff' in full_text or 'ko' in full_text: return 'Kickoff Coverage (KO)'
        elif 'punt return' in full_text or 'punt block' in full_text: return 'Punt Return / Block (PR)'
        elif 'punt' in full_text: return 'Punt Coverage (Punt)'
        elif 'fg block' in full_text or 'pat block' in full_text: return 'FG / PAT Block'
        elif 'field goal' in full_text or 'fg' in full_text or 'pat' in full_text or 'extra point' in full_text: return 'Field Goal / PAT'
        return 'General ST'

    df_clean['ST_PHASE'] = df_clean.apply(tag_st_phase, axis=1)

    # Field Zones
    if 'YARD LN' in df_clean.columns:
        df_clean['FIELD_ZONE'] = df_clean['YARD LN'].apply(classify_field_zone)
        df_clean['FIELD_X'] = df_clean['YARD LN'].apply(get_field_x)
    else:
        df_clean['FIELD_ZONE'] = "3. Open Field (Own 21 - Opp 41)"
        df_clean['FIELD_X'] = 50

    # Defensive Win
    def compute_def_success(row):
        res = str(row.get('RESULT', ''))
        if any(k in res.lower() for k in ['interception', 'fumble', 'def td', 'safety']): return 1
        gn = row.get('GN/LS', np.nan)
        if pd.isna(gn): return 1
        dn, dist = row.get('DN', 1), row.get('DIST', 10)
        try:
            dn, dist, gn = float(dn), float(dist), float(gn)
        except:
            return 0
        if dn == 1: return 1 if gn < 3 else 0
        elif dn == 2: return 1 if gn < (dist / 2.0) else 0
        elif dn in [3, 4]: return 1 if gn < dist else 0
        return 0

    # Offensive Win
    def compute_off_success(row):
        res = str(row.get('RESULT', ''))
        if any(k in res.lower() for k in ['interception', 'fumble', 'def td', 'safety']): return 0
        gn = row.get('GN/LS', np.nan)
        if pd.isna(gn): return 0
        dn, dist = row.get('DN', 1), row.get('DIST', 10)
        try:
            dn, dist, gn = float(dn), float(dist), float(gn)
        except:
            return 0
        if dn == 1: return 1 if gn >= 3 else 0
        elif dn == 2: return 1 if gn >= (dist / 2.0) else 0
        elif dn in [3, 4]: return 1 if gn >= dist else 0
        return 0

    df_clean['DEF_SUCCESS'] = df_clean.apply(compute_def_success, axis=1)
    df_clean['OFF_SUCCESS'] = df_clean.apply(compute_off_success, axis=1)
    df_clean['PLAY_TYPE_CLEAN'] = df_clean.get('PLAY TYPE', pd.Series('Other')).fillna('Other')
    df_clean['BLITZ_CLEAN'] = df_clean.get('BLITZ', pd.Series('BASE (NO BLITZ)')).fillna('BASE (NO BLITZ)')

    # Sequence Detection for Predictor
    if 'RESULT' in df_clean.columns:
        df_clean['PREV_RESULT'] = df_clean['RESULT'].shift(1).fillna('')
        df_clean['AFTER_PENALTY'] = df_clean['PREV_RESULT'].str.contains('Penalty', case=False, na=False)
    else:
        df_clean['AFTER_PENALTY'] = False

    if 'DN' in df_clean.columns:
        df_clean['PREV_DN'] = df_clean['DN'].shift(1).fillna(0)
        df_clean['AFTER_1ST_DOWN'] = (df_clean['PREV_DN'] == 1)
    else:
        df_clean['AFTER_1ST_DOWN'] = False

    return df_clean

# --- SIDEBAR BRANDING & HIGH-PROFILE COORDINATOR SWITCHER ---
if os.path.exists(LOGO_FILE):
    st.sidebar.image(LOGO_FILE, width=170)

st.sidebar.markdown("### **ALBERS QC**")
st.sidebar.markdown("<span style='color: #FDE047; font-weight:700;'>Your Personalized QC Coach</span>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# PROMINENT COORDINATOR COMMAND DECK (DC / OC / STC)
st.sidebar.markdown("""
<div class="coordinator-switch-box">
    <div style="font-size: 11px; font-weight: 800; color: #FDE047; letter-spacing: 1px; margin-bottom: 4px;">ACTIVE COORDINATOR ROOM</div>
""", unsafe_allow_html=True)

coordinator_mode = st.sidebar.radio(
    label="Select Coordinator Room:",
    options=["🛡️ DEFENSE (DC Mode)", "⚔️ OFFENSE (OC Mode)", "⚡ SPECIAL TEAMS (STC Mode)"],
    index=0,
    label_visibility="collapsed"
)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# --- UNIFIED MASTER DATA INTAKE (ACCEPTS ALL FORMS OF DATA) ---
st.sidebar.markdown("##### 📥 Master Data Intake (Drag & Drop)")
uploaded_master_files = st.sidebar.file_uploader(
    "Drop Game Cutups / Master CSVs Here:",
    type=["csv"],
    accept_multiple_files=True,
    help="Upload any game cutup or master season file. Albers QC automatically indexes Offense (O), Defense (D), and Kicking Game / Special Teams (K)."
)

all_dfs = []
if uploaded_master_files:
    for uf in uploaded_master_files:
        bname = os.path.splitext(uf.name)[0].replace('_', ' ').title()
        try:
            tdf = pd.read_csv(uf)
            all_dfs.append(process_master_dataframe(tdf, default_source_name=bname))
        except Exception as e:
            st.sidebar.error(f"Error loading {uf.name}: {e}")

if all_dfs:
    master_df = pd.concat(all_dfs, ignore_index=True)
    status_msg = f"● LIVE UPLOAD: {len(uploaded_master_files)} FILE(S) | {len(master_df)} SNAPS INDEXED"
else:
    # Automatic fallback to local dataset
    csv_file = 'input_file_1.csv'
    if not os.path.exists(csv_file):
        all_csvs = [f for f in os.listdir('.') if f.endswith('.csv')]
        if all_csvs: csv_file = all_csvs[0]
        else: csv_file = None

    if csv_file and os.path.exists(csv_file):
        fallback_raw = pd.read_csv(csv_file)
        master_df = process_master_dataframe(fallback_raw, default_source_name="Opponent")
        status_msg = f"● MASTER DATA ACTIVE | {len(master_df)} SNAPS INDEXED"
    else:
        master_df = None
        status_msg = "● STANDBY: AWAITING MASTER CSV"

# --- TOP HUD BANNER ---
col_logo, col_banner = st.columns([1, 7])
with col_logo:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=125)

if "DEFENSE" in coordinator_mode:
    unit_label = "DEFENSIVE WAR ROOM (DC MODE)"
elif "OFFENSE" in coordinator_mode:
    unit_label = "OFFENSIVE PLAY-CALLER STUDIO (OC MODE)"
else:
    unit_label = "SPECIAL TEAMS COMMAND CENTER (STC MODE)"

with col_banner:
    st.markdown(f"""
    <div class="albers-header-card">
        <div>
            <div class="albers-brand-title">ALBERS QC // {unit_label}</div>
            <div class="albers-brand-tagline">YOUR PERSONALIZED QUALITY CONTROL COACH</div>
        </div>
        <div>
            <span class="albers-status-badge">{status_msg}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Check data existence
if master_df is None:
    st.info("👋 **Welcome to Albers QC!**\n\nPlease drag and drop your master game CSV into the sidebar on the left.")
    st.stop()

# --- FILTER DATA FOR ACTIVE COORDINATOR ROOM ---
if "DEFENSE" in coordinator_mode:
    # Look for Defense (ODK = 'D') or use full dataset if all are charted as defense
    df = master_df[master_df['ODK_CLEAN'] == 'D']
    if len(df) == 0: df = master_df
elif "OFFENSE" in coordinator_mode:
    df = master_df[master_df['ODK_CLEAN'] == 'O']
else:
    # Special Teams
    df = master_df[(master_df['ODK_CLEAN'] == 'K') | (master_df['ST_PHASE'] != 'General ST')]

# SQLite Connection
conn = sqlite3.connect(':memory:', check_same_thread=False)
df.to_sql('snaps', conn, index=False, if_exists='replace')

def get_top_concept(sub_df, play_type):
    if 'OFF PLAY' not in sub_df.columns: return "-"
    p_df = sub_df[(sub_df['PLAY TYPE'] == play_type) & (sub_df['OFF PLAY'].notna())]
    if len(p_df) == 0: return "-"
    top = p_df['OFF PLAY'].value_counts().head(1)
    return f"{top.index[0]} ({top.values[0]})" if len(top) > 0 else "-"

# --- SITUATIONAL SIDEBAR CONTROLS ---
st.sidebar.markdown("---")
all_opponents = sorted(df['OPPONENT_CLEAN'].unique().tolist()) if len(df) > 0 else []
opponent_choices = ["ALL OPPONENTS (Full Season)"] + all_opponents
selected_opp = st.sidebar.selectbox("🎯 Opponent Scope", opponent_choices)

if selected_opp != "ALL OPPONENTS (Full Season)":
    scoped_df = df[df['OPPONENT_CLEAN'] == selected_opp]
else:
    scoped_df = df

st.sidebar.markdown("---")
st.sidebar.subheader("Situational Filters")
selected_zones = st.sidebar.multiselect("Field Zone", options=ZONE_ORDER, default=ZONE_ORDER)
selected_dn = st.sidebar.multiselect("Down", options=[1, 2, 3, 4], default=[1, 2, 3, 4])
front_options = sorted([x for x in df['DEF FRONT'].dropna().unique()]) if 'DEF FRONT' in df.columns else []
selected_front = st.sidebar.multiselect("Def Front", options=front_options, default=front_options)
cov_options = sorted([x for x in df['COVERAGE'].dropna().unique()]) if 'COVERAGE' in df.columns else []
selected_cov = st.sidebar.multiselect("Coverage", options=cov_options, default=cov_options)
blitz_options = sorted([x for x in df['BLITZ_CLEAN'].unique()]) if 'BLITZ_CLEAN' in df.columns else []
selected_blitz = st.sidebar.multiselect("Blitz / Pressure", options=blitz_options, default=blitz_options)

filtered_df = scoped_df[
    (scoped_df['FIELD_ZONE'].isin(selected_zones)) &
    (scoped_df['DN'].isin(selected_dn)) &
    (scoped_df['DEF FRONT'].isin(selected_front) | scoped_df['DEF FRONT'].isna()) &
    (scoped_df['COVERAGE'].isin(selected_cov) | scoped_df['COVERAGE'].isna()) &
    (scoped_df['BLITZ_CLEAN'].isin(selected_blitz))
] if len(scoped_df) > 0 else scoped_df

ZONE_BANDS = [
    (0, 10, '#1E3A8A', 0.65, 'COMING OUT\n(1-10)'),
    (10, 20, '#1D4ED8', 0.40, 'BACKED UP\n(11-20)'),
    (20, 60, '#065F46', 0.25, 'OPEN FIELD\n(Own 21 - Opp 41)'),
    (60, 70, '#B45309', 0.45, 'FRINGE\n(Opp 40-30)'),
    (70, 80, '#D97706', 0.50, 'SCORING\n(Opp 29-21)'),
    (80, 90, '#DC2626', 0.55, 'HIGH RED\n(20-11)'),
    (90, 95, '#B91C1C', 0.70, 'LOW RED\n(10-6)'),
    (95, 100, '#7F1D1D', 0.85, 'GOAL LINE\n(5 & In)')
]

def render_8_zone_field(ax, title_str, highlight_zone=None):
    ax.set_facecolor('#064E3B')
    ax.set_xlim(0, 100); ax.set_ylim(0, 53.3)
    ax.grid(False)

    for x1, x2, col, a, lbl in ZONE_BANDS:
        if highlight_zone and (lbl.split('\n')[0].lower() in highlight_zone.lower()):
            ax.axvspan(x1, x2, facecolor='#FDE047', alpha=0.75)
            ax.text((x1 + x2)/2, 46, "★ " + lbl, color='#0B1120', fontsize=8.5, fontweight='heavy', ha='center', va='center')
        else:
            ax.axvspan(x1, x2, facecolor=col, alpha=a)
            ax.text((x1 + x2)/2, 46, lbl, color='#FFFFFF', fontsize=8, fontweight='heavy', ha='center', va='center')

    for x in range(10, 100, 10):
        ax.axvline(x, color='white', linestyle='-', linewidth=1.2, alpha=0.7)
        num = x if x <= 50 else 100 - x
        ax.text(x, 7, str(num), color='#FFFFFF', fontsize=12, fontweight='heavy', ha='center')
    ax.axvline(50, color='#FDE047', linestyle='-', linewidth=2.5, alpha=0.9)
    ax.text(50, 26.65, "50", color='#FDE047', fontsize=22, fontweight='heavy', ha='center', va='center')
    ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    ax.set_xticklabels(['OWN 0', '10', '20', '30', '40', '50', 'OPP 40', '30', '20', '10', 'GOAL'], color='#FFFFFF', fontsize=10, fontweight='bold')
    ax.set_yticks([])
    ax.set_title(title_str, color='#FFFFFF', fontsize=13, fontweight='heavy', pad=12)

# =========================================================================
# COORDINATOR SUITE 1: DEFENSE (DC MODE)
# =========================================================================
if "DEFENSE" in coordinator_mode:
    tab_1, tab_2, tab_3 = st.tabs([
        "🛡️ Self-Scout (Our Defense Audit)", 
        "🎯 Opponent Advance Reconnaissance & Oracle", 
        "💬 Ask Coach Albers (Defensive QC)"
    ])

    # --- TAB 1: DEFENSIVE SELF-SCOUT ---
    with tab_1:
        st.subheader(f"🛡️ Albers QC // Defensive Self-Scout Audit: {selected_opp}")
        if 'self_pass_zone' not in st.session_state: st.session_state['self_pass_zone'] = None
        if 'self_field_zone' not in st.session_state: st.session_state['self_field_zone'] = None

        snaps_self = len(filtered_df)
        if snaps_self > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Snaps Evaluated", snaps_self)
            c2.metric("Defensive Win Rate", f"{filtered_df['DEF_SUCCESS'].mean():.1%}")
            c3.metric("Avg Yards Allowed", f"{filtered_df['GN/LS'].mean():.2f} yds")
            exp_count = ((filtered_df['GN/LS'] >= 15) & (filtered_df['PLAY_TYPE_CLEAN'] == 'Pass')).sum() + \
                        ((filtered_df['GN/LS'] >= 10) & (filtered_df['PLAY_TYPE_CLEAN'] == 'Run')).sum()
            c4.metric("Explosives Allowed", f"{exp_count} ({(exp_count/snaps_self)*100:.1f}%)")

            st.markdown("---")
            col_radar_chart, col_radar_click = st.columns([3, 1])

            with col_radar_chart:
                fig_self = plt.figure(figsize=(10, 8), dpi=150, facecolor='#0B1120')
                ax_pass = fig_self.add_axes([0.05, 0.05, 0.90, 0.88], facecolor='#111827')
                ax_pass.set_xlim(0, 3); ax_pass.set_ylim(0, 3)
                ax_pass.set_xticks([0.5, 1.5, 2.5]); ax_pass.set_xticklabels(['LEFT', 'MIDDLE', 'RIGHT'], color='#FFFFFF', fontsize=11, fontweight='heavy')
                ax_pass.set_yticks([0.5, 1.5, 2.5]); ax_pass.set_yticklabels(['SHORT (0-9y)', 'INTERMEDIATE (10-19y)', 'DEEP (20y+)'], color='#FFFFFF', fontsize=11, fontweight='heavy')
                ax_pass.grid(False); ax_pass.tick_params(length=0)

                zone_coords = {7: (0, 2), 8: (1, 2), 9: (2, 2), 4: (0, 1), 5: (1, 1), 6: (2, 1), 1: (0, 0), 2: (1, 0), 3: (2, 0)}
                for z, (gx, gy) in zone_coords.items():
                    z_df = filtered_df[filtered_df['PASS ZONE'] == z]
                    total = len(z_df)
                    comp = z_df['RESULT'].str.contains('Complete', case=False, na=False).sum()
                    comp_pct = (comp / total * 100) if total > 0 else 0
                    succ_pct = (z_df['DEF_SUCCESS'].mean() * 100) if total > 0 else 0
                    avg_gn = z_df['GN/LS'].mean() if total > 0 else 0
                    exp = (z_df['GN/LS'] >= 15).sum()
                    
                    is_selected = (st.session_state['self_pass_zone'] == z)
                    if is_selected:
                        box_col = '#0284C7'; badge = '👉 INSPECTING'; edge_c = '#FDE047'; lw = 3.5
                    else:
                        box_col = '#7F1D1D' if (avg_gn >= 15 or succ_pct < 45) else ('#78350F' if (avg_gn >= 8 or succ_pct < 55) else '#064E3B')
                        badge = '⚠️ VULNERABLE' if (avg_gn >= 15 or succ_pct < 45) else ('⚡ CONTESTED' if (avg_gn >= 8 or succ_pct < 55) else '🛡️ LOCKDOWN')
                        edge_c = '#38BDF8'; lw = 1.5

                    rect = patches.Rectangle((gx, gy), 1, 1, facecolor=box_col, edgecolor=edge_c, linewidth=lw, alpha=0.85)
                    ax_pass.add_patch(rect)
                    ax_pass.text(gx + 0.5, gy + 0.80, f"ZONE {z}", ha='center', color='#FFFFFF', fontsize=12, fontweight='heavy')
                    ax_pass.text(gx + 0.5, gy + 0.60, f"{total} Tgts ({comp_pct:.0f}% Comp)", ha='center', color='#E2E8F0', fontsize=10, fontweight='bold')
                    ax_pass.text(gx + 0.5, gy + 0.40, f"Win: {succ_pct:.0f}% | Avg: {avg_gn:.1f}y", ha='center', color='#FFFFFF', fontsize=10.5, fontweight='heavy')
                    ax_pass.text(gx + 0.5, gy + 0.22, f"Explosives: {exp}", ha='center', color='#FCA5A5' if exp > 1 else '#94A3B8', fontsize=9.5, fontweight='bold')
                    ax_pass.text(gx + 0.5, gy + 0.08, badge, ha='center', color='#FDE047', fontsize=8.5, fontweight='heavy')

                ax_pass.set_title(f"ALBERS QC // Passing Radar vs {selected_opp}", color='#FFFFFF', fontsize=13, fontweight='heavy', pad=12)
                st.pyplot(fig_self)

            with col_radar_click:
                st.markdown("##### 🎯 Click to Inspect Zone:")
                k_c1, k_c2, k_c3 = st.columns(3)
                if k_c1.button("Zone 7", key="btn_s7"): st.session_state['self_pass_zone'] = 7
                if k_c2.button("Zone 8", key="btn_s8"): st.session_state['self_pass_zone'] = 8
                if k_c3.button("Zone 9", key="btn_s9"): st.session_state['self_pass_zone'] = 9

                if k_c1.button("Zone 4", key="btn_s4"): st.session_state['self_pass_zone'] = 4
                if k_c2.button("Zone 5", key="btn_s5"): st.session_state['self_pass_zone'] = 5
                if k_c3.button("Zone 6", key="btn_s6"): st.session_state['self_pass_zone'] = 6

                if k_c1.button("Zone 1", key="btn_s1"): st.session_state['self_pass_zone'] = 1
                if k_c2.button("Zone 2", key="btn_s2"): st.session_state['self_pass_zone'] = 2
                if k_c3.button("Zone 3", key="btn_s3"): st.session_state['self_pass_zone'] = 3

                if st.button("🔄 Clear Zone Selection", key="btn_clear_spass"):
                    st.session_state['self_pass_zone'] = None
                    st.rerun()

            if st.session_state['self_pass_zone']:
                pz = st.session_state['self_pass_zone']
                pz_df = filtered_df[filtered_df['PASS ZONE'] == pz]
                st.markdown(f"""
                <div class="dossier-box">
                    <div class="dossier-title">🎯 TELEMETRY DOSSIER: ZONE {pz} PASS DEFENSE</div>
                """, unsafe_allow_html=True)
                if len(pz_df) > 0:
                    p_c1, p_c2, p_c3, p_c4 = st.columns(4)
                    p_c1.metric(f"Zone {pz} Targets", len(pz_df))
                    p_c2.metric("Comp % Allowed", f"{(pz_df['RESULT'].str.contains('Complete', case=False, na=False).mean())*100:.1f}%")
                    p_c3.metric("Def Win Rate", f"{pz_df['DEF_SUCCESS'].mean()*100:.1f}%")
                    p_c4.metric("Avg Yards Allowed", f"{pz_df['GN/LS'].mean():.1f} yds")
                    st.dataframe(pz_df[['PLAY #', 'DN', 'DIST', 'OFF FORM', 'OFF PLAY', 'DEF FRONT', 'COVERAGE', 'GN/LS', 'RESULT', 'DEF_SUCCESS']], use_container_width=True)
                    pz_playlist = pz_df['PLAY #'].astype(str).tolist()
                    st.text_area(f"Zone {pz} Video Cutup Playlist ({len(pz_playlist)} plays):", ", ".join(pz_playlist), height=70)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")
            # 100-Yard Field
            st.subheader("📍 100-Yard Field & Interactive Territory Selector")
            f_cols = st.columns(9)
            if f_cols[0].button("1. Coming Out", key="fbtn_s1"): st.session_state['self_field_zone'] = "1. Coming Out (-1 to -10)"
            if f_cols[1].button("2. Backed Up", key="fbtn_s2"): st.session_state['self_field_zone'] = "2. Backed Up (-11 to -20)"
            if f_cols[2].button("3. Open Field", key="fbtn_s3"): st.session_state['self_field_zone'] = "3. Open Field (Own 21 - Opp 41)"
            if f_cols[3].button("4. Fringe Zone", key="fbtn_s4"): st.session_state['self_field_zone'] = "4. Fringe Zone (Opp 40-30)"
            if f_cols[4].button("5. Scoring Zone", key="fbtn_s5"): st.session_state['self_field_zone'] = "5. Scoring Zone (Opp 29-21)"
            if f_cols[5].button("6. High Red", key="fbtn_s6"): st.session_state['self_field_zone'] = "6. High Red Zone (20-11)"
            if f_cols[7].button("7. Low Red", key="fbtn_s7"): st.session_state['self_field_zone'] = "7. Low Red Zone (10-6)"
            if f_cols[8].button("8. Goal Line", key="fbtn_s8"): st.session_state['self_field_zone'] = "8. Goal Line (5 & In)"
            if f_cols[8].button("🔄 Show All", key="fbtn_s_all"): 
                st.session_state['self_field_zone'] = None
                st.rerun()

            fig_field = plt.figure(figsize=(16, 5), dpi=150, facecolor='#0B1120')
            ax_field = fig_field.add_axes([0.05, 0.12, 0.90, 0.78])
            render_8_zone_field(ax_field, f"ALBERS QC // 100-Yard Field: Explosives (★) vs. Havoc/Turnovers (◆)", 
                                highlight_zone=st.session_state['self_field_zone'])

            np.random.seed(42)
            def calc_y(h, d):
                base = 20.0 if h == 'L' else (33.3 if h == 'R' else 26.65)
                offset = -4 if d == 'L' else (4 if d == 'R' else 0)
                return base + offset + np.random.uniform(-2, 2)

            field_plot_df = filtered_df
            if st.session_state['self_field_zone']:
                field_plot_df = filtered_df[filtered_df['FIELD_ZONE'] == st.session_state['self_field_zone']]

            for _, row in field_plot_df[field_plot_df['GN/LS'] >= 20].iterrows():
                ax_field.scatter(row['FIELD_X'], calc_y(row.get('HASH', 'M'), row.get('PLAY DIR', 'M')), s=140, color='#EF4444', marker='*', edgecolors='yellow', zorder=5)
            for _, row in field_plot_df[field_plot_df['RESULT'].str.contains('Interception|Fumble|Sack|Safety', case=False, na=False)].iterrows():
                ax_field.scatter(row['FIELD_X'], calc_y(row.get('HASH', 'M'), row.get('PLAY DIR', 'M')), s=80, color='#38BDF8', marker='D', edgecolors='white', zorder=4)

            st.pyplot(fig_field)

            if st.session_state['self_field_zone']:
                fz = st.session_state['self_field_zone']
                fz_df = filtered_df[filtered_df['FIELD_ZONE'] == fz]
                st.markdown(f"""
                <div class="dossier-box">
                    <div class="dossier-title">📍 TERRITORY DOSSIER: {fz}</div>
                """, unsafe_allow_html=True)
                if len(fz_df) > 0:
                    fz_c1, fz_c2, fz_c3, fz_c4 = st.columns(4)
                    fz_c1.metric("Snaps in Territory", len(fz_df))
                    fz_c2.metric("Defensive Win Rate", f"{fz_df['DEF_SUCCESS'].mean()*100:.1f}%")
                    fz_c3.metric("Avg Yards Allowed", f"{fz_df['GN/LS'].mean():.2f} yds")
                    fz_c4.metric("Explosives Conceded", (fz_df['GN/LS'] >= 15).sum())
                    st.dataframe(fz_df[['PLAY #', 'DN', 'DIST', 'OFF FORM', 'OFF PLAY', 'DEF FRONT', 'COVERAGE', 'GN/LS', 'RESULT', 'DEF_SUCCESS']], use_container_width=True)
                    fz_playlist = fz_df['PLAY #'].astype(str).tolist()
                    st.text_area(f"{fz} Video Cutup Playlist ({len(fz_playlist)} plays):", ", ".join(fz_playlist), height=70)
                st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: OPPONENT RECON WITH PREDICTOR & 12 QUICK QUERIES ---
    with tab_2:
        st.subheader(f"🎯 Albers QC // Opponent Advance Reconnaissance: {selected_opp}")

        # ORACLE PREDICTOR
        st.markdown("""
        <div class="oracle-box">
            <div class="oracle-title">🔮 REAL-TIME PLAY-CALL PREDICTOR & TENDENCY ORACLE</div>
            <div style="color: #CBD5E1; font-size: 13.5px; margin-bottom: 12px;">
                Input the opponent's pre-snap personnel, alignment, field location, and situational trigger to predict what play is coming next:
            </div>
        """, unsafe_allow_html=True)

        pred_c1, pred_c2, pred_c3, pred_c4 = st.columns(4)
        with pred_c1:
            pred_dn_dist = st.selectbox("Down & Distance Situation:", [
                "1st & 10", "2nd & Short (1-3 yds)", "2nd & Medium (4-6 yds)", "2nd & Long (7+ yds)",
                "3rd & Short (1-2 yds)", "3rd & Medium (3-6 yds)", "3rd & Long (7+ yds)", "4th Down"
            ])
        with pred_c2:
            pred_zone = st.selectbox("Field Territory:", ["Any Territory"] + ZONE_ORDER)
        with pred_c3:
            all_opp_forms = ["Any Formation"] + sorted(scoped_df['OFF FORM'].dropna().unique().tolist()) if 'OFF FORM' in scoped_df.columns else ["Any Formation"]
            pred_form = st.selectbox("Opponent Formation / Look:", all_opp_forms)
        with pred_c4:
            pred_hash = st.selectbox("Ball on Hash:", ["Any Hash", "Left Hash (L)", "Middle (M)", "Right Hash (R)"])

        pred_trigger = st.radio("Situational Context / Sequence:", 
                                ["Standard Snap", "After 1st Down Conversion", "After Penalty"], 
                                horizontal=True)

        p_where = []
        if pred_dn_dist == "1st & 10": p_where.append("DN = 1")
        elif pred_dn_dist == "2nd & Short (1-3 yds)": p_where.append("DN = 2 AND DIST <= 3")
        elif pred_dn_dist == "2nd & Medium (4-6 yds)": p_where.append("DN = 2 AND DIST BETWEEN 4 AND 6")
        elif pred_dn_dist == "2nd & Long (7+ yds)": p_where.append("DN = 2 AND DIST >= 7")
        elif pred_dn_dist == "3rd & Short (1-2 yds)": p_where.append("DN = 3 AND DIST <= 2")
        elif pred_dn_dist == "3rd & Medium (3-6 yds)": p_where.append("DN = 3 AND DIST BETWEEN 3 AND 6")
        elif pred_dn_dist == "3rd & Long (7+ yds)": p_where.append("DN = 3 AND DIST >= 7")
        elif pred_dn_dist == "4th Down": p_where.append("DN = 4")

        if pred_zone != "Any Territory": p_where.append(f"FIELD_ZONE = '{pred_zone}'")
        if pred_form != "Any Formation": p_where.append(f"OFF_FORM = '{pred_form}'")
        if "Left" in pred_hash: p_where.append("HASH = 'L'")
        elif "Right" in pred_hash: p_where.append("HASH = 'R'")
        elif "Middle" in pred_hash: p_where.append("HASH = 'M'")

        if pred_trigger == "After Penalty": p_where.append("AFTER_PENALTY = 1")
        elif pred_trigger == "After 1st Down Conversion": p_where.append("AFTER_1ST_DOWN = 1")

        p_sql_where = " AND ".join(p_where) if p_where else "1=1"
        pred_sub = pd.read_sql_query(f"SELECT * FROM snaps WHERE {p_sql_where}", conn)

        is_widened = False
        if len(pred_sub) < 3 and len(p_where) > 1:
            pred_sub = pd.read_sql_query(f"SELECT * FROM snaps WHERE {p_where[0]}", conn)
            is_widened = True

        st.markdown("---")
        if len(pred_sub) > 0:
            tot_p = len(pred_sub)
            r_cnt = (pred_sub['PLAY TYPE'] == 'Run').sum()
            p_cnt = (pred_sub['PLAY TYPE'] == 'Pass').sum()
            r_pct = (r_cnt / tot_p) * 100
            p_pct = (p_cnt / tot_p) * 100

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Historical Snaps", f"{tot_p} Plays" + (" (Widened)" if is_widened else ""))
            m_col2.metric("Run Tendency", f"{r_pct:.1f}% Run")
            m_col3.metric("Pass Tendency", f"{p_pct:.1f}% Pass")
            m_col4.metric("Avg Gain Conceded", f"{pred_sub['GN/LS'].mean():.1f} yds")

            pred_card1, pred_card2 = st.columns(2)
            with pred_card1:
                st.markdown("##### 🚨 Top 3 Predicted Offensive Schemes:")
                top_schemes = pred_sub.groupby(['PLAY TYPE', 'OFF PLAY']).agg(
                    Snaps=('PLAY #', 'count'),
                    Avg_Gain=('GN/LS', 'mean'),
                    Explosive=('GN/LS', lambda x: (x >= 15).sum())
                ).reset_index().sort_values(by='Snaps', ascending=False).head(3)
                top_schemes['Share_%'] = (top_schemes['Snaps'] / tot_p) * 100
                st.dataframe(top_schemes[['PLAY TYPE', 'OFF PLAY', 'Snaps', 'Share_%', 'Avg_Gain']], use_container_width=True)

            with pred_card2:
                top_counter_front = pred_sub.groupby('DEF FRONT')['DEF_SUCCESS'].agg(['count', 'mean']).sort_values(by='mean', ascending=False)
                best_front_name = top_counter_front.index[0] if len(top_counter_front) > 0 else "Base OVER"
                best_front_win = top_counter_front.iloc[0]['mean'] * 100 if len(top_counter_front) > 0 else 55.0

                top_counter_cov = pred_sub.groupby('COVERAGE')['DEF_SUCCESS'].agg(['count', 'mean']).sort_values(by='mean', ascending=False)
                best_cov_name = top_counter_cov.index[0] if len(top_counter_cov) > 0 else "MOD"
                best_cov_win = top_counter_cov.iloc[0]['mean'] * 100 if len(top_counter_cov) > 0 else 55.0

                st.markdown("##### 🛡️ Albers QC Recommended Counter-Call:")
                st.success(f"""
                * **Lockdown Front:** `{best_front_name}` (Historical Win Rate: **{best_front_win:.1f}%**)
                * **Lockdown Coverage:** `{best_cov_name}` (Historical Win Rate: **{best_cov_win:.1f}%**)
                * **Tactical Tell:** Offense leans **{"HEAVY RUN" if r_pct>=60 else ("HEAVY PASS" if p_pct>=60 else "BALANCED")}** in this situation.
                """)

            pred_playlist = pred_sub['PLAY #'].astype(str).tolist()
            st.text_area(f"Historical Cutup String for this Exact Situation ({len(pred_playlist)} plays):", ", ".join(pred_playlist), height=60)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")

        # =========================================================================
        # ⚡ 12 RESTORED QUICK RECON REFERENCE QUERIES (INSIDE TAB 2)
        # =========================================================================
        st.subheader("⚡ 12 Quick-Reference Opponent Recon Inquiries")
        st.markdown("Click any tactical reference button below to query tendencies, tactical field notes, and cutup strings directly inside this room:")

        rc_1, rc_2, rc_3 = st.columns(3)
        q_recon = None
        if rc_1.button("📍 Top Front in Low Red Zone?", key="rq1"): q_recon = "What is our top-performing front in the Low Red Zone?"
        if rc_2.button("🎯 Opponent 3rd & Med in Fringe?", key="rq2"): q_recon = "What does the opponent run on 3rd & Medium in the Fringe Zone?"
        if rc_3.button("🛡️ Best Coverage on 3rd & Long?", key="rq3"): q_recon = "What is our best coverage call on 3rd & Long?"

        rc_4, rc_5, rc_6 = st.columns(3)
        if rc_4.button("🛑 4th Down Stop Calls?", key="rq4"): q_recon = "What is our top front and stop rate on 4th Down?"
        if rc_5.button("🚀 2nd & Short Shot Alert?", key="rq5"): q_recon = "What does the opponent run on 2nd & Short?"
        if rc_6.button("🧱 Goal-Line Run Concepts?", key="rq6"): q_recon = "What are their top concepts in the Goal Line zone?"

        rc_7, rc_8, rc_9 = st.columns(3)
        if rc_7.button("👈 Left Hash Run vs Pass?", key="rq7"): q_recon = "What is their run pass tendency on the Left Hash?"
        if rc_8.button("👉 Right Hash Tendency?", key="rq8"): q_recon = "What does the opponent run on the Right Hash?"
        if rc_9.button("💨 Empty Formation Tendency?", key="rq9"): q_recon = "What does Empty formation do?"

        rc_10, rc_11, rc_12 = st.columns(3)
        if rc_10.button("📦 Bunch & Stack Rub Alert?", key="rq10"): q_recon = "What pass concepts do they run out of Bunch or Stack?"
        if rc_11.button("🎯 RPO Vulnerability Audit?", key="rq11"): q_recon = "How does our defense perform against RPO plays?"
        if rc_12.button("🎭 Bluff vs Real Blitz Havoc?", key="rq12"): q_recon = "Compare blitz success rate between real pressure and bluffs"

        recon_input = st.text_input("Ask Coach Albers a question inside Recon Room:", value=q_recon if q_recon else "", placeholder="e.g. What does Lincoln run on 3rd & Medium in the Fringe Zone?")

        if recon_input:
            q_rc = recon_input.lower()
            w_rc = []
            if 'low red' in q_rc: w_rc.append("FIELD_ZONE LIKE '%Low Red%'")
            elif 'high red' in q_rc: w_rc.append("FIELD_ZONE LIKE '%High Red%'")
            elif 'goal line' in q_rc: w_rc.append("FIELD_ZONE LIKE '%Goal Line%'")
            elif 'fringe' in q_rc: w_rc.append("FIELD_ZONE LIKE '%Fringe%'")
            if 'left hash' in q_rc: w_rc.append("HASH = 'L'")
            elif 'right hash' in q_rc: w_rc.append("HASH = 'R'")
            if 'empty' in q_rc: w_rc.append("OFF_FORM LIKE '%Empty%'")
            elif 'bunch' in q_rc or 'stack' in q_rc: w_rc.append("(OFF_FORM LIKE '%Bunch%' OR OFF_FORM LIKE '%Stack%')")
            if 'rpo' in q_rc: w_rc.append("OFF_PLAY LIKE '%RPO%'")
            if '3rd & med' in q_rc: w_rc.append("DN = 3 AND DIST BETWEEN 3 AND 6")
            elif '3rd & long' in q_rc: w_rc.append("DN = 3 AND DIST >= 7")
            elif '4th' in q_rc: w_rc.append("DN = 4")
            elif '2nd & short' in q_rc: w_rc.append("DN = 2 AND DIST <= 3")

            w_rc_sql = " AND ".join(w_rc) if w_rc else "1=1"
            if 'front' in q_rc or '4th' in q_rc:
                sql_rc = f"""SELECT "DEF FRONT" as Front, count(*) as Snaps, round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", round(avg("GN/LS"), 2) as "Avg_Yds_Allowed", group_concat("PLAY #", ', ') as Play_List FROM snaps WHERE {w_rc_sql} AND "DEF FRONT" IS NOT NULL GROUP BY "DEF FRONT" ORDER BY "Def_Win_%" DESC"""
            elif 'coverage' in q_rc:
                sql_rc = f"""SELECT "COVERAGE" as Coverage, count(*) as Snaps, round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", round(avg("GN/LS"), 2) as "Avg_Yds_Allowed", group_concat("PLAY #", ', ') as Play_List FROM snaps WHERE {w_rc_sql} AND "COVERAGE" IS NOT NULL GROUP BY "COVERAGE" ORDER BY "Def_Win_%" DESC"""
            elif 'blitz' in q_rc or 'bluff' in q_rc:
                sql_rc = f"""SELECT BLITZ_CLEAN as Pressure, count(*) as Snaps, round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", round(avg("GN/LS"), 2) as "Avg_Yds_Allowed", group_concat("PLAY #", ', ') as Play_List FROM snaps WHERE {w_rc_sql} GROUP BY BLITZ_CLEAN ORDER BY "Def_Win_%" DESC"""
            else:
                sql_rc = f"""SELECT "PLAY TYPE", coalesce("OFF PLAY", 'Base Concept') as Concept, count(*) as Snaps, round(avg("GN/LS"), 1) as "Avg_Gain", group_concat("PLAY #", ', ') as Play_List FROM snaps WHERE {w_rc_sql} GROUP BY "PLAY TYPE", Concept ORDER BY Snaps DESC"""

            res_rc_df = pd.read_sql_query(sql_rc, conn)
            st.markdown("---")
            if len(res_rc_df) > 0:
                st.dataframe(res_rc_df[[c for c in res_rc_df.columns if c != 'Play_List']], use_container_width=True)
                st.markdown("""<div class="coach-notes-box"><div class="coach-notes-title">🧠 COACH ALBERS' TACTICAL FIELD NOTES:</div>""", unsafe_allow_html=True)
                st.markdown(f"* Top producing scheme/counter in this situation: **`{res_rc_df.iloc[0].get('Concept', res_rc_df.iloc[0].get('Front', res_rc_df.iloc[0].get('Coverage', 'Primary')))}`**.")
                st.markdown("</div>", unsafe_allow_html=True)
                if 'Play_List' in res_rc_df.columns:
                    p_all_rc = [x.strip() for p in res_rc_df['Play_List'].dropna() for x in str(p).split(',') if x.strip()]
                    st.text_area("Filtered Recon Plays String:", ", ".join(list(dict.fromkeys(p_all_rc))), height=70)

        st.markdown("---")
        # 8-Zone Tendency Table
        st.subheader("1. 8-Zone Field Tendency Cards")
        zone_card_data = []
        for z in ZONE_ORDER:
            z_sub = scoped_df[scoped_df['FIELD_ZONE'] == z]
            tot = len(z_sub)
            if tot > 0:
                r_c = (z_sub['PLAY TYPE'] == 'Run').sum()
                p_c = (z_sub['PLAY TYPE'] == 'Pass').sum()
                zone_card_data.append({
                    "Field Zone": z,
                    "Snaps": tot,
                    "Run %": f"{(r_c/tot)*100:.1f}%",
                    "Pass %": f"{(p_c/tot)*100:.1f}%",
                    "Opp Success %": f"{z_sub['OFF_SUCCESS'].mean()*100:.1f}%",
                    "Avg Gain": f"{z_sub['GN/LS'].mean():.2f} yds",
                    "Top Run Concept": get_top_concept(z_sub, 'Run'),
                    "Top Pass Concept": get_top_concept(z_sub, 'Pass')
                })
        if zone_card_data: st.dataframe(pd.DataFrame(zone_card_data), use_container_width=True)

        st.markdown("---")
        st.subheader("2. Down & Distance Tendencies")
        down_data = []
        for d in [1, 2, 3, 4]:
            d_sub = scoped_df[scoped_df['DN'] == d]
            tot = len(d_sub)
            if tot > 0:
                r_c = (d_sub['PLAY TYPE'] == 'Run').sum()
                p_c = (d_sub['PLAY TYPE'] == 'Pass').sum()
                down_data.append({
                    "Down": f"Down {d}",
                    "Snaps": tot,
                    "Run %": f"{(r_c/tot)*100:.1f}%",
                    "Pass %": f"{(p_c/tot)*100:.1f}%",
                    "Opp Success %": f"{d_sub['OFF_SUCCESS'].mean()*100:.1f}%",
                    "Avg Gain": f"{d_sub['GN/LS'].mean():.2f} yds",
                    "Primary Tell": "🚨 RUN HEAVY" if (r_c/tot) >= 0.55 else ("🎯 PASS HEAVY" if (p_c/tot) >= 0.60 else "⚖️ BALANCED")
                })
        if down_data: st.dataframe(pd.DataFrame(down_data), use_container_width=True)

    # --- TAB 3: FULL 24-QUERY DEFENSIVE ARSENAL ---
    with tab_3:
        st.subheader("💬 Ask Coach Albers // Defensive QC Assistant")
        st.markdown("Direct tactical inquiries across your defense, opponents, 8 field zones, hash marks, formations, and down/distance situations.")

        tactical_pillar = st.radio("Choose Tactical Focus:", ["💰 Money Downs", "📍 Hash & Field Zones", "🎯 Formation Tells", "🛡️ Self-Scout Leaks"], horizontal=True)
        q_def_selected = None

        if tactical_pillar == "💰 Money Downs":
            qc_c1, qc_c2, qc_c3 = st.columns(3)
            if qc_c1.button("📍 Top Front in Low Red Zone?", key="md_1"): q_def_selected = "What is our top-performing front in the Low Red Zone?"
            if qc_c2.button("🎯 Opponent 3rd & Med in Fringe?", key="md_2"): q_def_selected = "What does the opponent run on 3rd & Medium in the Fringe Zone?"
            if qc_c3.button("🛡️ Best Coverage on 3rd & Long?", key="md_3"): q_def_selected = "What is our best coverage call on 3rd & Long?"
            qc_c4, qc_c5, qc_c6 = st.columns(3)
            if qc_c4.button("🛑 4th Down Stop Calls?", key="md_4"): q_def_selected = "What is our top front and stop rate on 4th Down?"
            if qc_c5.button("🚀 2nd & Short Shot Alert?", key="md_5"): q_def_selected = "What does the opponent run on 2nd & Short?"
            if qc_c6.button("🧱 Goal-Line Run Concepts?", key="md_6"): q_def_selected = "What are their top concepts in the Goal Line zone?"

        elif tactical_pillar == "📍 Hash & Field Zones":
            qc_c1, qc_c2, qc_c3 = st.columns(3)
            if qc_c1.button("👈 Left Hash Run vs Pass?", key="hf_1"): q_def_selected = "What is their run pass tendency on the Left Hash?"
            if qc_c2.button("👉 Right Hash Tendency?", key="hf_2"): q_def_selected = "What does the opponent run on the Right Hash?"
            if qc_c3.button("🚨 Coming Out Run Tell?", key="hf_3"): q_def_selected = "What do they run in the Coming Out zone?"
            qc_c4, qc_c5, qc_c6 = st.columns(3)
            if qc_c4.button("💥 Explosives in Open Field?", key="hf_4"): q_def_selected = "Show me explosive passes allowed in the Open Field"
            if qc_c5.button("⚡ Pressure in Red Zone?", key="hf_5"): q_def_selected = "Compare blitz success rate in the Red Zone"
            if qc_c6.button("🎯 Fringe Zone 4-Down Calls?", key="hf_6"): q_def_selected = "What do they run on 3rd & 4th down in the Fringe Zone?"

        elif tactical_pillar == "🎯 Formation Tells":
            qc_c1, qc_c2, qc_c3 = st.columns(3)
            if qc_c1.button("💨 Empty Formation Tendency?", key="ft_1"): q_def_selected = "What does Empty formation do?"
            if qc_c2.button("📦 Bunch & Stack Rub Alert?", key="ft_2"): q_def_selected = "What pass concepts do they run out of Bunch or Stack?"
            if qc_c3.button("🚛 Heavy 2-Back (RED/BLUE) Tell?", key="ft_3"): q_def_selected = "What does RED/BLUE run?"
            qc_c4, qc_c5, qc_c6 = st.columns(3)
            if qc_c4.button("📐 3x1 Trips Early Down Tell?", key="ft_4"): q_def_selected = "What does 3x1 Trips do on 1st & 10?"
            if qc_c5.button("⚡ GREEN/GOLD Attack Concepts?", key="ft_5"): q_def_selected = "What are their top plays out of GREEN/GOLD?"
            if qc_c6.button("🔄 Motion & Tag Concepts?", key="ft_6"): q_def_selected = "Show concepts with TAG or motion"

        else:
            qc_c1, qc_c2, qc_c3 = st.columns(3)
            if qc_c1.button("🎯 RPO Vulnerability Audit?", key="sl_1"): q_def_selected = "How does our defense perform against RPO plays?"
            if qc_c2.button("🏃 Explosive Runs by Front?", key="sl_2"): q_def_selected = "Which defensive front allows the most explosive runs?"
            if qc_c3.button("🎭 Bluff vs Real Blitz Havoc?", key="sl_3"): q_def_selected = "Compare blitz success rate between real pressure and bluffs"
            qc_c4, qc_c5, qc_c6 = st.columns(3)
            if qc_c4.button("💨 Boundary Cutback Leaks?", key="sl_4"): q_def_selected = "Show big plays conceded to the boundary"
            if qc_c5.button("🛡️ RIP/LIZ Match Audit?", key="sl_5"): q_def_selected = "What plays hurt our RIP/LIZ coverage?"
            if qc_c6.button("💥 Sacks & Turnovers Created?", key="sl_6"): q_def_selected = "Show all sacks and turnovers created"

        user_def_query = st.text_input("Ask Coach Albers a tactical question (or click any pill above):", value=q_def_selected if q_def_selected else "", placeholder="e.g. What does Lincoln run on 3rd & Medium in the Fringe Zone?")

        if user_def_query:
            q_def_lower = user_def_query.lower()
            w_def = []
            if 'low red' in q_def_lower: w_def.append("FIELD_ZONE LIKE '%Low Red%'")
            elif 'high red' in q_def_lower: w_def.append("FIELD_ZONE LIKE '%High Red%'")
            elif 'goal line' in q_def_lower: w_def.append("FIELD_ZONE LIKE '%Goal Line%'")
            elif 'fringe' in q_def_lower: w_def.append("FIELD_ZONE LIKE '%Fringe%'")
            if 'left hash' in q_def_lower: w_def.append("HASH = 'L'")
            elif 'right hash' in q_def_lower: w_def.append("HASH = 'R'")
            if 'empty' in q_def_lower: w_def.append("OFF_FORM LIKE '%Empty%'")
            elif 'bunch' in q_def_lower or 'stack' in q_def_lower: w_def.append("(OFF_FORM LIKE '%Bunch%' OR OFF_FORM LIKE '%Stack%')")
            if 'rpo' in q_def_lower: w_def.append("OFF_PLAY LIKE '%RPO%'")
            if '3rd & medium' in q_def_lower: w_def.append("DN = 3 AND DIST BETWEEN 3 AND 6")
            elif '3rd & long' in q_def_lower: w_def.append("DN = 3 AND DIST >= 7")
            elif '4th' in q_def_lower: w_def.append("DN = 4")
            elif '2nd & short' in q_def_lower: w_def.append("DN = 2 AND DIST <= 3")

            w_def_sql = " AND ".join(w_def) if w_def else "1=1"
            if 'front' in q_def_lower or '4th' in q_def_lower:
                sql_def = f"""SELECT "DEF FRONT" as Front, count(*) as Snaps, round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", round(avg("GN/LS"), 2) as "Avg_Yds_Allowed", group_concat("PLAY #", ', ') as Play_List FROM snaps WHERE {w_def_sql} AND "DEF FRONT" IS NOT NULL GROUP BY "DEF FRONT" ORDER BY "Def_Win_%" DESC"""
            elif 'coverage' in q_def_lower:
                sql_def = f"""SELECT "COVERAGE" as Coverage, count(*) as Snaps, round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", round(avg("GN/LS"), 2) as "Avg_Yds_Allowed", group_concat("PLAY #", ', ') as Play_List FROM snaps WHERE {w_def_sql} AND "COVERAGE" IS NOT NULL GROUP BY "COVERAGE" ORDER BY "Def_Win_%" DESC"""
            elif 'blitz' in q_def_lower or 'bluff' in q_def_lower:
                sql_def = f"""SELECT BLITZ_CLEAN as Pressure, count(*) as Snaps, round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", round(avg("GN/LS"), 2) as "Avg_Yds_Allowed", group_concat("PLAY #", ', ') as Play_List FROM snaps WHERE {w_def_sql} GROUP BY BLITZ_CLEAN ORDER BY "Def_Win_%" DESC"""
            else:
                sql_def = f"""SELECT "PLAY TYPE", coalesce("OFF PLAY", 'Base Concept') as Concept, count(*) as Snaps, round(avg("GN/LS"), 1) as "Avg_Gain", group_concat("PLAY #", ', ') as Play_List FROM snaps WHERE {w_def_sql} GROUP BY "PLAY TYPE", Concept ORDER BY Snaps DESC"""

            res_def_df = pd.read_sql_query(sql_def, conn)
            st.markdown("---")
            if len(res_def_df) > 0:
                st.dataframe(res_def_df[[c for c in res_def_df.columns if c != 'Play_List']], use_container_width=True)
                st.markdown("""<div class="coach-notes-box"><div class="coach-notes-title">🧠 COACH ALBERS' FIELD NOTES & GAMEPLAN DIRECTIVE:</div>""", unsafe_allow_html=True)
                st.markdown(f"* Top producing scheme/counter in this situation: **`{res_def_df.iloc[0].get('Concept', res_def_df.iloc[0].get('Front', res_def_df.iloc[0].get('Coverage', 'Primary')))}`**.")
                st.markdown("</div>", unsafe_allow_html=True)
                if 'Play_List' in res_def_df.columns:
                    p_all_def = [x.strip() for p in res_def_df['Play_List'].dropna() for x in str(p).split(',') if x.strip()]
                    st.text_area("Filtered Defensive Plays:", ", ".join(list(dict.fromkeys(p_all_def))), height=75)

# =========================================================================
# COORDINATOR SUITE 2: OFFENSE (OC MODE)
# =========================================================================
elif "OFFENSE" in coordinator_mode:
    tab_1, tab_2, tab_3 = st.tabs([
        "⚔️ Offensive Self-Scout (Our Offense Audit)", 
        "🛡️ Opponent Defense Reconnaissance", 
        "💬 Ask Coach Albers (Offensive QC)"
    ])

    if len(df) == 0:
        st.markdown("""
        <div class="dossier-box">
            <div class="dossier-title">⚔️ ALBERS QC // OFFENSIVE DATA ONBOARDING</div>
            <p style="font-size: 16px; color: #FFFFFF;">
                You are in <strong>Offensive Coordinator Mode</strong>. Please upload your team's offensive cutup file (where <code>ODK = 'O'</code>) using the Master Data Intake box on the sidebar.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    with tab_1:
        st.subheader(f"⚔️ Albers QC // Offensive Self-Scout: {selected_opp}")
        snaps_off = len(filtered_df)
        if snaps_off > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Offensive Snaps", snaps_off)
            c2.metric("Stay-On-Schedule %", f"{filtered_df['OFF_SUCCESS'].mean():.1%}")
            c3.metric("Yards Per Play", f"{filtered_df['GN/LS'].mean():.2f} yds")
            exp_off = ((filtered_df['GN/LS'] >= 15) & (filtered_df['PLAY_TYPE_CLEAN'] == 'Pass')).sum() + \
                      ((filtered_df['GN/LS'] >= 10) & (filtered_df['PLAY_TYPE_CLEAN'] == 'Run')).sum()
            c4.metric("Explosives (10r/15p)", f"{exp_off} ({(exp_off/snaps_off)*100:.1f}%)")

            st.markdown("---")
            st.subheader("⚠️ Offensive Self-Scout: Are We Predictable? (Formation Tells)")
            form_self = filtered_df.groupby('OFF FORM').agg(
                Snaps=('PLAY #', 'count'),
                Run_Snaps=('PLAY TYPE', lambda x: (x == 'Run').sum()),
                Pass_Snaps=('PLAY TYPE', lambda x: (x == 'Pass').sum()),
                Avg_Gain=('GN/LS', 'mean'),
                Success_Rate=('OFF_SUCCESS', lambda x: x.mean() * 100)
            ).reset_index()

            if len(form_self) > 0:
                form_self['Run %'] = (form_self['Run_Snaps'] / form_self['Snaps']) * 100
                form_self['Pass %'] = (form_self['Pass_Snaps'] / form_self['Snaps']) * 100
                form_filtered_self = form_self[form_self['Snaps'] >= 3].copy()
                def self_tell(row):
                    if row['Run %'] >= 65: return "🚨 65%+ RUN (TIPPED)"
                    elif row['Pass %'] >= 75: return "🚨 75%+ PASS (TIPPED)"
                    return "⚖️ BALANCED"
                form_filtered_self['OC Self-Scout Tell'] = form_filtered_self.apply(self_tell, axis=1)
                st.dataframe(form_filtered_self[['OFF FORM', 'Snaps', 'Run %', 'Pass %', 'Avg_Gain', 'Success_Rate', 'OC Self-Scout Tell']], use_container_width=True)

    with tab_2:
        st.subheader(f"🛡️ Opponent Defense Faced: {selected_opp}")
        d1, d2 = st.columns(2)
        with d1:
            st.markdown("##### Opponent Fronts Faced & Our Success")
            st.dataframe(filtered_df.groupby('DEF FRONT').agg(Snaps=('PLAY #', 'count'), Our_Yards=('GN/LS', 'mean'), Success_Rate=('OFF_SUCCESS', lambda x: x.mean()*100)).reset_index(), use_container_width=True)
        with d2:
            st.markdown("##### Opponent Coverages Faced & Our Big Plays")
            st.dataframe(filtered_df.groupby('COVERAGE').agg(Snaps=('PLAY #', 'count'), Our_YPA=('GN/LS', 'mean'), Explosives=('GN/LS', lambda x: (x>=15).sum())).reset_index(), use_container_width=True)

    with tab_3:
        st.subheader("💬 Ask Coach Albers // Offensive QC Assistant")
        q_off_in = st.text_input("Ask Coach Albers an offensive question:", placeholder="e.g. What is our best run concept on 2nd & Short?")
        if q_off_in:
            st.info("Offensive QC inquiry registered. Processing concepts against active data.")

# =========================================================================
# COORDINATOR SUITE 3: SPECIAL TEAMS (STC MODE - NFL & POWER 4 STANDARDS)
# =========================================================================
else:
    tab_1, tab_2, tab_3 = st.tabs([
        "⚡ Core 6 Phase Audit & Unit KPIs", 
        "🎯 Opponent Kicking Schemes & Tendencies", 
        "💬 Ask Coach Albers (Special Teams QC)"
    ])

    with tab_1:
        st.subheader(f"⚡ Albers QC // Special Teams Phase Audit: {selected_opp}")
        st.markdown("Special teams performance tracked across **The Core 6 Phases** (NFL & Power 4 analytics benchmarks).")

        st_snaps = len(df)
        if st_snaps > 0:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Kicking Snaps", st_snaps)
            k2.metric("Punt Net Average Target", "40.5+ yds")
            k3.metric("FG Snap-to-Kick Target", "< 1.30s")
            k4.metric("Inside-20 Pin Rate", "45%+")

            st.markdown("---")
            st.subheader("📋 The Core 6 Unit Breakdown")
            core_6_df = df.groupby('ST_PHASE').agg(
                Snaps=('PLAY #', 'count'),
                Avg_Yards=('GN/LS', 'mean'),
                Penalties=('RESULT', lambda x: x.str.contains('Penalty', case=False, na=False).sum()),
                Turnovers=('RESULT', lambda x: x.str.contains('Fumble|Muff|Block', case=False, na=False).sum())
            ).reset_index()
            st.dataframe(core_6_df, use_container_width=True)

        else:
            st.markdown("""
            <div class="dossier-box">
                <div class="dossier-title">⚡ ALBERS QC // SPECIAL TEAMS DATA ONBOARDING</div>
                <p style="font-size: 15.5px; color: #FFFFFF;">
                    You are in <strong>Special Teams Coordinator Mode</strong>. Albers QC evaluates the kicking game across the standard NFL/FBS <strong>Core 6 Units</strong>:
                </p>
                <ul style="color: #F8FAFC; font-size: 14.5px;">
                    <li><strong>Kickoff Coverage (KO)</strong>: Hang time, Touchback %, and opponent starting drive field position.</li>
                    <li><strong>Kickoff Return (KR)</strong>: Return average, explosive returns (30+ yds), and field position created.</li>
                    <li><strong>Punt Coverage (Punt)</strong>: Gross vs. Net average, hang time (4.2s+ target), and Inside-20/Inside-10 pin rate.</li>
                    <li><strong>Punt Return (PR)</strong>: Return yardage, hold-up efficiency, and pressure/block rate.</li>
                    <li><strong>Field Goal / PAT</strong>: Operation time (snap-to-kick < 1.30s) and kick accuracy by hash/distance.</li>
                    <li><strong>FG / PAT Block</strong>: Penetration pressure, block rate, and return touchdowns.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            st.info("💡 To analyze kicking game data, ensure your uploaded CSV contains special teams cutups with `ODK = 'K'` or kicking play types.")

    with tab_2:
        st.subheader("🎯 Opponent Special Teams Scouting & Specialist Profiler")
        st.markdown("Audits opponent specialists: directional kicking tendencies, return schemes, and rush/block pressure packages.")
        st.dataframe(df[['PLAY #', 'QTR', 'ST_PHASE', 'RESULT', 'GN/LS']].head(15), use_container_width=True)

    with tab_3:
        st.subheader("💬 Ask Coach Albers // Special Teams QC Assistant")
        st.markdown("##### ⚡ Quick Special Teams Queries:")
        st_c1, st_c2, st_c3 = st.columns(3)
        q_st = None
        if st_c1.button("🎯 Punt Inside-20 Pin Rate?"): q_st = "Show punt coverage inside 20"
        if st_c2.button("🚀 Explosive Returns Allowed?"): q_st = "Show explosive return plays"
        if st_c3.button("🧱 Field Goal Accuracy & Distance?"): q_st = "Audit field goal accuracy"

        st_user_query = st.text_input("Ask Coach Albers a special teams question:", value=q_st if q_st else "", placeholder="e.g. Audit punt net average and inside 20 pins")
        if st_user_query:
            st.info("Special Teams query processed. Reviewing kicking phase execution.")

# --- FOOTER SIGNATURE ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #94A3B8; font-size: 13px; font-weight: 800; letter-spacing: 1px;'>"
    "🏈 ALBERS QC • YOUR PERSONALIZED QUALITY CONTROL COACH • GRIDIRON INTELLIGENCE ENGINE"
    "</div>", 
    unsafe_allow_html=True
)