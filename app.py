"""
DishDash — Streamlit Web App
=============================
Run with:   streamlit run app.py
Make sure dishdash.db exists first (run pipeline.py once).
"""

import sqlite3
import math
import random

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams["text.usetex"] = False
mpl.rcParams["axes.formatter.use_mathtext"] = False
import matplotlib.patches as mpatches
import numpy as np

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="DishDash",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme Toggle ──────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
_dark = st.session_state.dark_mode


# ── Constants ─────────────────────────────────────────────────
NYU_LAT, NYU_LNG = 40.7295, -73.9965
SEARCH_RADIUS_M  = 800
DB_PATH          = "dishdash.db"

NS_COLOR = {
    "a": "#2d5a27", "b": "#6a9b5c", "c": "#c4854c",
    "d": "#c46a32", "e": "#b84233",
}
PRICE_ORDER = {"": 0, None: 0, "$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
PALETTE = [
    "#2d5a27", "#c4854c", "#1a1a1a", "#6a9b5c", "#b84233",
    "#3d7a6a", "#d4a574", "#4a6741", "#8b6547", "#5a8a4f",
    "#7a5c3e", "#2a6b5a", "#9b7b5e", "#3a5a3a",
]

CUISINE_MAP = {
    "pizza": ["pizza"], "italian": ["pasta", "pizza", "risotto"],
    "chinese": ["noodles", "fried rice", "dumplings"],
    "japanese": ["sushi", "ramen", "miso"], "sushi": ["sushi", "sashimi"],
    "mexican": ["burrito", "taco", "nachos"], "burger": ["burger", "hamburger"],
    "american": ["burger", "sandwich", "fries"], "indian": ["curry", "naan", "biryani"],
    "thai": ["pad thai", "curry", "spring roll"],
    "mediterranean": ["hummus", "falafel", "pita"],
    "french": ["croissant", "baguette", "quiche"],
    "korean": ["bibimbap", "kimchi", "bulgogi"],
    "vietnamese": ["pho", "banh mi", "spring roll"],
    "sandwich": ["sandwich", "sub"], "coffee_shop": ["coffee", "latte", "muffin"],
    "cafe": ["coffee", "pastry", "sandwich"], "unknown": ["meal", "food"],
}

# ── Custom CSS (dynamic light/dark) ──────────────────────────
_bg = "#141414" if _dark else "#fafaf8"
_surface = "#1e1e1e" if _dark else "#ffffff"
_surface_hover = "#2a2a2a" if _dark else "#f5f5f2"
_border = "#333333" if _dark else "#e8e6e1"
_text1 = "#e8e8e8" if _dark else "#1a1a1a"
_text2 = "#a0a0a0" if _dark else "#6b6b6b"
_textm = "#666666" if _dark else "#9a9a9a"
_accent = "#4a9e3f" if _dark else "#2d5a27"
_accent_lt = "#1a2e18" if _dark else "#e8f0e6"
_hero_bg = "#0a0a0a" if _dark else "#1a1a1a"
_shadow_o = "0.25" if _dark else "0.06"
_card_chart_bg = "#1a1a1a" if _dark else "#f5f4f0"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Fraunces:opsz,wght@9..144,700&display=swap');

:root {{
    --bg: {_bg};
    --surface: {_surface};
    --surface-hover: {_surface_hover};
    --border: {_border};
    --text-primary: {_text1};
    --text-secondary: {_text2};
    --text-muted: {_textm};
    --accent: {_accent};
    --accent-light: {_accent_lt};
    --accent-warm: #c4854c;
    --score-excellent: {_accent};
    --score-great: {"#6db85f" if _dark else "#5a8a4f"};
    --score-decent: #c4854c;
    --score-low: #c47832;
    --score-poor: #b84233;
    --radius: 12px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,{_shadow_o});
    --shadow-md: 0 4px 16px rgba(0,0,0,{_shadow_o});
    --shadow-lg: 0 8px 32px rgba(0,0,0,{_shadow_o});
}}

html, body, [class*="css"] {{ font-family: 'Outfit', sans-serif; color: var(--text-primary); }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stApp {{ background: var(--bg); }}

/* Tabs */
button[data-baseweb="tab"] {{ font-family: 'Outfit', sans-serif !important; }}
button[data-baseweb="tab"] p {{ color: var(--text-secondary) !important; font-weight: 500 !important; font-size: 15px !important; }}
button[aria-selected="true"] p {{ color: var(--text-primary) !important; font-weight: 700 !important; }}
div[data-testid="stCheckbox"] label p {{ color: var(--text-primary) !important; }}

/* Hero */
.dd-hero {{
    background: {_hero_bg};
    border-radius: 20px;
    padding: 40px 44px 36px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}}
.dd-hero::before {{
    content: '';
    position: absolute;
    right: -40px; top: -40px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(45,90,39,0.3) 0%, transparent 70%);
    border-radius: 50%;
}}
.dd-hero::after {{
    content: '';
    position: absolute;
    left: 30%; bottom: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(196,133,76,0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.dd-hero h1 {{ font-family: 'Fraunces', serif; font-size: 48px; color: #ffffff; margin: 0 0 8px 0; letter-spacing: -1.5px; position: relative; z-index: 1; }}
.dd-hero p {{ color: rgba(255,255,255,0.55); font-size: 15px; margin: 0 0 20px 0; font-weight: 400; letter-spacing: 0.3px; position: relative; z-index: 1; }}
.dd-pill {{
    display: inline-block;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 100px;
    padding: 6px 16px; font-size: 13px;
    color: rgba(255,255,255,0.7);
    margin-right: 8px; margin-top: 4px;
    font-weight: 500; position: relative; z-index: 1;
    backdrop-filter: blur(4px);
}}

/* Cards */
.dd-card {{
    background: var(--surface);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 8px;
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    transition: all 0.2s ease;
}}
.dd-card:hover {{ box-shadow: var(--shadow-md); transform: translateY(-1px); }}
.dd-card-left {{ flex: 1; }}
.dd-card-right {{ text-align: right; min-width: 100px; padding-left: 16px; }}
.dd-card-name {{ font-size: 17px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; letter-spacing: -0.3px; }}
.dd-cuisine-tag {{
    display: inline-block;
    background: var(--accent-light);
    color: var(--accent);
    border-radius: 100px;
    padding: 3px 12px; font-size: 11px; font-weight: 600;
    text-transform: capitalize; letter-spacing: 0.2px;
}}
.dd-detail {{ font-size: 13px; color: var(--text-secondary); margin-top: 6px; }}
.dd-rating {{ font-size: 28px; font-weight: 800; color: var(--text-primary); line-height: 1; letter-spacing: -1px; }}
.dd-stars {{ color: var(--accent-warm); font-size: 12px; margin-top: 2px; letter-spacing: 1px; }}
.dd-price {{ font-size: 14px; color: var(--accent); font-weight: 700; margin-top: 4px; }}
.dd-ns-badge {{ display: inline-block; color: #fff; border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-right: 6px; }}
.dd-sentiment-pos {{ color: var(--accent); font-weight: 600; }}
.dd-sentiment-neg {{ color: var(--score-poor); font-weight: 600; }}
.dd-section {{ font-size: 22px; font-weight: 700; color: var(--text-primary); border-left: 3px solid var(--accent); padding-left: 14px; margin: 28px 0 16px; letter-spacing: -0.5px; }}
.dd-empty {{ text-align: center; color: var(--text-muted); padding: 56px 0; font-size: 15px; }}

/* Force readable text in metrics and detail panel */
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] div[data-testid="stMetricValue"],
div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {{ color: {_text1} !important; }}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] div {{ color: {_text1} !important; }}
div[data-testid="stDataFrame"] {{ color: {_text1} !important; }}

div[data-testid="stSelectbox"] label p,
div[data-testid="stTextInput"] label p,
div[data-testid="stSlider"] label p,
div[data-testid="stCheckbox"] label p,
div[data-testid="stMultiSelect"] label p {{ color: {_text1} !important; }}

/* Sidebar styling */
section[data-testid="stSidebar"] {{ background: {"#0a0a0a" if _dark else "#1a1a2e"}; }}
section[data-testid="stSidebar"] * {{ color: {"#d0d0d0" if _dark else "#e8edf5"} !important; }}
section[data-testid="stSidebar"] h3 {{ color: #ffffff !important; }}

/* Prominent sidebar toggle when collapsed */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {{
    background: {_accent} !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3) !important;
    z-index: 99999 !important;
    position: fixed !important;
    top: 0.6rem !important;
    left: 0.6rem !important;
    border: 2px solid {_accent} !important;
}}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {{
    color: #ffffff !important;
    fill: #ffffff !important;
    width: 20px !important;
    height: 20px !important;
}}
[data-testid="stSidebarCollapsedControl"]::after,
[data-testid="collapsedControl"]::after {{
    content: " Filters";
    color: #ffffff !important;
    font-weight: 700 !important;
    font-family: Outfit, Arial, sans-serif !important;
    margin-left: 6px !important;
    font-size: 14px !important;
}}
[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="collapsedControl"]:hover {{
    transform: scale(1.05);
    filter: brightness(1.15);
    transition: all 0.15s ease;
}}
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────

def estimate_nutrition(df):
    """Fill missing nutrition data with estimates based on cuisine averages.
    Venues with 'unknown' cuisine get the overall cross-cuisine average."""
    # Cross-cuisine averages (computed from the 17 known cuisine profiles)
    CUISINE_NUTRITION = {
        "pizza":         {"cal": 266, "fat": 11.2, "protein": 11.4, "carbs": 30.2, "ns": "d"},
        "italian":       {"cal": 312, "fat": 12.8, "protein": 10.6, "carbs": 38.4, "ns": "c"},
        "chinese":       {"cal":  64, "fat":  2.2, "protein":  3.8, "carbs":  9.6, "ns": "a"},
        "japanese":      {"cal": 152, "fat":  3.1, "protein":  8.8, "carbs": 21.4, "ns": "b"},
        "sushi":         {"cal": 143, "fat":  2.8, "protein":  9.2, "carbs": 19.6, "ns": "a"},
        "mexican":       {"cal": 198, "fat":  7.6, "protein":  9.4, "carbs": 24.8, "ns": "c"},
        "burger":        {"cal": 295, "fat": 16.4, "protein": 15.2, "carbs": 22.8, "ns": "d"},
        "american":      {"cal": 248, "fat": 11.8, "protein": 12.6, "carbs": 24.2, "ns": "c"},
        "indian":        {"cal": 186, "fat":  8.2, "protein":  7.8, "carbs": 22.4, "ns": "c"},
        "thai":          {"cal": 162, "fat":  6.4, "protein":  8.6, "carbs": 18.8, "ns": "b"},
        "mediterranean": {"cal": 184, "fat":  9.6, "protein":  7.4, "carbs": 18.2, "ns": "b"},
        "french":        {"cal": 338, "fat": 18.6, "protein":  8.2, "carbs": 34.6, "ns": "c"},
        "korean":        {"cal": 148, "fat":  4.8, "protein":  9.6, "carbs": 18.4, "ns": "b"},
        "vietnamese":    {"cal": 112, "fat":  2.4, "protein":  7.8, "carbs": 16.4, "ns": "a"},
        "sandwich":      {"cal": 226, "fat":  8.4, "protein": 11.2, "carbs": 26.8, "ns": "c"},
        "coffee_shop":   {"cal":  62, "fat":  1.8, "protein":  2.4, "carbs":  9.6, "ns": "b"},
        "cafe":          {"cal": 118, "fat":  4.2, "protein":  4.8, "carbs": 16.2, "ns": "b"},
    }
    # Overall average across all cuisines (for "unknown" types)
    all_cals = [v["cal"] for v in CUISINE_NUTRITION.values()]
    all_fats = [v["fat"] for v in CUISINE_NUTRITION.values()]
    all_pros = [v["protein"] for v in CUISINE_NUTRITION.values()]
    all_carbs = [v["carbs"] for v in CUISINE_NUTRITION.values()]
    OVERALL_AVG = {
        "cal": round(sum(all_cals) / len(all_cals), 1),
        "fat": round(sum(all_fats) / len(all_fats), 1),
        "protein": round(sum(all_pros) / len(all_pros), 1),
        "carbs": round(sum(all_carbs) / len(all_carbs), 1),
        "ns": "c",  # middle grade for unknown
    }

    rows = df.copy()

    for col, key in [("avg_cal", "cal"), ("avg_fat", "fat"), ("avg_protein", "protein"), ("avg_carbs", "carbs")]:
        if col not in rows.columns:
            rows[col] = None
        rows[col] = pd.to_numeric(rows[col], errors="coerce")

    # Track which rows we estimate
    rows["nutrition_estimated"] = False

    for idx, row in rows.iterrows():
        if pd.notna(row.get("avg_cal")) and row["avg_cal"] > 0:
            continue  # already has real data

        cuisine = str(row.get("cuisine_key") or "unknown")
        profile = CUISINE_NUTRITION.get(cuisine, OVERALL_AVG)

        rows.at[idx, "avg_cal"]     = profile["cal"]
        rows.at[idx, "avg_fat"]     = profile["fat"]
        rows.at[idx, "avg_protein"] = profile["protein"]
        rows.at[idx, "avg_carbs"]   = profile["carbs"]
        rows.at[idx, "nutrition_estimated"] = True

        # Only fill nutriscore if missing
        ns = row.get("nutriscore")
        if not ns or str(ns).lower() in ("nan", "none", "unknown", ""):
            rows.at[idx, "nutriscore"] = profile["ns"]

    return rows


def compute_dd_score(df):
    """Composite 0-10 score for every venue. Also assigns estimated ratings."""
    NS_SCORE = {"a": 10, "b": 8, "c": 5, "d": 2, "e": 0}
    CUISINE_AVG = {
        "sushi": 4.4, "japanese": 4.3, "italian": 4.3, "french": 4.3,
        "mediterranean": 4.2, "vietnamese": 4.2, "american": 4.1,
        "thai": 4.1, "korean": 4.1, "indian": 4.0, "chinese": 4.0,
        "mexican": 3.9, "burger": 3.9, "sandwich": 3.9,
        "coffee_shop": 4.2, "cafe": 4.1, "pizza": 4.0, "unknown": 3.8,
    }
    GLOBAL_MEAN, K = 4.1, 200

    rows = df.copy()
    rows["google_rating"] = pd.to_numeric(rows.get("google_rating"), errors="coerce")
    rows["rating_count"]  = pd.to_numeric(rows.get("rating_count"), errors="coerce")

    # Assign estimated rating for venues with no Google data
    def est_rating(row):
        if pd.notna(row["google_rating"]):
            return row["google_rating"]
        cuisine = str(row.get("cuisine_key") or "unknown")
        base = CUISINE_AVG.get(cuisine, 3.8)
        # Add small Nutri-Score bonus: healthier cuisines get a slight bump
        ns = str(row.get("nutriscore") or "").lower()
        ns_bump = {"a": 0.15, "b": 0.08, "c": 0.0, "d": -0.05, "e": -0.1}.get(ns, 0)
        return round(min(max(base + ns_bump, 1.0), 5.0), 1)

    rows["display_rating"] = rows.apply(est_rating, axis=1)

    def calc(row):
        r, rc = row["google_rating"], row.get("rating_count")
        if pd.isna(r):
            cuisine_r = CUISINE_AVG.get(str(row.get("cuisine_key") or "unknown"), 3.8)
            r_s = (cuisine_r - 1) / 4 * 10 * 0.6
        else:
            rc_v = rc if pd.notna(rc) else 0
            bayesian = (rc_v * r + K * GLOBAL_MEAN) / (rc_v + K)
            r_s = (bayesian - 1) / 4 * 10
        ns = row.get("nutriscore")
        ns_score = NS_SCORE.get(str(ns).lower(), 5) if ns else 5
        score = r_s * 0.40 + ns_score * 0.20 + 5 * 0.15
        if pd.notna(rc) and pd.notna(r):
            score += min(float(rc) / 1000, 1.0) * 2.5
        return round(min(max(score, 0), 10), 1)

    rows["dd_score"] = rows.apply(calc, axis=1)

    def confidence(row):
        rc = row.get("rating_count")
        if not pd.notna(row.get("google_rating")): return "estimated"
        if pd.notna(rc) and rc < 200: return "low"
        return "ok"

    rows["dd_confidence"] = rows.apply(confidence, axis=1)
    return rows


@st.cache_data(ttl=30)
def load_data():
    """Load from SQLite, fall back to demo data if DB not found.
    Handles both the 393-venue pipeline.py schema and the 2006-venue full schema."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM venues", conn)
        conn.close()
        df["google_rating"] = pd.to_numeric(df.get("google_rating"), errors="coerce")
        df["rating_count"]  = pd.to_numeric(df.get("rating_count"), errors="coerce")

        # Handle column name differences between db versions
        col_map = {
            "avg_calories_100g": "avg_cal",
            "avg_fat_100g": "avg_fat",
            "avg_protein_100g": "avg_protein",
            "avg_carbs_100g": "avg_carbs",
            "avg_sugar_100g": "avg_sugar",
            "avg_sodium_100g": "avg_sodium",
            "common_nutriscore": "nutriscore",
        }
        for old_col, new_col in col_map.items():
            if old_col in df.columns and new_col not in df.columns:
                df[new_col] = df[old_col]

        df["avg_cal"] = pd.to_numeric(df.get("avg_cal"), errors="coerce")

        # Build address from parts if needed
        if "address" not in df.columns or df["address"].isna().all():
            num = df.get("addr_number", pd.Series("", index=df.index)).fillna("")
            street = df.get("addr_street", pd.Series("", index=df.index)).fillna("")
            df["address"] = (num.astype(str) + " " + street.astype(str)).str.strip()

        for c in ["price_level", "cuisine_key", "address", "nutriscore", "neighborhood",
                  "sentiment_label", "sentiment_score", "avg_fat", "avg_protein", "avg_carbs",
                  "phone", "website", "opening_hours", "review_text"]:
            if c not in df.columns:
                df[c] = None

        # Estimate nutrition for venues missing it
        df = estimate_nutrition(df)
        df = compute_dd_score(df)
        return df, "live"
    except Exception:
        return compute_dd_score(estimate_nutrition(make_demo())), "demo"


def make_demo():
    random.seed(42)
    venues = [
        ("Bleecker Street Pizza", "pizza",         "$",    4.6,  0.003, -0.002, "c", 285),
        ("Mamoun's Falafel",      "mediterranean", "$",    4.5,  0.001,  0.004, "b", 195),
        ("Joe Shanghai",          "chinese",        "$$",   4.4,  0.002, -0.003, "c", 340),
        ("Bar Pitti",             "italian",        "$$$",  4.5, -0.001,  0.002, "c", 520),
        ("Sushi Noz",             "sushi",          "$$$$", 4.8,  0.004,  0.001, "a", 180),
        ("Superiority Burger",    "burger",         "$",    4.5, -0.002,  0.005, "c", 410),
        ("The Grey Dog",          "cafe",           "$$",   4.4,  0.005, -0.001, "b", 250),
        ("Raoul's",               "french",         "$$$",  4.7, -0.003, -0.003, "c", 580),
        ("Kunjip",                "korean",         "$$",   4.2,  0.006,  0.003, "b", 340),
        ("Pho Grand",             "vietnamese",     "$$",   4.3, -0.005,  0.002, "b", 290),
        ("Dos Toros Taqueria",    "mexican",        "$",    4.1,  0.002,  0.006, "c", 430),
        ("Cafe Reggio",           "cafe",           "$",    4.5, -0.001, -0.004, "b", 220),
        ("Lucali",                "pizza",          "$$",   4.9,  0.007,  0.003, "d", 295),
        ("Spice Symphony",        "indian",         "$$",   4.2, -0.004,  0.004, "c", 410),
        ("Pure Thai Cookhouse",   "thai",           "$$",   4.4,  0.003, -0.005, "b", 360),
        ("Takahachi",             "japanese",       "$$",   4.5, -0.006,  0.001, "b", 390),
        ("Corner Bistro",         "burger",         "$",    4.3,  0.001,  0.007, "d", 560),
        ("Blue Hill",             "american",       "$$$$", 4.7, -0.004, -0.002, "b", 340),
        ("Buvette",               "french",         "$$$",  4.6,  0.005,  0.005, "c", 510),
        ("Ippudo NY",             "japanese",       "$$",   4.5, -0.007,  0.002, "b", 430),
        ("Xi'an Famous Foods",    "chinese",        "$",    4.3,  0.004, -0.006, "c", 370),
        ("Westville",             "american",       "$$",   4.3,  0.008,  0.001, "b", 380),
        ("Num Pang Kitchen",      "sandwich",       "$$",   4.3, -0.002,  0.006, "c", 380),
        ("Taim Falafel",          "mediterranean",  "$$",   4.4,  0.006, -0.004, "b", 200),
        ("Lupa Osteria Romana",   "italian",        "$$$",  4.6,  0.001,  0.008, "c", 530),
        ("Okonomi Ramen",         "japanese",       "$$",   4.4, -0.003, -0.005, "b", 390),
        ("Artichoke Basilles",    "pizza",          "$",    4.2,  0.009,  0.002, "d", 310),
        ("Murray Cheese Bar",     "american",       "$$$",  4.6, -0.008, -0.001, "d", 490),
        ("Thai Villa",            "thai",           "$$",   4.1,  0.007, -0.007, "b", 380),
        ("Integral Yoga Natural", "cafe",           "$",    4.4, -0.009,  0.003, "a", 180),
    ]
    streets = ["Bleecker St", "MacDougal St", "Thompson St", "Sullivan St", "W 4th St", "6th Ave"]
    rows = []
    for name, cuisine, price, rating, dlat, dlng, ns, cal in venues:
        rows.append({
            "name":            name,
            "cuisine_key":     cuisine,
            "price_level":     price,
            "google_rating":   rating,
            "rating_count":    random.randint(60, 3000),
            "lat":             round(NYU_LAT + dlat + random.uniform(-0.0007, 0.0007), 6),
            "lng":             round(NYU_LNG + dlng + random.uniform(-0.0007, 0.0007), 6),
            "amenity_type":    "cafe" if cuisine in ("cafe", "coffee_shop") else "restaurant",
            "address":         f"{random.randint(1,300)} {random.choice(streets)}, New York NY",
            "review_text":     f"Great {cuisine.replace('_',' ')} near NYU!",
            "avg_cal":         float(cal),
            "avg_fat":         round(cal * 0.11, 1),
            "avg_protein":     round(cal * 0.08, 1),
            "avg_carbs":       round(cal * 0.15, 1),
            "nutriscore":      ns,
            "sentiment_label": random.choice(["POSITIVE", "POSITIVE", "POSITIVE", "NEGATIVE"]),
            "sentiment_score": round(random.uniform(0.72, 0.99), 3),
        })
    return pd.DataFrame(rows)


# ── Card renderer ─────────────────────────────────────────────

def render_card(row):
    r     = row.get("google_rating")
    disp_r = row.get("display_rating", r)
    conf  = row.get("dd_confidence", "ok")
    if pd.notna(r):
        r_str = f"{r:.1f}"
        stars = "★" * int(round(r)) + "☆" * (5 - int(round(r)))
    elif pd.notna(disp_r):
        r_str = f"~{disp_r:.1f}"
        stars = "★" * int(round(disp_r)) + "☆" * (5 - int(round(disp_r)))
    else:
        r_str = "—"
        stars = ""
    price = row.get("price_level") or ""
    ns    = str(row.get("nutriscore") or "").lower()
    ns_bg = NS_COLOR.get(ns, "#aaa")
    ns_html = f'<span class="dd-ns-badge" style="background:{ns_bg}">{ns.upper()}</span>' if ns else ""
    cuisine = str(row.get("cuisine_key") or "").replace("_", " ").title()
    cal   = row.get("avg_cal")
    is_nutr_est = row.get("nutrition_estimated", False)
    cal_s = (f"~{int(cal)} kcal/100g" if is_nutr_est else f"{int(cal)} kcal/100g") if pd.notna(cal) else ""
    addr  = row.get("address") or row.get("addr") or ""
    rc    = row.get("rating_count")
    rc_s  = f"({int(rc):,} reviews)" if pd.notna(rc) and rc else ("(estimated)" if conf == "estimated" else "")
    sent  = row.get("sentiment_label")
    sent_html = ""
    if sent:
        cls = "pos" if sent == "POSITIVE" else "neg"
        icon = "😊" if sent == "POSITIVE" else "😞"
        sent_html = f'<span class="dd-sentiment-{cls}">{icon} {sent.title()}</span>'

    # DishDash Score badge
    dd = row.get("dd_score", 5.0) if pd.notna(row.get("dd_score")) else 5.0
    dd_color = ("#2d5a27" if dd >= 8.0 else "#5a8a4f" if dd >= 6.5
                else "#c4854c" if dd >= 5.0 else "#c47832" if dd >= 3.5 else "#b84233")
    dd_html = f'<span style="background:{dd_color};color:#fff;border-radius:6px;padding:3px 9px;font-size:12px;font-weight:bold;margin-right:8px">🍜 {dd:.1f}/10</span>'

    conf = row.get("dd_confidence", "ok")
    caveat_html = ""
    if conf == "low":
        caveat_html = '<div class="dd-detail" style="font-size:11px;color:#e67e22">⚠️ Score may be unreliable (few reviews)</div>'
    elif conf == "estimated":
        caveat_html = '<div class="dd-detail" style="font-size:11px;color:#888">~ Estimated (no Google data)</div>'

    addr_html = f'<div class="dd-detail" style="margin-top:4px;font-size:12px;color:#666">📍 {addr}</div>' if addr else ""

    return (
        '<div class="dd-card">'
        '<div class="dd-card-left">'
        f'<div class="dd-card-name">{row["name"]}</div>'
        f'<span class="dd-cuisine-tag">{cuisine}</span>'
        f'<div class="dd-detail" style="margin-top:7px">{dd_html}{ns_html}{cal_s}</div>'
        f'{caveat_html}'
        f'<div class="dd-detail">{sent_html}</div>'
        f'{addr_html}'
        '</div>'
        '<div class="dd-card-right">'
        f'<div class="dd-rating">{r_str}</div>'
        f'<div class="dd-stars">{stars}</div>'
        f'<div class="dd-detail" style="font-size:11px">{rc_s}</div>'
        f'<div class="dd-price">{price}</div>'
        '</div>'
        '</div>'
    )


# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────

df, data_src = load_data()

cuisines = sorted(df["cuisine_key"].dropna().unique().tolist())
neighborhoods = sorted(df["neighborhood"].dropna().unique().tolist()) if "neighborhood" in df.columns else []

# ── Sidebar Filters ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🍜 Filters")

    _c1, _c2 = st.columns(2)
    with _c1:
        if st.button("🔄 Refresh", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
    with _c2:
        if st.button("🌙 Dark" if not _dark else "☀️ Light", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown("---")
    search_q    = st.text_input("Search by name", placeholder="e.g. pizza, sushi...")
    cuisine_sel = st.selectbox("Cuisine", ["All cuisines"] + cuisines)
    if neighborhoods:
        nbhd_sel = st.multiselect("Neighborhood", neighborhoods)
    else:
        nbhd_sel = []
    prices      = ["Any price", "$", "$$", "$$$", "$$$$"]
    price_sel   = st.selectbox("Max price", prices)
    min_rating  = st.slider("Min rating", 0.0, 5.0, 0.0, 0.5)
    min_dd      = st.slider("Min DishDash Score 🍜", 0.0, 10.0, 0.0, 0.5)

    ns_opts = {"Any": "any", "A only (best)": "a", "A or B": "b", "A, B, or C": "c"}
    ns_sel = st.selectbox("Nutri-Score ≤", list(ns_opts.keys()))

    sort_opts = ["DishDash Score ↓", "Rating ↓", "Name A-Z", "Price ↑", "Calories ↑"]
    sort_sel  = st.selectbox("Sort by", sort_opts)

    has_rev = st.checkbox("Has reviews only")

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:12px;color:#9a9a9a'>"
        f"Data: {'🟢 Live' if data_src == 'live' else '🔵 Demo'} · "
        f"{len(df)} venues · {len(cuisines)} cuisines"
        f"</div>",
        unsafe_allow_html=True,
    )

# ── Apply Filters ─────────────────────────────────────────────
PRICE_ORDER = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
filtered = df.copy()
if search_q:
    filtered = filtered[filtered["name"].str.lower().str.contains(search_q.lower(), na=False)]
if cuisine_sel != "All cuisines":
    filtered = filtered[filtered["cuisine_key"] == cuisine_sel]
if nbhd_sel:
    filtered = filtered[filtered["neighborhood"].isin(nbhd_sel)]
if price_sel != "Any price":
    cap = PRICE_ORDER[price_sel]
    filtered = filtered[filtered["price_level"].map(lambda p: PRICE_ORDER.get(str(p) if p else "", 99) <= cap)]
if min_rating > 0:
    filtered = filtered[filtered["google_rating"].fillna(-1) >= min_rating]
if min_dd > 0 and "dd_score" in filtered.columns:
    filtered = filtered[filtered["dd_score"] >= min_dd]

ns_val = ns_opts[ns_sel]
NS_ORD = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
if ns_val != "any":
    thr = NS_ORD[ns_val]
    filtered = filtered[
        filtered["nutriscore"].apply(lambda x: NS_ORD.get(str(x).lower(), 99) <= thr if x else False)
    ]
if has_rev:
    filtered = filtered[filtered["review_text"].fillna("").str.strip().astype(bool)]

if sort_sel == "DishDash Score ↓" and "dd_score" in filtered.columns:
    filtered = filtered.sort_values("dd_score", ascending=False)
elif sort_sel == "Rating ↓":
    filtered = filtered.sort_values("google_rating", ascending=False, na_position="last")
elif sort_sel == "Name A-Z":
    filtered = filtered.sort_values("name")
elif sort_sel == "Price ↑":
    filtered = filtered.sort_values("price_level", key=lambda s: s.map(lambda x: PRICE_ORDER.get(x, 0)))
elif sort_sel == "Calories ↑":
    filtered = filtered.sort_values("avg_cal", na_position="last")


# ── Hero banner ───────────────────────────────────────────────
avg_r  = df["google_rating"].mean()
n_cuis = df["cuisine_key"].nunique()
st.markdown(f"""
            

            
            
<div class="dd-hero">
  <h1>DishDash</h1>
  <p>Hyperlocal Restaurant Discovery · NYU / Greenwich Village</p>
  <span class="dd-pill">📍 {len(df)} venues</span>
  <span class="dd-pill">⭐ {avg_r:.2f} avg rating</span>
  <span class="dd-pill">🍴 {n_cuis} cuisines</span>
  <span class="dd-pill">{'🟢 Live data' if data_src == 'live' else '🔵 Demo data'}</span>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search", "🗺️ Map", "📊 Analytics", "🤖 Recommender"])


# ══════════════════════════════════════════════════════════════
# TAB 1 — Search & Filter
# ══════════════════════════════════════════════════════════════
with tab1:
    st.markdown(f'<div class="dd-section">Results ({len(filtered)} restaurants)</div>',
                unsafe_allow_html=True)

    if filtered.empty:
        st.markdown('<div class="dd-empty">No restaurants match your filters — try widening them.</div>',
                    unsafe_allow_html=True)
    else:
        for _, row in filtered.head(25).iterrows():
            st.markdown(render_card(row), unsafe_allow_html=True)
        if len(filtered) > 25:
            st.caption(f"Showing 25 of {len(filtered)} results")


# ══════════════════════════════════════════════════════════════
# TAB 2 — Folium Map
# ══════════════════════════════════════════════════════════════
    # ── Venue Detail Panel ─────────────────────────────────
    if not filtered.empty:
        st.markdown('<div class="dd-section">Venue Detail</div>', unsafe_allow_html=True)
        rated_names = filtered[filtered["google_rating"].notna()]["name"].tolist()
        all_names = filtered["name"].tolist()
        default_idx = all_names.index(rated_names[0]) if rated_names else 0
        pick = st.selectbox("Select a venue for details", all_names, index=default_idx, key="detail_pick")
        row = filtered[filtered["name"] == pick].iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        r_val = row.get("google_rating")
        disp_r_val = row.get("display_rating", r_val)
        conf_val = row.get("dd_confidence", "ok")
        if pd.notna(r_val):
            c1.metric("Google Rating", f"{r_val:.1f}")
        elif pd.notna(disp_r_val):
            c1.metric("Est. Rating", f"~{disp_r_val:.1f}")
        else:
            c1.metric("Rating", "-")
        c2.metric("Price", row.get("price_level") if pd.notna(row.get("price_level")) and row.get("price_level") else "-")
        dd_val = row.get("dd_score")
        c3.metric("DishDash Score", f"{dd_val:.1f}/10" if pd.notna(dd_val) else "-")
        ns_val_d = row.get("nutriscore")
        c4.metric("Nutri-Score", str(ns_val_d).upper() if pd.notna(ns_val_d) and ns_val_d and str(ns_val_d).lower() not in ("nan", "none", "unknown") else "-")

        detail_left, detail_right = st.columns([1, 1])
        with detail_left:
            st.markdown(f(f'<p style="color:{_text1};font-weight:bold">Nutrition (cuisine avg per 100g){" — estimated" if row.get("nutrition_estimated") else ""}</p>'), unsafe_allow_html=True)
            nut_data = {
                "Nutrient": ["Calories", "Fat", "Protein", "Carbs"],
                "Value": [
                    f"{int(row['avg_cal'])} kcal" if pd.notna(row.get('avg_cal')) else "-",
                    f"{row['avg_fat']:.1f} g" if pd.notna(row.get('avg_fat')) else "-",
                    f"{row['avg_protein']:.1f} g" if pd.notna(row.get('avg_protein')) else "-",
                    f"{row['avg_carbs']:.1f} g" if pd.notna(row.get('avg_carbs')) else "-",
                ]
            }
            # Add sugar and sodium if available
            if pd.notna(row.get("avg_sugar")):
                nut_data["Nutrient"].append("Sugar")
                nut_data["Value"].append(f"{row['avg_sugar']:.1f} g")
            if pd.notna(row.get("avg_sodium")):
                nut_data["Nutrient"].append("Sodium")
                nut_data["Value"].append(f"{row['avg_sodium']:.3f} g")
            st.dataframe(pd.DataFrame(nut_data), hide_index=True, use_container_width=True)

        with detail_right:
            st.markdown(f'<p style="color:{_text1};font-weight:bold">Contact & Info</p>', unsafe_allow_html=True)
            addr = row.get("address") or ""
            if addr: st.markdown(f'<p style="color:{_text1}">📍 {addr}</p>', unsafe_allow_html=True)
            phone = row.get("phone")
            if phone and str(phone).strip(): st.markdown(f'<p style="color:{_text1}">📞 {phone}</p>', unsafe_allow_html=True)
            website = row.get("website")
            if website and str(website).strip(): st.markdown(f'<p style="color:{_text1}">🌐 <a href="{website}" style="color:{_accent}">{website}</a></p>', unsafe_allow_html=True)
            hours = row.get("opening_hours")
            if hours and str(hours).strip(): st.markdown(f'<p style="color:{_text1}">🕐 {hours}</p>', unsafe_allow_html=True)
            nbhd = row.get("neighborhood")
            if nbhd and str(nbhd).strip(): st.markdown(f'<p style="color:{_text1}">📌 {nbhd}</p>', unsafe_allow_html=True)

        if row.get("review_text") and str(row["review_text"]).strip():
            with st.expander("📝 Sample Reviews"):
                st.write(str(row["review_text"])[:600])

with tab2:
    st.markdown('<div class="dd-section">Restaurant Map</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        map_cuisine = st.selectbox("Filter cuisine", ["All cuisines"] + cuisines, key="map_c")
    with col_b:
        healthy_only = st.checkbox("Healthy only (Nutri-Score A or B)", key="map_h")

    map_df = filtered.copy()
    if map_cuisine != "All cuisines":
        map_df = map_df[map_df["cuisine_key"] == map_cuisine]
    if healthy_only:
        map_df = map_df[map_df["nutriscore"].isin(["a", "b"])]

    m = folium.Map(location=[NYU_LAT, NYU_LNG], zoom_start=15, tiles="CartoDB positron")
    folium.Marker(
        [NYU_LAT, NYU_LNG],
        tooltip="NYU / Washington Square Park",
        icon=folium.Icon(color="darkblue", icon="university", prefix="fa"),
    ).add_to(m)
    folium.Circle(
        [NYU_LAT, NYU_LNG], radius=SEARCH_RADIUS_M,
        color="#2d5a27", weight=1.5, fill=True,
        fill_color="#2d5a27", fill_opacity=0.04,
    ).add_to(m)

    n_added = 0
    for _, row in map_df.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lng"]):
            continue
        r = row.get("google_rating")
        dd = float(row["dd_score"]) if pd.notna(row.get("dd_score")) else 5.0
        conf = row.get("dd_confidence", "ok")
        color = ("#2d5a27" if dd >= 8.0 else "#5a8a4f" if dd >= 6.5 else "#c4854c" if dd >= 5.0 else "#c47832" if dd >= 3.5 else "#b84233")
        ns  = str(row.get("nutriscore") or "?").upper()
        cal = row.get("avg_cal")
        popup_html = (
            f"<b>{row['name']}</b><br>"
            f"🍴 {str(row.get('cuisine_key', '')).replace('_', ' ').title()}<br>"
            f"⭐ {f'{r:.1f}' if pd.notna(r) else 'Unrated'} &nbsp; {row.get('price_level') or '—'}<br>"
            f"🥗 Nutri-Score <b>{ns}</b>"
            + (f" · {int(cal)} kcal/100g" if pd.notna(cal) else "")
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=(9 if conf == "ok" else 6 if conf == "low" else 5), color="white", weight=1.5,
            fill=True, fill_color=color, fill_opacity=0.88,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=row["name"],
        ).add_to(m)
        n_added += 1

    st.markdown(f'<div style="display:flex;align-items:center;gap:16px;padding:12px 18px;background:#fff;border-radius:12px;border:1px solid #e8e6e1;margin-bottom:12px;font-family:Outfit,sans-serif;font-size:13px;flex-wrap:wrap;color:#1a1a1a"><b>DishDash Score</b><span><span style="background:#2d5a27;border-radius:50%;width:12px;height:12px;display:inline-block"></span> <b>8+</b> Excellent</span><span><span style="background:#5a8a4f;border-radius:50%;width:12px;height:12px;display:inline-block"></span> <b>6.5+</b> Great</span><span><span style="background:#c4854c;border-radius:50%;width:12px;height:12px;display:inline-block"></span> <b>5+</b> Decent</span><span><span style="background:#c47832;border-radius:50%;width:12px;height:12px;display:inline-block"></span> <b>3.5+</b> Below avg</span><span><span style="background:#b84233;border-radius:50%;width:12px;height:12px;display:inline-block"></span> <b>&lt;3.5</b> Poor</span><span style="color:#9a9a9a;margin-left:auto">{n_added} venues</span></div>', unsafe_allow_html=True)
    st_folium(m, width=None, height=520, returned_objects=[])


# ══════════════════════════════════════════════════════════════
# TAB 3 — Analytics Dashboard
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="dd-section">Analytics Dashboard</div>', unsafe_allow_html=True)

    # ── Top metrics ───────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="dd-metric"><div class="dd-metric-val">{len(df)}</div><div class="dd-metric-lbl">Total Venues</div></div>', unsafe_allow_html=True)
    with m2:
        avg = df["google_rating"].mean()
        st.markdown(f'<div class="dd-metric"><div class="dd-metric-val">{avg:.2f}</div><div class="dd-metric-lbl">Avg Rating</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="dd-metric"><div class="dd-metric-val">{df["cuisine_key"].nunique()}</div><div class="dd-metric-lbl">Cuisines</div></div>', unsafe_allow_html=True)
    with m4:
        pct = int(df["google_rating"].notna().mean() * 100)
        st.markdown(f'<div class="dd-metric"><div class="dd-metric-val">{pct}%</div><div class="dd-metric-lbl">Have Ratings</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.patch.set_facecolor("#141414" if _dark else "#fafaf8")
    fig.suptitle("DishDash Analytics — NYU Area", fontsize=15,
                 fontweight="bold", color=("#e8e8e8" if _dark else "#1a1a1a"), y=1.01)

    # 1. Rating histogram
    ax = axes[0, 0]
    rated = df["google_rating"].dropna()
    if len(rated):
        bins = [1, 2, 2.5, 3, 3.5, 4, 4.25, 4.5, 4.75, 5.01]
        cnts, edges = np.histogram(rated, bins=bins)
        clrs = ["#e74c3c" if e < 3.5 else ("#f39c12" if e < 4.0 else "#27ae60") for e in edges[:-1]]
        bars = ax.bar(range(len(cnts)), cnts, color=clrs, edgecolor="white")
        ax.set_xticks(range(len(cnts)))
        ax.set_xticklabels([f"{edges[i]:.2g}–{edges[i+1]:.2g}" for i in range(len(cnts))],
                           rotation=35, ha="right", fontsize=8)
        ax.axvline(np.searchsorted(edges[:-1], rated.mean()) - 0.5,
                   color="#2d5a27", ls="--", lw=1.5, label=f"Mean {rated.mean():.2f}")
        ax.legend(fontsize=8)
        for b, c in zip(bars, cnts):
            if c:
                ax.text(b.get_x() + b.get_width() / 2, c + 0.1, str(c),
                        ha="center", va="bottom", fontsize=8)
    ax.set_title("⭐ Rating Distribution", fontweight="bold", color=("#e8e8e8" if _dark else "#1a1a1a"))
    ax.set_ylabel("Restaurants")
    ax.set_facecolor("#1a1a1a" if _dark else "#f5f4f0")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    # 2. Cuisine pie
    ax = axes[0, 1]
    cc = df["cuisine_key"].value_counts().head(12)
    if len(cc):
        lbls = [c.replace("_", " ").title() for c in cc.index]
        expl = [0.05 if i == 0 else 0 for i in range(len(cc))]
        ws, ts, ats = ax.pie(
            cc.values, labels=lbls,
            autopct=lambda p: f"{p:.0f}%" if p > 5 else "",
            colors=PALETTE[:len(cc)], explode=expl, startangle=140,
            pctdistance=0.75, wedgeprops={"edgecolor": "white", "linewidth": 1.5},
        )
        for t in ts:  t.set_fontsize(8)
        for at in ats: at.set_fontsize(7); at.set_color("white"); at.set_fontweight("bold")
    ax.set_title("🍴 Cuisine Breakdown", fontweight="bold", color=("#e8e8e8" if _dark else "#1a1a1a"))

    # 3. Calories by cuisine
    ax = axes[1, 0]
    cdf = (df[df["avg_cal"].notna()].groupby("cuisine_key")["avg_cal"].mean()
           .sort_values().head(12))
    if len(cdf):
        ns_map = df.groupby("cuisine_key")["nutriscore"].first()
        clrs   = [NS_COLOR.get(str(ns_map.get(c, "")).lower(), "#aaa") for c in cdf.index]
        hbs = ax.barh([c.replace("_", " ").title() for c in cdf.index],
                      cdf.values, color=clrs, edgecolor="white")
        ax.axvline(cdf.values.mean(), color="#2d5a27", ls="--", lw=1.5)
        for b in hbs:
            ax.text(b.get_width() + 2, b.get_y() + b.get_height() / 2,
                    f"{int(b.get_width())}", va="center", fontsize=8)
        patches = [mpatches.Patch(color=v, label=f"Nutri-Score {k.upper()}")
                   for k, v in NS_COLOR.items()]
        ax.legend(handles=patches, fontsize=7, loc="lower right")
    ax.set_title("🔥 Avg Calories / 100g by Cuisine", fontweight="bold", color=("#e8e8e8" if _dark else "#1a1a1a"))
    ax.set_xlabel("kcal / 100g")
    ax.set_facecolor("#1a1a1a" if _dark else "#f5f4f0")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    # 4. Sentiment or Rating vs Price
    ax = axes[1, 1]
    has_sent = df["sentiment_label"].notna().sum() > 2
    if has_sent:
        sc = df["sentiment_label"].value_counts()
        sc_c = ["#27ae60" if l == "POSITIVE" else "#e74c3c" for l in sc.index]
        bs = ax.bar(sc.index, sc.values, color=sc_c, edgecolor="white", width=0.5)
        for b in bs:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.2,
                    str(int(b.get_height())), ha="center", fontweight="bold")
        ax.set_title(f"😊 Review Sentiment (n={sc.sum()})", fontweight="bold", color=("#e8e8e8" if _dark else "#1a1a1a"))
    else:
        sdf = df[df["google_rating"].notna() & df["price_level"].notna()].copy()
        pm  = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
        sdf = sdf[sdf["price_level"].isin(pm)]
        if len(sdf):
            sdf["pn"] = sdf["price_level"].map(pm)
            jit = np.random.uniform(-0.15, 0.15, len(sdf))
            sc2 = ["#0f3460" if r >= 4.5 else ("#f5a623" if r >= 4.0 else "#e94560")
                   for r in sdf["google_rating"]]
            ax.scatter(sdf["pn"] + jit, sdf["google_rating"],
                       c=sc2, alpha=0.72, s=55, edgecolors="white", lw=0.8)
            ax.set_xticks([1, 2, 3, 4])
            ax.set_xticklabels(["Cheap", "Mid", "Pricey", "Luxury"], fontsize=12)
            ax.set_ylim(2.5, 5.2)
        ax.set_title("💰 Rating vs Price Level", fontweight="bold", color=("#e8e8e8" if _dark else "#1a1a1a"))
        ax.set_xlabel("Price Level"); ax.set_ylabel("Google Rating")
    ax.set_facecolor("#1a1a1a" if _dark else "#f5f4f0")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    try:
        plt.tight_layout()
    except Exception:
        pass
    st.pyplot(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# TAB 4 — Natural-Language Recommender
# ══════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="dd-section">🤖 Natural-Language Recommender</div>',
                unsafe_allow_html=True)
    st.caption("Describe what you want in plain English and get personalised picks from the DishDash database.")

    examples = [
        "— Pick an example —",
        "I want something cheap and healthy near NYU",
        "Best rated sushi or Japanese food",
        "Late-night comfort food, not worried about calories",
        "Impressive upscale dinner, budget not a concern",
        "Vegetarian-friendly with a good Nutri-Score",
        "Quick cheap lunch under $10",
    ]
    example_sel = st.selectbox("Try an example", examples)
    default_q   = "" if example_sel == examples[0] else example_sel
    user_query  = st.text_area("Your query", value=default_q,
                               placeholder='e.g. "cheap healthy food near campus"',
                               height=80)

    if st.button("Get Recommendations", type="primary"):
        q = user_query.strip().lower()
        if not q:
            st.warning("Please enter a query above.")
        else:
            sc = df.copy()
            sc["_s"] = sc["google_rating"].fillna(3.5) * 2.0

            # Price
            if any(w in q for w in ["cheap", "budget", "affordable", "inexpensive", "$10"]):
                sc["_s"] += sc["price_level"].map({"$": 6, "$$": 3, "$$$": 1, "$$$$": 0}).fillna(0)
            if any(w in q for w in ["upscale", "fancy", "fine dining", "impress", "splurge", "special"]):
                sc["_s"] += sc["price_level"].map({"$$$$": 6, "$$$": 4, "$$": 1, "$": 0}).fillna(0)

            # Health
            if any(w in q for w in ["healthy", "health", "nutri", "light", "vegetarian", "vegan", "diet"]):
                sc["_s"] += sc["nutriscore"].map({"a": 6, "b": 4, "c": 2, "d": 0, "e": 0}).fillna(0)

            # Cuisine
            for ck in CUISINE_MAP:
                if ck.replace("_", " ") in q or ck in q:
                    sc["_s"] += (sc["cuisine_key"] == ck).astype(float) * 10
            for kw, ck in [("sushi", "sushi"), ("ramen", "japanese"), ("taco", "mexican"),
                            ("pasta", "italian"), ("falafel", "mediterranean"),
                            ("pho", "vietnamese"), ("noodle", "chinese"), ("burger", "burger")]:
                if kw in q:
                    sc["_s"] += (sc["cuisine_key"] == ck).astype(float) * 8

            top3 = sc.nlargest(3, "_s")
            st.markdown(f"*Query: \"{user_query.strip()}\"*")
            st.markdown("")

            for _, row in top3.iterrows():
                r   = row.get("google_rating")
                ns  = str(row.get("nutriscore") or "?").upper()
                bg  = NS_COLOR.get(ns.lower(), "#aaa")
                cal = row.get("avg_cal")
                cuis = str(row.get("cuisine_key", "")).replace("_", " ").title()
                price = row.get("price_level") or ""
                r_str = f"{r:.1f} ⭐" if pd.notna(r) else "Unrated"
                cal_s = f"{int(cal)} kcal/100g" if pd.notna(cal) else ""

                why = []
                if pd.notna(r) and r >= 4.5:   why.append("highly rated")
                if price == "$":                why.append("budget-friendly")
                if price == "$$$$":             why.append("upscale experience")
                if ns.lower() in ("a", "b"):    why.append(f"healthy (Nutri-Score {ns})")
                if ns.lower() in ("d", "e"):    why.append("indulgent comfort food")
                why_s = ", ".join(why) if why else "good all-round pick"

                st.markdown(
                    f'<div class="dd-card" style="border-left:5px solid {bg}">'
                    f'<div class="dd-card-left">'
                    f'<div class="dd-card-name">{row["name"]}</div>'
                    f'<span class="dd-cuisine-tag">{cuis}</span>'
                    f'<div class="dd-detail" style="margin-top:7px">'
                    f'{r_str} &nbsp; {price} &nbsp; '
                    f'<span class="dd-ns-badge" style="background:{bg}">{ns}</span>{cal_s}'
                    f'</div>'
                    f'<div class="dd-detail" style="font-style:italic;color:#555">Why: {why_s}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
