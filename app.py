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

        # Tactical Outer Ring & Perimeter Dials
        theta = np.linspace(0, 2*np.pi, 300)
        ax.plot(np.cos(theta)*1.18, np.sin(theta)*1.18, color='#1E293B', linewidth=5)
        ax.plot(np.cos(theta)*1.12, np.sin(theta)*1.12, color='#38BDF8', linewidth=1.5, alpha=0.8)

        for deg in range(0, 360, 10):
            rad = np.radians(deg)
            r1 = 1.08 if deg % 30 == 0 else 1.12
            lw = 2.5 if deg % 90 == 0 else (1.8 if deg % 30 == 0 else 0.8)
            col = '#FBBF24' if deg % 90 == 0 else ('#38BDF8' if deg % 30 == 0 else '#475569')
            ax.plot([np.cos(rad)*r1, np.cos(rad)*1.16], [np.sin(rad)*r1, np.sin(rad)*1.16], color=col, linewidth=lw)

        # Armored Football Shield
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

        # Monogram "A" with Gold Border & Black Football Laces
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

# --- HIGH-CONTRAST WAR ROOM CSS ---
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
        font-size: 30px;
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

    /* High-Contrast Interactive Coaching Buttons */
    div.stButton > button {
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

    div[data-baseweb="tag"] {
        background-color: #1E293B !important;
        border: 1.5px solid #38BDF8 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="tag"] span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
    }
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

    .stTable, table {
        background-color: #111C30 !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
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
        border-bottom: 1px solid #1E293B !important;
        font-size: 13.5px !important;
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
    if -10 <= yl <= -1: return "1. Coming Out (-1 to -10)"
    elif -20 <= yl <= -11: return "2. Backed Up (-11 to -20)"
    elif (-49 <= yl <= -21) or (yl == 50) or (41 <= yl <= 49): return "3. Open Field (Own 21 - Opp 41)"
    elif 30 <= yl <= 40: return "4. Fringe Zone (Opp 40-30)"
    elif 21 <= yl <= 29: return "5. Scoring Zone (Opp 29-21)"
    elif 11 <= yl <= 20: return "6. High Red Zone (20-11)"
    elif 6 <= yl <= 10: return "7. Low Red Zone (10-6)"
    elif 1 <= yl <= 5: return "8. Goal Line (5 & In)"
    return "Other"

def get_field_x(yl):
    if yl < 0: return abs(yl)
    elif yl == 50: return 50
    else: return 100 - yl

# --- DATA INTAKE & PROCESSOR ---
def process_dataframe(raw_df, default_source_name="Unknown Opponent"):
    df_clean = raw_df.copy()

    opp_col = next((c for c in df_clean.columns if any(k in c.lower() for k in ['opp', 'game', 'team'])), None)
    if opp_col:
        df_clean['OPPONENT_CLEAN'] = df_clean[opp_col].fillna(default_source_name).astype(str)
    else:
        df_clean['OPPONENT_CLEAN'] = default_source_name

    df_clean['FIELD_ZONE'] = df_clean['YARD LN'].apply(classify_field_zone)
    df_clean['FIELD_X'] = df_clean['YARD LN'].apply(get_field_x)

    def compute_def_success(row):
        result = str(row['RESULT'])
        if any(k in result.lower() for k in ['interception', 'fumble', 'def td', 'safety']): return 1
        gn = row['GN/LS']
        if pd.isna(gn): return 1
        dn, dist = row['DN'], row['DIST']
        if dn == 1: return 1 if gn < 3 else 0
        elif dn == 2: return 1 if gn < (dist / 2.0) else 0
        elif dn in [3, 4]: return 1 if gn < dist else 0
        return 0

    def compute_off_success(row):
        result = str(row['RESULT'])
        if any(k in result.lower() for k in ['interception', 'fumble', 'def td', 'safety']): return 0
        gn = row['GN/LS']
        if pd.isna(gn): return 0
        dn, dist = row['DN'], row['DIST']
        if dn == 1: return 1 if gn >= 3 else 0
        elif dn == 2: return 1 if gn >= (dist / 2.0) else 0
        elif dn in [3, 4]: return 1 if gn >= dist else 0
        return 0

    df_clean['DEF_SUCCESS'] = df_clean.apply(compute_def_success, axis=1)
    df_clean['OFF_SUCCESS'] = df_clean.apply(compute_off_success, axis=1)
    df_clean['PLAY_TYPE_CLEAN'] = df_clean['PLAY TYPE'].fillna('Other')
    df_clean['BLITZ_CLEAN'] = df_clean['BLITZ'].fillna('BASE (NO BLITZ)')
    return df_clean

# --- SIDEBAR WITH DRAG-AND-DROP FILE UPLOADER ---
if os.path.exists(LOGO_FILE):
    st.sidebar.image(LOGO_FILE, width=170)

st.sidebar.markdown("### **ALBERS QC**")
st.sidebar.markdown("<span style='color: #FDE047; font-weight:700;'>Your Personalized QC Coach</span>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.markdown("##### 📥 Data Intake (Drag & Drop)")
uploaded_files = st.sidebar.file_uploader(
    "Drop Game CSVs Here:",
    type=["csv"],
    accept_multiple_files=True,
    help="Drag and drop one or multiple game exports from Hudl, Catapult, or Excel."
)

all_dfs = []
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_base_name = os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ').title()
        try:
            temp_df = pd.read_csv(uploaded_file)
            processed_temp = process_dataframe(temp_df, default_source_name=file_base_name)
            all_dfs.append(processed_temp)
        except Exception as e:
            st.sidebar.error(f"Error loading {uploaded_file.name}: {e}")

if all_dfs:
    df = pd.concat(all_dfs, ignore_index=True)
    status_msg = f"● LIVE UPLOAD: {len(uploaded_files)} GAME(S) | {len(df)} SNAPS"
else:
    csv_file = 'input_file_1.csv'
    if not os.path.exists(csv_file):
        all_csvs = [f for f in os.listdir('.') if f.endswith('.csv')]
        if all_csvs:
            csv_file = all_csvs[0]
        else:
            csv_file = None

    if csv_file and os.path.exists(csv_file):
        fallback_raw = pd.read_csv(csv_file)
        df = process_dataframe(fallback_raw, default_source_name="Opponent")
        status_msg = f"● QC ENGINE ACTIVE | {len(df)} SNAPS INDEXED"
    else:
        st.markdown(f"""
        <div class="albers-header-card">
            <div>
                <div class="albers-brand-title">ALBERS QC</div>
                <div class="albers-brand-tagline">YOUR PERSONALIZED QUALITY CONTROL COACH</div>
            </div>
            <div>
                <span class="albers-status-badge">● STANDBY: AWAITING CSV</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info("👋 **Welcome to Albers QC!**\n\nTo begin analyzing, please **drag and drop your game CSV file** into the box on the left sidebar.")
        st.stop()

conn = sqlite3.connect(':memory:', check_same_thread=False)
df.to_sql('snaps', conn, index=False, if_exists='replace')

def get_top_concept(sub_df, play_type):
    p_df = sub_df[(sub_df['PLAY TYPE'] == play_type) & (sub_df['OFF PLAY'].notna())]
    if len(p_df) == 0: return "-"
    top = p_df['OFF PLAY'].value_counts().head(1)
    return f"{top.index[0]} ({top.values[0]})" if len(top) > 0 else "-"

st.sidebar.markdown("---")

all_opponents = sorted(df['OPPONENT_CLEAN'].unique().tolist())
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
front_options = sorted([x for x in df['DEF FRONT'].dropna().unique()])
selected_front = st.sidebar.multiselect("Def Front", options=front_options, default=front_options)
cov_options = sorted([x for x in df['COVERAGE'].dropna().unique()])
selected_cov = st.sidebar.multiselect("Coverage", options=cov_options, default=cov_options)

# Blitz / Pressure filter
blitz_options = sorted([x for x in df['BLITZ_CLEAN'].unique()])
selected_blitz = st.sidebar.multiselect("Blitz / Pressure Call", options=blitz_options, default=blitz_options)

filtered_df = scoped_df[
    (scoped_df['FIELD_ZONE'].isin(selected_zones)) &
    (scoped_df['DN'].isin(selected_dn)) &
    (scoped_df['DEF FRONT'].isin(selected_front) | scoped_df['DEF FRONT'].isna()) &
    (scoped_df['COVERAGE'].isin(selected_cov) | scoped_df['COVERAGE'].isna()) &
    (scoped_df['BLITZ_CLEAN'].isin(selected_blitz))
]

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

# --- TOP HUD BANNER ---
col_logo, col_banner = st.columns([1, 7])
with col_logo:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=125)

with col_banner:
    st.markdown(f"""
    <div class="albers-header-card">
        <div>
            <div class="albers-brand-title">ALBERS QC</div>
            <div class="albers-brand-tagline">YOUR PERSONALIZED QUALITY CONTROL COACH</div>
        </div>
        <div>
            <span class="albers-status-badge">{status_msg}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- TOP NAVIGATION TABS ---
tab_self, tab_opp, tab_qc = st.tabs([
    "🛡️ Self-Scout (Our Defense Audit)", 
    "🎯 Opponent Advance Reconnaissance", 
    "💬 Ask Coach Albers (Your Personal QC)"
])

# =========================================================================
# TAB 1: SELF-SCOUT (OUR DEFENSE)
# =========================================================================
with tab_self:
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
        st.subheader("📍 Albers QC // Spatial & Tactical Battle Boards")

        col_radar_chart, col_radar_click = st.columns([3, 1])

        with col_radar_chart:
            fig_self = plt.figure(figsize=(10, 8), dpi=150, facecolor='#0B1120')
            ax_pass = fig_self.add_axes([0.05, 0.05, 0.90, 0.88], facecolor='#111827')
            ax_pass.set_xlim(0, 3); ax_pass.set_ylim(0, 3)
            ax_pass.set_xticks([0.5, 1.5, 2.5]); ax_pass.set_xticklabels(['LEFT', 'MIDDLE', 'RIGHT'], color='#FFFFFF', fontsize=11, fontweight='heavy')
            ax_pass.set_yticks([0.5, 1.5, 2.5]); ax_pass.set_yticklabels(['SHORT (0-9y)', 'INTERMEDIATE (10-19y)', 'DEEP (20y+)'], color='#FFFFFF', fontsize=11, fontweight='heavy')
            ax_pass.grid(False)
            ax_pass.tick_params(length=0)

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

        # PASSING ZONE DOSSIER
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

                st.markdown(f"**Play Breakdown for Zone {pz}:**")
                st.dataframe(pz_df[['PLAY #', 'DN', 'DIST', 'OFF FORM', 'OFF PLAY', 'DEF FRONT', 'COVERAGE', 'GN/LS', 'RESULT', 'DEF_SUCCESS']], use_container_width=True)
                
                pz_playlist = pz_df['PLAY #'].astype(str).tolist()
                st.text_area(f"Zone {pz} Video Cutup Playlist ({len(pz_playlist)} plays):", ", ".join(pz_playlist), height=70)
            else:
                st.write(f"No snaps logged in Zone {pz} under current filters.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # 100-YARD FIELD & INTERACTIVE STRIP
        st.subheader("📍 100-Yard Field & Interactive Territory Selector")
        st.markdown("**Click any Field Zone below to inspect its plays and telemetry:**")
        f_cols = st.columns(9)
        if f_cols[0].button("1. Coming Out", key="fbtn_s1"): st.session_state['self_field_zone'] = "1. Coming Out (-1 to -10)"
        if f_cols[1].button("2. Backed Up", key="fbtn_s2"): st.session_state['self_field_zone'] = "2. Backed Up (-11 to -20)"
        if f_cols[2].button("3. Open Field", key="fbtn_s3"): st.session_state['self_field_zone'] = "3. Open Field (Own 21 - Opp 41)"
        if f_cols[3].button("4. Fringe Zone", key="fbtn_s4"): st.session_state['self_field_zone'] = "4. Fringe Zone (Opp 40-30)"
        if f_cols[4].button("5. Scoring Zone", key="fbtn_s5"): st.session_state['self_field_zone'] = "5. Scoring Zone (Opp 29-21)"
        if f_cols[5].button("6. High Red", key="fbtn_s6"): st.session_state['self_field_zone'] = "6. High Red Zone (20-11)"
        if f_cols[7].button("7. Low Red", key="fbtn_s7"): st.session_state['self_field_zone'] = "7. Low Red Zone (10-6)"
        if f_cols[7].button("8. Goal Line", key="fbtn_s8"): st.session_state['self_field_zone'] = "8. Goal Line (5 & In)"
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
            ax_field.scatter(row['FIELD_X'], calc_y(row['HASH'], row['PLAY DIR']), s=140, color='#EF4444', marker='*', edgecolors='yellow', zorder=5)
        for _, row in field_plot_df[field_plot_df['RESULT'].str.contains('Interception|Fumble|Sack|Safety', case=False, na=False)].iterrows():
            ax_field.scatter(row['FIELD_X'], calc_y(row['HASH'], row['PLAY DIR']), s=80, color='#38BDF8', marker='D', edgecolors='white', zorder=4)

        st.pyplot(fig_field)

        # FIELD ZONE DOSSIER
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

                st.markdown(f"**Snap Breakdown for {fz}:**")
                st.dataframe(fz_df[['PLAY #', 'DN', 'DIST', 'OFF FORM', 'OFF PLAY', 'DEF FRONT', 'COVERAGE', 'GN/LS', 'RESULT', 'DEF_SUCCESS']], use_container_width=True)
                
                fz_playlist = fz_df['PLAY #'].astype(str).tolist()
                st.text_area(f"{fz} Video Cutup Playlist ({len(fz_playlist)} plays):", ", ".join(fz_playlist), height=70)
            else:
                st.write(f"No snaps logged in {fz} under current filters.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🎬 Coach Albers' Full Filtered Cutup Playlist")
        playlist_self = filtered_df['PLAY #'].astype(str).tolist()
        st.text_area(f"Play Numbers ({len(playlist_self)} plays):", ", ".join(playlist_self), height=80)

# =========================================================================
# TAB 2: OPPONENT ADVANCE SCOUT (THEIR OFFENSE)
# =========================================================================
with tab_opp:
    st.subheader(f"🎯 Albers QC // Opponent Advance Reconnaissance: {selected_opp}")

    if 'opp_pass_zone' not in st.session_state: st.session_state['opp_pass_zone'] = None
    if 'opp_field_zone' not in st.session_state: st.session_state['opp_field_zone'] = None

    total_opp = len(scoped_df)
    run_opp = (scoped_df['PLAY TYPE'] == 'Run').sum()
    pass_opp = (scoped_df['PLAY TYPE'] == 'Pass').sum()
    run_pct_total = (run_opp / total_opp) * 100 if total_opp > 0 else 0
    pass_pct_total = (pass_opp / total_opp) * 100 if total_opp > 0 else 0
    off_succ_rate = scoped_df['OFF_SUCCESS'].mean() * 100 if total_opp > 0 else 0

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Total Snaps Scouted", total_opp)
    o2.metric("Run / Pass Ratio", f"{run_pct_total:.1f}% Run / {pass_pct_total:.1f}% Pass")
    o3.metric("Offensive Success Rate", f"{off_succ_rate:.1f}%")
    o4.metric("Offensive Avg Yards/Play", f"{scoped_df['GN/LS'].mean():.2f} yds")

    st.markdown("---")
    st.subheader(f"📍 Albers QC // Opponent Tactical Attack Boards: {selected_opp}")

    col_opp_radar, col_opp_click = st.columns([3, 1])

    with col_opp_radar:
        fig_opp = plt.figure(figsize=(10, 8), dpi=150, facecolor='#0B1120')
        ax_opp_pass = fig_opp.add_axes([0.05, 0.05, 0.90, 0.88], facecolor='#111827')
        ax_opp_pass.set_xlim(0, 3); ax_opp_pass.set_ylim(0, 3)
        ax_opp_pass.set_xticks([0.5, 1.5, 2.5]); ax_opp_pass.set_xticklabels(['LEFT', 'MIDDLE', 'RIGHT'], color='#FFFFFF', fontsize=11, fontweight='heavy')
        ax_opp_pass.set_yticks([0.5, 1.5, 2.5]); ax_opp_pass.set_yticklabels(['SHORT (0-9y)', 'INTERMEDIATE (10-19y)', 'DEEP (20y+)'], color='#FFFFFF', fontsize=11, fontweight='heavy')
        ax_opp_pass.grid(False)
        ax_opp_pass.tick_params(length=0)

        zone_coords = {7: (0, 2), 8: (1, 2), 9: (2, 2), 4: (0, 1), 5: (1, 1), 6: (2, 1), 1: (0, 0), 2: (1, 0), 3: (2, 0)}
        total_passes = len(scoped_df[scoped_df['PASS ZONE'].notna()])

        for z, (gx, gy) in zone_coords.items():
            z_df = scoped_df[scoped_df['PASS ZONE'] == z]
            total_z = len(z_df)
            comp_z = z_df['RESULT'].str.contains('Complete', case=False, na=False).sum()
            comp_pct = (comp_z / total_z * 100) if total_z > 0 else 0
            share_pct = (total_z / total_passes * 100) if total_passes > 0 else 0
            avg_gn = z_df['GN/LS'].mean() if total_z > 0 else 0
            exp_z = (z_df['GN/LS'] >= 15).sum()
            
            is_opp_selected = (st.session_state['opp_pass_zone'] == z)
            if is_opp_selected:
                box_col = '#0284C7'; badge = '👉 INSPECTING'; edge_c = '#FDE047'; lw = 3.5
            else:
                box_col = '#991B1B' if (total_z >= 15 or avg_gn >= 15) else ('#C2410C' if (total_z >= 8 or avg_gn >= 8) else '#1E293B')
                badge = '🔥 PRIMARY THREAT' if (total_z >= 15 or avg_gn >= 15) else ('⚡ ACTIVE ATTACK' if (total_z >= 8 or avg_gn >= 8) else '❄️ LOW VOLUME')
                edge_c = '#F59E0B'; lw = 1.5

            rect = patches.Rectangle((gx, gy), 1, 1, facecolor=box_col, edgecolor=edge_c, linewidth=lw, alpha=0.85)
            ax_opp_pass.add_patch(rect)
            ax_opp_pass.text(gx + 0.5, gy + 0.80, f"ZONE {z}", ha='center', color='#FFFFFF', fontsize=12, fontweight='heavy')
            ax_opp_pass.text(gx + 0.5, gy + 0.60, f"{total_z} Att ({share_pct:.0f}% Share)", ha='center', color='#E2E8F0', fontsize=10, fontweight='bold')
            ax_opp_pass.text(gx + 0.5, gy + 0.40, f"{comp_pct:.0f}% Comp | {avg_gn:.1f} YPA", ha='center', color='#FFFFFF', fontsize=10.5, fontweight='heavy')
            ax_opp_pass.text(gx + 0.5, gy + 0.22, f"Explosive Passes: {exp_z}", ha='center', color='#FCA5A5' if exp_z > 1 else '#94A3B8', fontsize=9.5, fontweight='bold')
            ax_opp_pass.text(gx + 0.5, gy + 0.08, badge, ha='center', color='#FDE047', fontsize=8.5, fontweight='heavy')

        ax_opp_pass.set_title("ALBERS QC // Opponent Passing Sector Heatmap", color='#FFFFFF', fontsize=13, fontweight='heavy', pad=12)
        st.pyplot(fig_opp)

    with col_opp_click:
        st.markdown("##### 🎯 Click to Inspect Attack Zone:")
        ok_c1, ok_c2, ok_c3 = st.columns(3)
        if ok_c1.button("Zone 7", key="btn_o7"): st.session_state['opp_pass_zone'] = 7
        if ok_c2.button("Zone 8", key="btn_o8"): st.session_state['opp_pass_zone'] = 8
        if ok_c3.button("Zone 9", key="btn_o9"): st.session_state['opp_pass_zone'] = 9

        if ok_c1.button("Zone 4", key="btn_o4"): st.session_state['opp_pass_zone'] = 4
        if ok_c2.button("Zone 5", key="btn_o5"): st.session_state['opp_pass_zone'] = 5
        if ok_c3.button("Zone 6", key="btn_o6"): st.session_state['opp_pass_zone'] = 6

        if ok_c1.button("Zone 1", key="btn_o1"): st.session_state['opp_pass_zone'] = 1
        if ok_c2.button("Zone 2", key="btn_o2"): st.session_state['opp_pass_zone'] = 2
        if ok_c3.button("Zone 3", key="btn_o3"): st.session_state['opp_pass_zone'] = 3

        if st.button("🔄 Clear Opponent Zone", key="btn_clear_opass"):
            st.session_state['opp_pass_zone'] = None
            st.rerun()

    # Opponent Passing Dossier
    if st.session_state['opp_pass_zone']:
        opz = st.session_state['opp_pass_zone']
        opz_df = scoped_df[scoped_df['PASS ZONE'] == opz]
        
        st.markdown(f"""
        <div class="dossier-box">
            <div class="dossier-title">🎯 OPPONENT PASSING RECONNAISSANCE: ZONE {opz}</div>
        """, unsafe_allow_html=True)
        
        if len(opz_df) > 0:
            oc1, oc2, oc3, oc4 = st.columns(4)
            oc1.metric(f"Zone {opz} Attempts", len(opz_df))
            oc2.metric("Completion %", f"{(opz_df['RESULT'].str.contains('Complete', case=False, na=False).mean())*100:.1f}%")
            oc3.metric("Yards Per Attempt", f"{opz_df['GN/LS'].mean():.1f} YPA")
            oc4.metric("Explosive Passes (>=15)", (opz_df['GN/LS'] >= 15).sum())

            st.markdown(f"**Opponent Concepts Targeted in Zone {opz}:**")
            st.dataframe(opz_df[['PLAY #', 'DN', 'DIST', 'OFF FORM', 'OFF PLAY', 'GN/LS', 'RESULT', 'COVERAGE', 'DEF_SUCCESS']], use_container_width=True)
            
            opz_playlist = opz_df['PLAY #'].astype(str).tolist()
            st.text_area(f"Zone {opz} Film Cutup ({len(opz_playlist)} plays):", ", ".join(opz_playlist), height=70)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Opponent 100-Yard Field & Interactive Strip
    st.subheader("📍 Opponent 100-Yard Field & Territory Selector")
    st.markdown("**Click any Field Zone below to inspect opponent tendencies in that territory:**")
    
    of_cols = st.columns(9)
    if of_cols[0].button("1. Coming Out", key="ofbtn_1"): st.session_state['opp_field_zone'] = "1. Coming Out (-1 to -10)"
    if of_cols[1].button("2. Backed Up", key="ofbtn_2"): st.session_state['opp_field_zone'] = "2. Backed Up (-11 to -20)"
    if of_cols[2].button("3. Open Field", key="ofbtn_3"): st.session_state['opp_field_zone'] = "3. Open Field (Own 21 - Opp 41)"
    if of_cols[3].button("4. Fringe Zone", key="ofbtn_4"): st.session_state['opp_field_zone'] = "4. Fringe Zone (Opp 40-30)"
    if of_cols[4].button("5. Scoring Zone", key="ofbtn_5"): st.session_state['opp_field_zone'] = "5. Scoring Zone (Opp 29-21)"
    if of_cols[5].button("6. High Red", key="ofbtn_6"): st.session_state['opp_field_zone'] = "6. High Red Zone (20-11)"
    if of_cols[6].button("7. Low Red", key="ofbtn_7"): st.session_state['opp_field_zone'] = "7. Low Red Zone (10-6)"
    if of_cols[7].button("8. Goal Line", key="ofbtn_8"): st.session_state['opp_field_zone'] = "8. Goal Line (5 & In)"
    if of_cols[8].button("🔄 Show All", key="ofbtn_all"): 
        st.session_state['opp_field_zone'] = None
        st.rerun()

    fig_opp_field = plt.figure(figsize=(16, 5), dpi=150, facecolor='#0B1120')
    ax_opp_field = fig_opp_field.add_axes([0.05, 0.12, 0.90, 0.78])
    render_8_zone_field(ax_opp_field, f"ALBERS QC // Opponent Strike Map: Big Plays (★) vs. Mistakes/Turnovers (✖)",
                        highlight_zone=st.session_state['opp_field_zone'])

    opp_plot_df = scoped_df
    if st.session_state['opp_field_zone']:
        opp_plot_df = scoped_df[scoped_df['FIELD_ZONE'] == st.session_state['opp_field_zone']]

    for _, row in opp_plot_df[opp_plot_df['GN/LS'] >= 20].iterrows():
        ax_opp_field.scatter(row['FIELD_X'], calc_y(row['HASH'], row['PLAY DIR']), s=140, color='#F59E0B', marker='*', edgecolors='red', linewidth=1, zorder=5)
    for _, row in opp_plot_df[opp_plot_df['RESULT'].str.contains('Interception|Fumble|Sack|Safety', case=False, na=False)].iterrows():
        ax_opp_field.scatter(row['FIELD_X'], calc_y(row['HASH'], row['PLAY DIR']), s=80, color='#DC2626', marker='X', edgecolors='white', linewidth=1, zorder=4)

    st.pyplot(fig_opp_field)

    # Opponent Territory Dossier
    if st.session_state['opp_field_zone']:
        ofz = st.session_state['opp_field_zone']
        ofz_df = scoped_df[scoped_df['FIELD_ZONE'] == ofz]
        
        st.markdown(f"""
        <div class="dossier-box">
            <div class="dossier-title">📍 OPPONENT TERRITORY DOSSIER: {ofz}</div>
        """, unsafe_allow_html=True)
        
        if len(ofz_df) > 0:
            oc1, oc2, oc3, oc4 = st.columns(4)
            oc1.metric("Snaps in Territory", len(ofz_df))
            oc2.metric("Run / Pass Ratio", f"{(ofz_df['PLAY TYPE']=='Run').mean()*100:.0f}% Run / {(ofz_df['PLAY TYPE']=='Pass').mean()*100:.0f}% Pass")
            oc3.metric("Offensive Success", f"{ofz_df['OFF_SUCCESS'].mean()*100:.1f}%")
            oc4.metric("Avg Yards Gained", f"{ofz_df['GN/LS'].mean():.2f} yds")

            st.markdown(f"**Opponent Scheme Breakdown in {ofz}:**")
            st.dataframe(ofz_df[['PLAY #', 'DN', 'DIST', 'OFF FORM', 'OFF PLAY', 'GN/LS', 'RESULT', 'DEF FRONT', 'COVERAGE', 'DEF_SUCCESS']], use_container_width=True)
            
            ofz_playlist = ofz_df['PLAY #'].astype(str).tolist()
            st.text_area(f"{ofz} Video Cutup Playlist ({len(ofz_playlist)} plays):", ", ".join(ofz_playlist), height=70)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # 8-ZONE TENDENCY TABLE
    st.subheader("1. 8-Zone Field Tendency Cards & Arsenal Breakdown")
    zone_card_data = []
    for z in ZONE_ORDER:
        z_sub = scoped_df[scoped_df['FIELD_ZONE'] == z]
        tot = len(z_sub)
        if tot > 0:
            r_c = (z_sub['PLAY TYPE'] == 'Run').sum()
            p_c = (z_sub['PLAY TYPE'] == 'Pass').sum()
            run_pct = (r_c / tot) * 100
            pass_pct = (p_c / tot) * 100
            tell = "🚨 HEAVY RUN (CONSERVATIVE)" if run_pct >= 65 else ("🎯 PASS HEAVY (AGGRESSIVE)" if pass_pct >= 60 else "⚖️ BALANCED ATTACK")
            zone_card_data.append({
                "Field Zone": z,
                "Snaps": tot,
                "Run %": f"{run_pct:.1f}%",
                "Pass %": f"{pass_pct:.1f}%",
                "Off Success %": f"{z_sub['OFF_SUCCESS'].mean()*100:.1f}%",
                "Avg Gain": f"{z_sub['GN/LS'].mean():.2f} yds",
                "Primary Tell": tell,
                "Top Run Concept": get_top_concept(z_sub, 'Run'),
                "Top Pass Concept": get_top_concept(z_sub, 'Pass')
            })

    if zone_card_data:
        st.dataframe(pd.DataFrame(zone_card_data), use_container_width=True)

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
                "Off Success %": f"{d_sub['OFF_SUCCESS'].mean()*100:.1f}%",
                "Avg Gain": f"{d_sub['GN/LS'].mean():.2f} yds",
                "Primary Tell": "🚨 RUN HEAVY" if (r_c/tot) >= 0.55 else ("🎯 PASS HEAVY" if (p_c/tot) >= 0.60 else "⚖️ BALANCED")
            })
    if down_data:
        st.table(pd.DataFrame(down_data))

    st.markdown("---")
    st.subheader("3. Formation 'Tip-Off' Matrix")
    form_df = scoped_df.groupby('OFF FORM').agg(
        Snaps=('PLAY #', 'count'),
        Run_Snaps=('PLAY TYPE', lambda x: (x == 'Run').sum()),
        Pass_Snaps=('PLAY TYPE', lambda x: (x == 'Pass').sum()),
        Avg_Gain=('GN/LS', 'mean'),
        Off_Success=('OFF_SUCCESS', lambda x: x.mean() * 100)
    ).reset_index()

    if len(form_df) > 0:
        form_df['Run %'] = (form_df['Run_Snaps'] / form_df['Snaps']) * 100
        form_df['Pass %'] = (form_df['Pass_Snaps'] / form_df['Snaps']) * 100
        form_filtered = form_df[form_df['Snaps'] >= max(3, int(total_opp * 0.03))].copy()
        def get_tip_off(row):
            if row['Run %'] >= 65: return "🚨 HEAVY RUN TELL"
            elif row['Pass %'] >= 75: return "🎯 HEAVY PASS TELL"
            elif row['Off_Success'] >= 50: return "⚠️ HIGH EFFICIENCY"
            return "⚖️ BALANCED"
        form_filtered['Coaching Tell'] = form_filtered.apply(get_tip_off, axis=1)
        st.dataframe(form_filtered.sort_values(by='Snaps', ascending=False)[['OFF FORM', 'Snaps', 'Run %', 'Pass %', 'Avg_Gain', 'Off_Success', 'Coaching Tell']], use_container_width=True)

    st.subheader("4. 🎬 Opponent Cutup Strings")
    opp_filter = st.selectbox("Generate Cutup For:", [
        "Opponent Explosive Runs (>=10 yds)",
        "Opponent 3rd Down Passing Snaps",
        "Opponent Red Zone Snaps (Zones 6, 7 & 8)",
        "Opponent Coming Out / Backed Up Snaps (Zones 1 & 2)",
        "Opponent Incomplete / Sacked Passing Snaps"
    ])
    if opp_filter == "Opponent Explosive Runs (>=10 yds)":
        p_list = scoped_df[(scoped_df['PLAY TYPE'] == 'Run') & (scoped_df['GN/LS'] >= 10)]['PLAY #'].astype(str).tolist()
    elif opp_filter == "Opponent 3rd Down Passing Snaps":
        p_list = scoped_df[(scoped_df['DN'] == 3) & (scoped_df['PLAY TYPE'] == 'Pass')]['PLAY #'].astype(str).tolist()
    elif opp_filter == "Opponent Red Zone Snaps (Zones 6, 7 & 8)":
        p_list = scoped_df[scoped_df['FIELD_ZONE'].isin(["6. High Red Zone (20-11)", "7. Low Red Zone (10-6)", "8. Goal Line (5 & In)"])]['PLAY #'].astype(str).tolist()
    elif opp_filter == "Opponent Coming Out / Backed Up Snaps (Zones 1 & 2)":
        p_list = scoped_df[scoped_df['FIELD_ZONE'].isin(["1. Coming Out (-1 to -10)", "2. Backed Up (-11 to -20)"])]['PLAY #'].astype(str).tolist()
    else:
        p_list = scoped_df[scoped_df['RESULT'].str.contains('Incomplete|Sack', case=False, na=False)]['PLAY #'].astype(str).tolist()

    st.text_area(f"{opp_filter} Play Numbers ({len(p_list)} plays):", ", ".join(p_list), height=90)

# =========================================================================
# TAB 3: ASK COACH ALBERS (THE EXPANDED ARSENAL)
# =========================================================================
with tab_qc:
    st.subheader("💬 Ask Coach Albers // Your Personalized QC Assistant")
    st.markdown("Direct tactical inquiries across your defense, opponents, 8 field zones, hash marks, formations, and down/distance situations.")

    # Segmented Tactical Focus Areas
    st.markdown("##### ⚡ Quick Coaching Arsenal by Tactical Pillar:")
    tactical_pillar = st.radio(
        "Choose Tactical Focus:",
        ["💰 Money Downs", "📍 Hash & Field Zones", "🎯 Formation Tells", "🛡️ Self-Scout Leaks"],
        horizontal=True
    )

    q_selected = None

    if tactical_pillar == "💰 Money Downs":
        qc_c1, qc_c2, qc_c3 = st.columns(3)
        if qc_c1.button("📍 Top Front in Low Red Zone?"): q_selected = "What is our top-performing front in the Low Red Zone?"
        if qc_c2.button("🎯 Opponent 3rd & Med in Fringe?"): q_selected = "What does the opponent run on 3rd & Medium in the Fringe Zone?"
        if qc_c3.button("🛡️ Best Coverage on 3rd & Long?"): q_selected = "What is our best coverage call on 3rd & Long?"

        qc_c4, qc_c5, qc_c6 = st.columns(3)
        if qc_c4.button("🛑 4th Down Stop Calls?"): q_selected = "What is our top front and stop rate on 4th Down?"
        if qc_c5.button("🚀 2nd & Short Shot Alert?"): q_selected = "What does the opponent run on 2nd & Short?"
        if qc_c6.button("🧱 Goal-Line Run Concepts?"): q_selected = "What are their top concepts in the Goal Line zone?"

    elif tactical_pillar == "📍 Hash & Field Zones":
        qc_c1, qc_c2, qc_c3 = st.columns(3)
        if qc_c1.button("👈 Left Hash Run vs Pass?"): q_selected = "What is their run pass tendency on the Left Hash?"
        if qc_c2.button("👉 Right Hash Tendency?"): q_selected = "What does the opponent run on the Right Hash?"
        if qc_c3.button("🚨 Coming Out Run Tell?"): q_selected = "What do they run in the Coming Out zone?"

        qc_c4, qc_c5, qc_c6 = st.columns(3)
        if qc_c4.button("💥 Explosives in Open Field?"): q_selected = "Show me explosive passes allowed in the Open Field"
        if qc_c5.button("⚡ Pressure in Red Zone?"): q_selected = "Compare blitz success rate in the Red Zone"
        if qc_c6.button("🎯 Fringe Zone 4-Down Calls?"): q_selected = "What do they run on 3rd & 4th down in the Fringe Zone?"

    elif tactical_pillar == "🎯 Formation Tells":
        qc_c1, qc_c2, qc_c3 = st.columns(3)
        if qc_c1.button("💨 Empty Formation Tendency?"): q_selected = "What does Empty formation do?"
        if qc_c2.button("📦 Bunch & Stack Rub Alert?"): q_selected = "What pass concepts do they run out of Bunch or Stack?"
        if qc_c3.button("🚛 Heavy 2-Back (RED/BLUE) Tell?"): q_selected = "What does RED/BLUE run?"

        qc_c4, qc_c5, qc_c6 = st.columns(3)
        if qc_c4.button("📐 3x1 Trips Early Down Tell?"): q_selected = "What does 3x1 Trips do on 1st & 10?"
        if qc_c5.button("⚡ GREEN/GOLD Attack Concepts?"): q_selected = "What are their top plays out of GREEN/GOLD?"
        if qc_c6.button("🔄 Motion & Tag Concepts?"): q_selected = "Show concepts with TAG or motion"

    else: # 🛡️ Self-Scout Leaks
        qc_c1, qc_c2, qc_c3 = st.columns(3)
        if qc_c1.button("🎯 RPO Vulnerability Audit?"): q_selected = "How does our defense perform against RPO plays?"
        if qc_c2.button("🏃 Explosive Runs by Front?"): q_selected = "Which defensive front allows the most explosive runs?"
        if qc_c3.button("🎭 Bluff vs Real Blitz Havoc?"): q_selected = "Compare blitz success rate between real pressure and bluffs"

        qc_c4, qc_c5, qc_c6 = st.columns(3)
        if qc_c4.button("💨 Boundary Cutback Leaks?"): q_selected = "Show big plays conceded to the boundary"
        if qc_c5.button("🛡️ RIP/LIZ Match Audit?"): q_selected = "What plays hurt our RIP/LIZ coverage?"
        if qc_c6.button("💥 Sacks & Turnovers Created?"): q_selected = "Show all sacks and turnovers created"

    default_text = q_selected if q_selected else ""
    user_query = st.text_input("Ask Coach Albers a tactical question (or click any pill above):", value=default_text, placeholder="e.g. What does Lincoln run on 3rd & Medium in the Fringe Zone?")

    def execute_qc_agent(query_str, active_opp):
        q = query_str.lower()
        where_clauses = []

        matched_opp = None
        for opp in all_opponents:
            if opp.lower() in q:
                matched_opp = opp
                break
        
        if matched_opp:
            where_clauses.append(f"OPPONENT_CLEAN = '{matched_opp}'")
            opp_context = matched_opp
        elif active_opp != "ALL OPPONENTS (Full Season)":
            where_clauses.append(f"OPPONENT_CLEAN = '{active_opp}'")
            opp_context = active_opp
        else:
            opp_context = "Full Season"

        # Field Zone Parsing
        zone_label = "All Zones"
        if 'low red' in q:
            where_clauses.append("FIELD_ZONE LIKE '%Low Red Zone%'")
            zone_label = "Low Red Zone (10-6)"
        elif 'high red' in q:
            where_clauses.append("FIELD_ZONE LIKE '%High Red Zone%'")
            zone_label = "High Red Zone (20-11)"
        elif 'goal line' in q or 'goal-line' in q:
            where_clauses.append("FIELD_ZONE LIKE '%Goal Line%'")
            zone_label = "Goal Line (5 & In)"
        elif 'red zone' in q or 'redzone' in q:
            where_clauses.append("FIELD_ZONE IN ('6. High Red Zone (20-11)', '7. Low Red Zone (10-6)', '8. Goal Line (5 & In)')")
            zone_label = "Red Zone (Inside 20)"
        elif 'fringe' in q:
            where_clauses.append("FIELD_ZONE LIKE '%Fringe%'")
            zone_label = "Fringe Zone (Opp 40-30)"
        elif 'scoring' in q:
            where_clauses.append("FIELD_ZONE LIKE '%Scoring%'")
            zone_label = "Scoring Zone (Opp 29-21)"
        elif 'open field' in q:
            where_clauses.append("FIELD_ZONE LIKE '%Open Field%'")
            zone_label = "Open Field (Own 21 - Opp 41)"
        elif 'backed up' in q:
            where_clauses.append("FIELD_ZONE LIKE '%Backed Up%'")
            zone_label = "Backed Up (Own 11-20)"
        elif 'coming out' in q:
            where_clauses.append("FIELD_ZONE LIKE '%Coming Out%'")
            zone_label = "Coming Out (Own 1-10)"

        # Hash Parsing
        if 'left hash' in q:
            where_clauses.append("HASH = 'L'")
            zone_label += " | Left Hash"
        elif 'right hash' in q:
            where_clauses.append("HASH = 'R'")
            zone_label += " | Right Hash"

        # Formation Parsing
        if 'empty' in q:
            where_clauses.append("OFF_FORM LIKE '%Empty%'")
        elif 'bunch' in q or 'stack' in q:
            where_clauses.append("(OFF_FORM LIKE '%Bunch%' OR OFF_FORM LIKE '%Stack%')")
        elif 'red/blue' in q or '2-back' in q:
            where_clauses.append("OFF_FORM LIKE '%RED/BLUE%'")
        elif '3x1' in q or 'trips' in q:
            where_clauses.append("(OFF_FORM LIKE '%Rita/Lisa%' OR OFF_FORM LIKE '%GREEN/GOLD%' OR OFF_FORM LIKE '%Trip%')")
        elif 'green/gold' in q:
            where_clauses.append("OFF_FORM LIKE '%GREEN/GOLD%'")

        # Play Concept / Scheme Parsing
        if 'rpo' in q:
            where_clauses.append("OFF_PLAY LIKE '%RPO%'")
        elif 'rip/liz' in q:
            where_clauses.append("COVERAGE LIKE '%RIP/LIZ%'")

        # Down & Distance Parsing
        sit_label = "All Downs"
        if '3rd & medium' in q or '3rd and medium' in q:
            where_clauses.append("DN = 3 AND DIST BETWEEN 3 AND 6")
            sit_label = "3rd & Medium (3-6 yds)"
        elif '3rd & long' in q or '3rd and long' in q:
            where_clauses.append("DN = 3 AND DIST >= 7")
            sit_label = "3rd & Long (7+ yds)"
        elif '3rd & short' in q or '3rd and short' in q:
            where_clauses.append("DN = 3 AND DIST <= 2")
            sit_label = "3rd & Short (1-2 yds)"
        elif '3rd & 4th' in q:
            where_clauses.append("DN IN (3, 4)")
            sit_label = "3rd & 4th Down"
        elif '3rd down' in q or '3rd dn' in q:
            where_clauses.append("DN = 3")
            sit_label = "3rd Down"
        elif '4th down' in q or '4th' in q:
            where_clauses.append("DN = 4")
            sit_label = "4th Down"
        elif '2nd & short' in q or '2nd and short' in q:
            where_clauses.append("DN = 2 AND DIST <= 3")
            sit_label = "2nd & Short (1-3 yds)"
        elif '2nd & long' in q or '2nd and long' in q:
            where_clauses.append("DN = 2 AND DIST >= 7")
            sit_label = "2nd & Long (7+ yds)"
        elif '2nd down' in q:
            where_clauses.append("DN = 2")
            sit_label = "2nd Down"
        elif '1st down' in q or '1st & 10' in q:
            where_clauses.append("DN = 1")
            sit_label = "1st Down"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        if 'front' in q or '4th down' in q:
            sql = f"""
                SELECT "DEF FRONT" as Front, count(*) as Snaps, 
                       round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", 
                       round(avg("GN/LS"), 2) as "Avg_Yds_Allowed",
                       group_concat("PLAY #", ', ') as Play_List
                FROM snaps 
                WHERE {where_sql} AND "DEF FRONT" IS NOT NULL
                GROUP BY "DEF FRONT" 
                ORDER BY "Def_Win_%" DESC, Snaps DESC
            """
            title = f"Defensive Front Performance ({zone_label} | {sit_label})"
            mode = "front"

        elif 'coverage' in q:
            sql = f"""
                SELECT "COVERAGE" as Coverage, count(*) as Snaps, 
                       round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", 
                       round(avg("GN/LS"), 2) as "Avg_Yds_Allowed",
                       group_concat("PLAY #", ', ') as Play_List
                FROM snaps 
                WHERE {where_sql} AND "COVERAGE" IS NOT NULL
                GROUP BY "COVERAGE" 
                ORDER BY "Def_Win_%" DESC, Snaps DESC
            """
            title = f"Coverage Efficiency ({zone_label} | {sit_label})"
            mode = "coverage"

        elif 'blitz' in q or 'pressure' in q:
            sql = f"""
                SELECT BLITZ_CLEAN as Pressure, count(*) as Snaps, 
                       round(avg(DEF_SUCCESS)*100, 1) as "Def_Win_%", 
                       round(avg("GN/LS"), 2) as "Avg_Yds_Allowed",
                       group_concat("PLAY #", ', ') as Play_List
                FROM snaps 
                WHERE {where_sql}
                GROUP BY BLITZ_CLEAN 
                ORDER BY "Def_Win_%" DESC, Snaps DESC
            """
            title = f"Pressure & Blitz Efficiency ({zone_label} | {sit_label})"
            mode = "pressure"

        elif 'explosive' in q:
            sql = f"""
                SELECT "PLAY #", "DN", "DIST", "FIELD_ZONE", "PLAY TYPE", coalesce("OFF PLAY", 'Unspecified') as Concept, 
                       "DEF FRONT", "COVERAGE", "GN/LS" as Yards_Gained
                FROM snaps 
                WHERE {where_sql} AND "GN/LS" >= 15
                ORDER BY "GN/LS" DESC
            """
            title = f"Explosive Plays Allowed ({zone_label} | {sit_label})"
            mode = "explosive"

        elif 'turnover' in q or 'sack' in q:
            sql = f"""
                SELECT "PLAY #", "DN", "DIST", "FIELD_ZONE", "PLAY TYPE", "RESULT", "DEF FRONT", "COVERAGE", "BLITZ_CLEAN", "GN/LS"
                FROM snaps 
                WHERE {where_sql} AND (RESULT LIKE '%Sack%' OR RESULT LIKE '%Interception%' OR RESULT LIKE '%Fumble%' OR RESULT LIKE '%Safety%')
                ORDER BY "DN" ASC
            """
            title = f"Havoc, Sacks & Turnovers Created ({zone_label} | {sit_label})"
            mode = "havoc"

        else:
            sql = f"""
                SELECT "PLAY TYPE", coalesce("OFF PLAY", 'Unspecified Concept') as Concept, 
                       count(*) as Snaps, 
                       round(avg("GN/LS"), 1) as "Avg_Gain",
                       group_concat("PLAY #", ', ') as Play_List
                FROM snaps 
                WHERE {where_sql}
                GROUP BY "PLAY TYPE", Concept 
                ORDER BY Snaps DESC
            """
            title = f"Tactical Scheme Breakdown ({opp_context} | {zone_label} | {sit_label})"
            mode = "scheme"

        res_df = pd.read_sql_query(sql, conn)
        return title, mode, opp_context, zone_label, sit_label, res_df

    if user_query:
        title, mode, opp_ctx, z_lbl, s_lbl, result_df = execute_qc_agent(user_query, selected_opp)
        
        st.markdown("---")
        st.subheader(f"📋 Coach Albers' Report: {title}")

        if len(result_df) > 0:
            k1, k2, k3 = st.columns(3)
            tot_snaps = result_df['Snaps'].sum() if 'Snaps' in result_df.columns else len(result_df)
            k1.metric("Sample Size", f"{tot_snaps} Snaps")
            k2.metric("Opponent Scope", opp_ctx)
            k3.metric("Situational Context", f"{z_lbl} | {s_lbl}")

            display_cols = [c for c in result_df.columns if c != 'Play_List']
            st.dataframe(result_df[display_cols], use_container_width=True)

            # COACH ALBERS' FIELD NOTES
            st.markdown("""
            <div class="coach-notes-box">
                <div class="coach-notes-title">🧠 COACH ALBERS' FIELD NOTES & GAMEPLAN DIRECTIVE:</div>
            """, unsafe_allow_html=True)

            if mode == "front":
                top_front = result_df.iloc[0]['Front']
                top_win = result_df.iloc[0]['Def_Win_%']
                avg_yds = result_df.iloc[0]['Avg_Yds_Allowed']
                st.markdown(f"""
                * **Primary Call:** `{top_front}` is your highest-performing front in this situation (**{top_win}% defensive win rate**, holding the offense to **{avg_yds} yards**).
                * **QC Recommendation:** Green-light `{top_front}` on your wristband / call sheet for {z_lbl}.
                """)
            elif mode == "coverage":
                top_cov = result_df.iloc[0]['Coverage']
                top_win = result_df.iloc[0]['Def_Win_%']
                st.markdown(f"""
                * **Lockdown Look:** `{top_cov}` ranks #1 with a **{top_win}% defensive win rate**.
                * **Assignment Note:** Ensure boundary safety communication and cutback lane fits are reviewed during Friday walk-through.
                """)
            elif mode == "pressure":
                top_press = result_df.iloc[0]['Pressure']
                top_win = result_df.iloc[0]['Def_Win_%']
                st.markdown(f"""
                * **Optimal Pressure:** `{top_press}` leads the unit with a **{top_win}% win rate**.
                * **Self-Scout Alert:** Mix in simulated pressure (Bluffs) to freeze the quarterback and prevent offensive line slide adjustments.
                """)
            elif mode == "scheme":
                runs = result_df[result_df['PLAY TYPE'] == 'Run']['Snaps'].sum()
                passes = result_df[result_df['PLAY TYPE'] == 'Pass']['Snaps'].sum()
                top_concept = result_df.iloc[0]['Concept']
                st.markdown(f"""
                * **Run / Pass Ratio:** Offense leans **{runs} Runs vs. {passes} Passes** in this situation.
                * **Primary Concept Alert:** Offense heavily favors **`{top_concept}`** as their go-to call.
                * **Practice Installation:** Drill defensive ends and overhangs against this concept during Tuesday/Wednesday practice.
                """)
            elif mode == "havoc":
                st.markdown(f"* Created **{len(result_df)} game-changing negative plays / turnovers** in this situation. Review tape to reinforce player execution.")
            else:
                st.markdown(f"* Surrendered **{len(result_df)} explosive plays** in this situation. Audit film below for missed tackles and coverage busts.")

            st.markdown("</div>", unsafe_allow_html=True)

            # FILM ROOM PLAYLIST
            st.markdown("##### 🎬 Coach Albers' Film Room Playlist:")
            if 'Play_List' in result_df.columns:
                all_plays = []
                for p_str in result_df['Play_List'].dropna():
                    all_plays.extend([x.strip() for x in str(p_str).split(',') if x.strip()])
                unique_plays = list(dict.fromkeys(all_plays))
                st.text_area("Filtered Play Numbers (Copy & paste directly into Hudl/Catapult):", ", ".join(unique_plays), height=80)
            elif 'PLAY #' in result_df.columns:
                p_list = result_df['PLAY #'].astype(str).tolist()
                st.text_area("Filtered Play Numbers (Copy & paste directly into Hudl/Catapult):", ", ".join(p_list), height=80)

        else:
            st.warning(f"No snaps in the dataset match '{user_query}' under the current scope. Try widening the situation or selecting 'ALL OPPONENTS'.")

# --- FOOTER SIGNATURE ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #94A3B8; font-size: 13px; font-weight: 800; letter-spacing: 1px;'>"
    "🏈 ALBERS QC • YOUR PERSONALIZED QUALITY CONTROL COACH • GRIDIRON INTELLIGENCE ENGINE"
    "</div>", 
    unsafe_allow_html=True
)