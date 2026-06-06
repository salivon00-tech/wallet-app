import streamlit as st
import json, os, uuid
from datetime import datetime, date
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WalletUA — Сімейний бюджет",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
USD = 44.38
EUR = 51.67
DATA_FILE = "wallet_data.json"
MONTHS_UA = ["Січень","Лютий","Березень","Квітень","Травень","Червень",
             "Липень","Серпень","Вересень","Жовтень","Листопад","Грудень"]
SHORT_UA  = ["Січ","Лют","Бер","Кві","Тра","Чер","Лип","Сер","Вер","Жов","Лис","Гру"]

USERS = {
    "family": {"name": "👨‍👩‍👧 Сім'я",   "color": "#7B61FF"},
    "me":     {"name": "👤 Я",         "color": "#00D084"},
    "wife":   {"name": "👩 Дружина",   "color": "#ec4899"},
}

INC_CATS = [
    {"id":"salary",   "label":"Зарплата",           "icon":"💼", "color":"#00D084"},
    {"id":"housing",  "label":"Компенсація найму",   "icon":"🏠", "color":"#00b872"},
    {"id":"parents",  "label":"Допомога батьків",    "icon":"👨‍👩‍👧","color":"#34d399"},
    {"id":"rental",   "label":"Дохід від оренди",    "icon":"🏢", "color":"#059669"},
    {"id":"divid",    "label":"Дивіденди",           "icon":"📈", "color":"#10b981"},
    {"id":"freelance","label":"Фріланс",             "icon":"💻", "color":"#6ee7b7"},
    {"id":"cashback", "label":"Кешбек",              "icon":"🎁", "color":"#a7f3d0"},
    {"id":"other_i",  "label":"Інші доходи",         "icon":"➕", "color":"#6b7280"},
]
EXP_CATS = [
    {"id":"rent",     "label":"Оренда",             "icon":"🏠", "color":"#FF4757", "budget":13314},
    {"id":"mortgage", "label":"Іпотека",            "icon":"🏦", "color":"#ff6b81", "budget":8000},
    {"id":"utils",    "label":"Комуналка",          "icon":"💡", "color":"#ffa502", "budget":2000},
    {"id":"food",     "label":"Продукти",           "icon":"🛒", "color":"#84cc16", "budget":5000},
    {"id":"cafe",     "label":"Кафе / Ресторани",   "icon":"☕", "color":"#22c55e", "budget":1500},
    {"id":"child",    "label":"Дитяче",             "icon":"👶", "color":"#06b6d4", "budget":2000},
    {"id":"fuel",     "label":"Пальне",             "icon":"⛽", "color":"#3b82f6", "budget":2000},
    {"id":"car",      "label":"Ремонт авто",        "icon":"🔧", "color":"#6366f1", "budget":1000},
    {"id":"mobile",   "label":"Мобільний зв'язок",  "icon":"📞", "color":"#a855f7", "budget":850},
    {"id":"subs",     "label":"Підписки",           "icon":"📱", "color":"#8b5cf6", "budget":1641},
    {"id":"cigs",     "label":"Цигарки",            "icon":"🚬", "color":"#ec4899", "budget":4800},
    {"id":"clothes",  "label":"Одяг",               "icon":"👕", "color":"#f43f5e", "budget":1000},
    {"id":"health",   "label":"Здоров'я",           "icon":"💊", "color":"#14b8a6", "budget":500},
    {"id":"entertain","label":"Розваги",            "icon":"🎮", "color":"#f59e0b", "budget":500},
    {"id":"edu",      "label":"Освіта",             "icon":"📚", "color":"#0ea5e9", "budget":0},
    {"id":"gifts",    "label":"Подарунки",          "icon":"🎀", "color":"#e879f9", "budget":0},
    {"id":"travel",   "label":"Подорожі",           "icon":"✈️", "color":"#38bdf8", "budget":0},
    {"id":"other_e",  "label":"Інше",               "icon":"💸", "color":"#6b7280", "budget":1000},
]
ALL_CATS = INC_CATS + EXP_CATS
CAT_MAP  = {c["id"]: c for c in ALL_CATS}

INSTRUMENTS = [
    {"id":"inzhur_reit",   "label":"Inzhur REIT",          "icon":"🏪","color":"#7B61FF","rate":9.5},
    {"id":"inzhur_energy", "label":"Inzhur Energy",        "icon":"⚡","color":"#ffa502","rate":15.0},
    {"id":"binance_flex",  "label":"Binance Earn Flexible", "icon":"🟡","color":"#f0b90b","rate":6.0},
    {"id":"mono_jar",      "label":"Monobank Скарбничка",   "icon":"🐱","color":"#34d399","rate":13.0},
    {"id":"ovdp",          "label":"ОВДП",                 "icon":"📜","color":"#60a5fa","rate":17.0},
    {"id":"other_sav",     "label":"Інше",                 "icon":"💼","color":"#6b7280","rate":0.0},
]
INSTR_MAP = {i["id"]: i for i in INSTRUMENTS}

# ── HELPERS ───────────────────────────────────────────────────────────────────
def to_uah(amount, cur):
    if cur == "$": return amount * USD
    if cur == "€": return amount * EUR
    return amount

def fmt(n, cur="₴"):
    n = abs(float(n))
    s = f"{n:,.0f}".replace(",", " ")
    if cur == "$": return f"${s}"
    if cur == "€": return f"€{s}"
    return f"{s} ₴"

def uid(): return str(uuid.uuid4())[:8]

def cat_label(cat_id):
    c = CAT_MAP.get(cat_id, {})
    return f"{c.get('icon','❓')} {c.get('label', cat_id)}"

# ── DATA ──────────────────────────────────────────────────────────────────────
CY, CM = datetime.now().year, datetime.now().month - 1  # 0-indexed month
mk = f"{CY}-{str(CM+1).padStart(2,'0') if hasattr(str(CM+1),'padStart') else str(CM+1).zfill(2)}"
TODAY = date.today().isoformat()
THIS_MONTH = f"{CY}-{str(CM+1).zfill(2)}"

def default_data():
    return {
        "accounts": [
            {"id": uid(), "name": "Monobank",    "type": "card",   "currency": "₴", "balance": 4200,  "icon": "🐱", "note": "Чорна картка", "user": "me"},
            {"id": uid(), "name": "ПриватБанк",  "type": "card",   "currency": "₴", "balance": 1850,  "icon": "🏦", "note": "",              "user": "wife"},
            {"id": uid(), "name": "Готівка",      "type": "cash",   "currency": "₴", "balance": 3500,  "icon": "💵", "note": "",              "user": "family"},
            {"id": uid(), "name": "Binance",      "type": "crypto", "currency": "$", "balance": 68,    "icon": "🟡", "note": "Earn Flexible", "user": "me"},
        ],
        "transactions": [
            {"id": uid(), "type": "income",  "cat": "salary",  "amount": 35000, "currency": "₴", "note": "Зарплата",          "date": f"{CY}-{str(CM+1).zfill(2)}-01", "user": "me"},
            {"id": uid(), "type": "income",  "cat": "housing", "amount": 2300,  "currency": "₴", "note": "Компенсація найму", "date": f"{CY}-{str(CM+1).zfill(2)}-01", "user": "me"},
            {"id": uid(), "type": "income",  "cat": "parents", "amount": 100,   "currency": "$", "note": "Батьки",            "date": f"{CY}-{str(CM+1).zfill(2)}-02", "user": "family"},
            {"id": uid(), "type": "expense", "cat": "rent",    "amount": 300,   "currency": "$", "note": "Оренда",            "date": f"{CY}-{str(CM+1).zfill(2)}-03", "user": "family"},
            {"id": uid(), "type": "expense", "cat": "utils",   "amount": 1800,  "currency": "₴", "note": "Комуналка",         "date": f"{CY}-{str(CM+1).zfill(2)}-05", "user": "family"},
            {"id": uid(), "type": "expense", "cat": "mobile",  "amount": 850,   "currency": "₴", "note": "Київстар ×2",       "date": f"{CY}-{str(CM+1).zfill(2)}-05", "user": "family"},
            {"id": uid(), "type": "expense", "cat": "subs",    "amount": 1641,  "currency": "₴", "note": "Netflix+YT+iCloud", "date": f"{CY}-{str(CM+1).zfill(2)}-05", "user": "family"},
            {"id": uid(), "type": "expense", "cat": "food",    "amount": 3800,  "currency": "₴", "note": "Сільпо",            "date": f"{CY}-{str(CM+1).zfill(2)}-10", "user": "wife"},
            {"id": uid(), "type": "expense", "cat": "cigs",    "amount": 4800,  "currency": "₴", "note": "Цигарки",           "date": f"{CY}-{str(CM+1).zfill(2)}-15", "user": "me"},
            {"id": uid(), "type": "expense", "cat": "child",   "amount": 1500,  "currency": "₴", "note": "Дитяче",            "date": f"{CY}-{str(CM+1).zfill(2)}-12", "user": "wife"},
            {"id": uid(), "type": "expense", "cat": "fuel",    "amount": 1800,  "currency": "₴", "note": "Пальне Audi",       "date": f"{CY}-{str(CM+1).zfill(2)}-14", "user": "me"},
            {"id": uid(), "type": "expense", "cat": "cafe",    "amount": 680,   "currency": "₴", "note": "Кав'ярня",          "date": f"{CY}-{str(CM+1).zfill(2)}-18", "user": "wife"},
            # Prev month
            {"id": uid(), "type": "income",  "cat": "salary",  "amount": 35000, "currency": "₴", "note": "Зарплата",  "date": f"{CY}-{str(CM).zfill(2) if CM>0 else '05'}-01", "user": "me"},
            {"id": uid(), "type": "expense", "cat": "cigs",    "amount": 4800,  "currency": "₴", "note": "Цигарки",   "date": f"{CY}-{str(CM).zfill(2) if CM>0 else '05'}-15", "user": "me"},
            {"id": uid(), "type": "expense", "cat": "food",    "amount": 4200,  "currency": "₴", "note": "Продукти",  "date": f"{CY}-{str(CM).zfill(2) if CM>0 else '05'}-10", "user": "wife"},
            {"id": uid(), "type": "expense", "cat": "car",     "amount": 3200,  "currency": "₴", "note": "Ремонт Audi","date":f"{CY}-{str(CM).zfill(2) if CM>0 else '05'}-20", "user": "me"},
            {"id": uid(), "type": "expense", "cat": "rent",    "amount": 300,   "currency": "$", "note": "Оренда",    "date": f"{CY}-{str(CM).zfill(2) if CM>0 else '05'}-03", "user": "family"},
        ],
        "debts": [
            {"id": uid(), "dir": "owe",  "label": "Кредитна картка", "amount": 12260, "currency": "₴", "paid": 0, "due": "", "note": "Monobank кредитка",   "user": "me"},
            {"id": uid(), "dir": "owe",  "label": "Іпотека єОселя",  "amount": 8000,  "currency": "₴", "paid": 0, "due": "", "note": "Щомісячний платіж",   "user": "family"},
            {"id": uid(), "dir": "owed", "label": "Весільні кошти",  "amount": 2000,  "currency": "$", "paid": 0, "due": "", "note": "Повернути в спільний фонд", "user": "me"},
        ],
        "savings": [
            {"id": uid(), "instrument": "inzhur_reit",  "amount": 2150, "currency": "₴", "date": f"{CY}-01-01", "note": "Початкова позиція", "user": "me"},
            {"id": uid(), "instrument": "binance_flex", "amount": 68,   "currency": "$", "date": f"{CY}-03-01", "note": "Earn USDT",         "user": "me"},
        ],
        "goals": [
            {"id": "credit",  "label": "Закрити кредитку",  "target": 12260, "currency": "₴", "icon": "💳", "color": "#FF4757", "deadline": "2026-07-01", "saved": 0},
            {"id": "cashpad", "label": "Швидка каса",        "target": 20000, "currency": "₴", "icon": "🚨", "color": "#ffa502", "deadline": "2026-12-01", "saved": 0},
            {"id": "wedding", "label": "Весільні кошти",     "target": 2000,  "currency": "$", "icon": "💍", "color": "#8b5cf6", "deadline": "2027-06-01", "saved": 0},
            {"id": "cushion", "label": "Подушка сім'ї",      "target": 1500,  "currency": "$", "icon": "🛡️", "color": "#3b82f6", "deadline": "2027-09-01", "saved": 0},
            {"id": "repair",  "label": "Ремонт квартири",    "target": 3000,  "currency": "$", "icon": "🏠", "color": "#00D084", "deadline": "2028-12-01", "saved": 0},
        ],
        "budgets": {c["id"]: c["budget"] for c in EXP_CATS},
        "budget_month": THIS_MONTH,
        "roadmap": [
            {"id": uid(), "month": 1,  "icon": "💳", "text": "Закрити кредитку 12 260 ₴ одним платежем"},
            {"id": uid(), "month": 2,  "icon": "🚀", "text": "Старт: 7 400 ₴ → Binance (весільні), 4 400 ₴ → Inzhur REIT, 3 200 ₴ → Mono"},
            {"id": uid(), "month": 6,  "icon": "🚨", "text": "Швидка каса 20 000 ₴ набрана"},
            {"id": uid(), "month": 12, "icon": "💍", "text": "Весільні 2 000$ повернуті на Binance Flexible"},
            {"id": uid(), "month": 14, "icon": "🏗️", "text": "Старт: 8 000 ₴/міс ремонт + 4 000 ₴ → Inzhur Energy"},
            {"id": uid(), "month": 15, "icon": "🛡️", "text": "Подушка сім'ї 1 500$ в Inzhur REIT"},
            {"id": uid(), "month": 30, "icon": "🏠", "text": "Косметичний ремонт готовий, квартира здається в оренду"},
        ],
    }

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default_data()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Unbounded:wght@600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #06060f;
        color: #f0efff;
    }
    .stApp { background-color: #06060f; }
    .main .block-container { padding: 1.5rem 2rem 3rem; max-width: 1200px; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0d0d1c;
        border-right: 1px solid #1e1e3a;
    }
    [data-testid="stSidebar"] .stMarkdown p { color: #9896c8; }

    /* Metrics */
    [data-testid="stMetric"] {
        background: #0f0f1c;
        border: 1px solid #1e1e3a;
        border-radius: 14px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] { color: #6b6b90 !important; font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
    [data-testid="stMetricValue"] { font-family: 'Unbounded', sans-serif; font-size: 24px; color: #f0efff; }
    [data-testid="stMetricDelta"] { font-size: 12px; }

    /* Buttons */
    .stButton > button {
        background: #7B61FF;
        color: #fff;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        font-size: 13px;
        padding: 10px 20px;
        transition: all .2s;
    }
    .stButton > button:hover { background: #8a73ff; box-shadow: 0 4px 20px #7B61FF44; }

    /* Selectbox, input */
    .stSelectbox > div > div, .stTextInput > div > div > input,
    .stNumberInput > div > div > input, .stDateInput > div > div > input {
        background: #131327 !important;
        border: 1px solid #1e1e3a !important;
        border-radius: 10px !important;
        color: #f0efff !important;
    }
    .stTextArea > div > div > textarea {
        background: #131327 !important;
        border: 1px solid #1e1e3a !important;
        color: #f0efff !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #0d0d1c;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #1e1e3a;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 9px;
        color: #6b6b90;
        font-weight: 600;
        font-size: 13px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #7B61FF !important;
        color: #fff !important;
    }

    /* Dataframe */
    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid #1e1e3a; }
    iframe { background: #0f0f1c; }

    /* Cards */
    .wallet-card {
        background: #0f0f1c;
        border: 1px solid #1e1e3a;
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 12px;
    }
    .wallet-card-hero {
        background: linear-gradient(135deg, #0f0a2e, #1a1050, #0a0a1e);
        border: 1px solid #7B61FF33;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 16px;
    }
    .user-badge-me     { background: #00D08418; border: 1px solid #00D08444; border-radius: 99px; padding: 3px 10px; color: #00D084; font-size: 12px; font-weight: 600; display: inline-block; }
    .user-badge-wife   { background: #ec489918; border: 1px solid #ec489944; border-radius: 99px; padding: 3px 10px; color: #ec4899; font-size: 12px; font-weight: 600; display: inline-block; }
    .user-badge-family { background: #7B61FF18; border: 1px solid #7B61FF44; border-radius: 99px; padding: 3px 10px; color: #a78bfa; font-size: 12px; font-weight: 600; display: inline-block; }
    .inc-badge  { color: #00D084; font-weight: 700; }
    .exp-badge  { color: #FF4757; font-weight: 700; }
    .h1-title   { font-family: 'Unbounded', sans-serif; font-size: 28px; font-weight: 800; letter-spacing: -.02em; }
    .section-label { font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: #4a4880; margin-bottom: 8px; }
    div[data-testid="stExpander"] {
        background: #0f0f1c;
        border: 1px solid #1e1e3a;
        border-radius: 12px;
    }
    .stProgress > div > div { background: #7B61FF; border-radius: 99px; }
    .stProgress { border-radius: 99px; }
    hr { border-color: #1e1e3a; }
    </style>
    """, unsafe_allow_html=True)

# ── CHART THEME ───────────────────────────────────────────────────────────────
PLOT_BG   = "#0f0f1c"
PAPER_BG  = "#06060f"
GRID_CLR  = "#1e1e3a"
TEXT_CLR  = "#6b6b90"
FONT_FAM  = "Inter"

def chart_layout(fig, title="", height=280):
    fig.update_layout(
        title=title,
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(family=FONT_FAM, color=TEXT_CLR, size=11),
        margin=dict(l=10, r=10, t=30 if title else 10, b=10),
        height=height,
        showlegend=True,
        legend=dict(font=dict(color="#9896c8"), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, linecolor=GRID_CLR),
        yaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, linecolor=GRID_CLR),
    )
    return fig

# ── FILTER TX ─────────────────────────────────────────────────────────────────
def filter_tx(data, user_filter, month=None, tx_type=None):
    txs = data["transactions"]
    if user_filter != "family":
        txs = [t for t in txs if t["user"] in (user_filter, "family")]
    if month:
        txs = [t for t in txs if t["date"].startswith(month)]
    if tx_type:
        txs = [t for t in txs if t["type"] == tx_type]
    return txs

def month_stats(data, user_filter, month):
    txs = filter_tx(data, user_filter, month)
    inc = sum(to_uah(t["amount"], t["currency"]) for t in txs if t["type"] == "income")
    exp = sum(to_uah(t["amount"], t["currency"]) for t in txs if t["type"] == "expense")
    return inc, exp

# ── PAGE: DASHBOARD ───────────────────────────────────────────────────────────
def page_dashboard(data, user_filter):
    st.markdown(f'<div class="h1-title">⚡ Головна</div>', unsafe_allow_html=True)
    st.markdown(f"<div style='color:#6b6b90;font-size:13px;margin-bottom:20px'>1$ = {USD} ₴ · 1€ = {EUR} ₴ · {MONTHS_UA[CM]} {CY}</div>", unsafe_allow_html=True)

    # Accounts total
    accs = data["accounts"]
    if user_filter != "family":
        accs = [a for a in accs if a["user"] in (user_filter, "family")]
    net_worth = sum(to_uah(a["balance"], a["currency"]) for a in accs)

    # This month stats
    inc, exp = month_stats(data, user_filter, THIS_MONTH)
    net = inc - exp
    sav_rate = round((net / inc * 100)) if inc > 0 else 0

    # Total savings
    savs = data["savings"]
    if user_filter != "family":
        savs = [s for s in savs if s.get("user","family") in (user_filter,"family")]
    total_sav_uah = sum(to_uah(s["amount"], s["currency"]) for s in savs)

    # Hero
    st.markdown(f"""
    <div class="wallet-card-hero">
        <div class="section-label">Загальний капітал</div>
        <div class="h1-title" style="font-size:36px;color:#f0efff;margin:8px 0 4px">{fmt(net_worth)}</div>
        <div style="color:#6b6b90;font-size:13px">≈ ${round(net_worth/USD):,} USD</div>
        <div style="display:flex;gap:32px;margin-top:20px">
            <div>
                <div style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px">Доходи/міс</div>
                <div style="font-size:18px;font-weight:700;color:#00D084">{fmt(inc, short=True) if hasattr(fmt,'short') else fmt(inc)}</div>
            </div>
            <div>
                <div style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px">Витрати/міс</div>
                <div style="font-size:18px;font-weight:700;color:#FF4757">{fmt(exp)}</div>
            </div>
            <div>
                <div style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px">Заощадження</div>
                <div style="font-size:18px;font-weight:700;color:#7B61FF">≈${round(total_sav_uah/USD):,}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    sav_color = "normal" if sav_rate >= 20 else "inverse"
    c1.metric("💰 Дохід цього місяця", fmt(inc), f"+{sav_rate}% норма заощаджень")
    c2.metric("💸 Витрати", fmt(exp), f"{fmt(net)} залишок", delta_color="inverse" if net < 0 else "normal")
    c3.metric("📈 Інвестиції", f"${round(total_sav_uah/USD):,}", f"{len(savs)} позицій")
    total_debt = sum(to_uah(d["amount"]-d["paid"], d["currency"]) for d in data["debts"] if d["dir"]=="owe")
    c4.metric("🔴 Борги", fmt(total_debt), "треба погасити", delta_color="inverse")

    st.markdown("---")

    # Charts row
    col_l, col_r = st.columns([3, 2])

    with col_l:
        # Last 6 months bar chart
        months_data = []
        for i in range(5, -1, -1):
            mo = CM - i
            yr = CY
            if mo < 0: mo += 12; yr -= 1
            mk = f"{yr}-{str(mo+1).zfill(2)}"
            mi, me = month_stats(data, user_filter, mk)
            months_data.append({"month": SHORT_UA[mo], "Доходи": round(mi/1000,1), "Витрати": round(me/1000,1)})

        df = pd.DataFrame(months_data)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Доходи",  x=df["month"], y=df["Доходи"],  marker_color="#00D08488", marker_cornerradius=4))
        fig.add_trace(go.Bar(name="Витрати", x=df["month"], y=df["Витрати"], marker_color="#FF475788", marker_cornerradius=4))
        fig = chart_layout(fig, "Доходи vs Витрати (тис. ₴)", 260)
        fig.update_layout(barmode="group", bargap=0.2)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # Expense pie this month
        txs = filter_tx(data, user_filter, THIS_MONTH, "expense")
        by_cat = {}
        for t in txs:
            by_cat[t["cat"]] = by_cat.get(t["cat"], 0) + to_uah(t["amount"], t["currency"])

        if by_cat:
            labels = [cat_label(k) for k in by_cat]
            values = list(by_cat.values())
            colors = [CAT_MAP.get(k, {}).get("color", "#888") for k in by_cat]
            fig2 = go.Figure(go.Pie(
                labels=labels, values=values,
                hole=0.55, marker_colors=colors,
                textinfo="percent", textfont_size=11,
                hovertemplate="%{label}: %{value:,.0f} ₴<extra></extra>",
            ))
            chart_layout(fig2, "Структура витрат", 260)
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Немає витрат цього місяця")

    # Top expenses + recent transactions
    col_tl, col_tr = st.columns(2)

    with col_tl:
        st.markdown('<div class="section-label">Топ витрат</div>', unsafe_allow_html=True)
        top = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:5] if by_cat else []
        for cat_id, val in top:
            c = CAT_MAP.get(cat_id, {})
            pct = int(val / top[0][1] * 100) if top else 0
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
                <span style="font-size:20px">{c.get('icon','❓')}</span>
                <div style="flex:1">
                    <div style="font-size:13px;font-weight:500;margin-bottom:3px">{c.get('label',cat_id)}</div>
                    <div style="background:#1e1e3a;border-radius:99px;height:4px;overflow:hidden">
                        <div style="width:{pct}%;height:100%;background:{c.get('color','#888')};border-radius:99px"></div>
                    </div>
                </div>
                <span style="font-size:13px;color:#9896c8;font-weight:600;white-space:nowrap">{fmt(val)}</span>
            </div>
            """, unsafe_allow_html=True)

    with col_tr:
        st.markdown('<div class="section-label">Останні операції</div>', unsafe_allow_html=True)
        recent = sorted(filter_tx(data, user_filter), key=lambda x: x["date"], reverse=True)[:6]
        for t in recent:
            c = CAT_MAP.get(t["cat"], {})
            user_c = USERS.get(t.get("user","family"), {}).get("color","#888")
            color = "#00D084" if t["type"] == "income" else "#FF4757"
            sign  = "+" if t["type"] == "income" else "−"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
                <div style="width:36px;height:36px;border-radius:10px;background:{c.get('color','#888')}22;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0">{c.get('icon','❓')}</div>
                <div style="flex:1">
                    <div style="font-size:13px;font-weight:500">{c.get('label',t['cat'])}</div>
                    <div style="font-size:11px;color:#6b6b90">{t['date']} · <span style="color:{user_c}">{USERS.get(t.get('user','family'),{}).get('name','')}</span></div>
                </div>
                <span style="font-weight:700;font-size:14px;color:{color}">{sign}{t['amount']}{t['currency']}</span>
            </div>
            """, unsafe_allow_html=True)

    # Goals quick view
    st.markdown("---")
    st.markdown('<div class="section-label">Фінансові цілі</div>', unsafe_allow_html=True)
    goal_cols = st.columns(len(data["goals"]))
    for i, g in enumerate(data["goals"]):
        pct = min(100, round(g["saved"] / g["target"] * 100)) if g["target"] > 0 else 0
        with goal_cols[i]:
            st.markdown(f"""
            <div class="wallet-card" style="text-align:center;border-color:{g['color']}33">
                <div style="font-size:24px;margin-bottom:6px">{g['icon']}</div>
                <div style="font-size:12px;font-weight:600;margin-bottom:4px">{g['label']}</div>
                <div style="font-family:'Unbounded',sans-serif;font-size:22px;font-weight:800;color:{g['color']}">{pct}%</div>
                <div style="background:#1e1e3a;border-radius:99px;height:5px;overflow:hidden;margin-top:8px">
                    <div style="width:{pct}%;height:100%;background:{g['color']};border-radius:99px"></div>
                </div>
                <div style="font-size:11px;color:#6b6b90;margin-top:6px">{fmt(g['saved'],g['currency'])} / {fmt(g['target'],g['currency'])}</div>
            </div>
            """, unsafe_allow_html=True)

# ── PAGE: TRANSACTIONS ────────────────────────────────────────────────────────
def page_transactions(data, user_filter):
    st.markdown('<div class="h1-title">📋 Операції</div>', unsafe_allow_html=True)

    # Add transaction form
    with st.expander("➕ Додати операцію", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            tx_type = st.selectbox("Тип", ["expense", "income"], format_func=lambda x: "💸 Витрата" if x == "expense" else "💰 Дохід", key="new_tx_type")
            cats = EXP_CATS if tx_type == "expense" else INC_CATS
            cat_options = {c["id"]: f"{c['icon']} {c['label']}" for c in cats}
            cat_id = st.selectbox("Категорія", list(cat_options.keys()), format_func=lambda x: cat_options[x], key="new_tx_cat")
            amount = st.number_input("Сума", min_value=0.0, step=100.0, key="new_tx_amount")
            currency = st.selectbox("Валюта", ["₴", "$", "€"], key="new_tx_cur")
        with col2:
            user_opt = st.selectbox("Хто", list(USERS.keys()), format_func=lambda x: USERS[x]["name"], key="new_tx_user")
            tx_date  = st.date_input("Дата", value=date.today(), key="new_tx_date")
            note     = st.text_input("Примітка", key="new_tx_note")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Зберегти операцію", use_container_width=True):
                if amount > 0:
                    data["transactions"].append({
                        "id": uid(), "type": tx_type, "cat": cat_id,
                        "amount": amount, "currency": currency,
                        "note": note, "date": tx_date.isoformat(), "user": user_opt,
                    })
                    save_data(data)
                    st.success("Операцію додано!")
                    st.rerun()

    st.markdown("---")

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        f_type = st.selectbox("Фільтр за типом", ["all","income","expense"], format_func=lambda x: {"all":"Всі","income":"💰 Доходи","expense":"💸 Витрати"}[x], key="f_type")
    with col_f2:
        f_month = st.text_input("Місяць (РРРР-ММ)", value=THIS_MONTH, key="f_month")
    with col_f3:
        f_search = st.text_input("🔍 Пошук по примітці", key="f_search")

    txs = filter_tx(data, user_filter)
    if f_type != "all":  txs = [t for t in txs if t["type"] == f_type]
    if f_month:          txs = [t for t in txs if t["date"].startswith(f_month)]
    if f_search:         txs = [t for t in txs if f_search.lower() in (t.get("note","")).lower()]
    txs = sorted(txs, key=lambda x: x["date"], reverse=True)

    if not txs:
        st.info("Немає операцій за вибраним фільтром")
        return

    # Build display df
    rows = []
    for t in txs:
        c = CAT_MAP.get(t["cat"], {})
        rows.append({
            "Дата":       t["date"],
            "Тип":        "💰 Дохід" if t["type"]=="income" else "💸 Витрата",
            "Категорія":  f"{c.get('icon','❓')} {c.get('label',t['cat'])}",
            "Сума":       f"{'+'if t['type']=='income' else '−'}{t['amount']}{t['currency']}",
            "₴ еквів.":  f"{fmt(to_uah(t['amount'],t['currency']))}",
            "Хто":        USERS.get(t.get("user","family"),{}).get("name",""),
            "Примітка":   t.get("note",""),
            "_id":        t["id"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df.drop(columns=["_id"]),
        use_container_width=True,
        height=400,
        hide_index=True,
    )

    # Delete
    st.markdown("---")
    del_ids = [t["id"] for t in txs]
    del_labels = [f"{t['date']} · {cat_label(t['cat'])} · {t['amount']}{t['currency']}" for t in txs]
    col_d1, col_d2 = st.columns([3,1])
    with col_d1:
        del_sel = st.selectbox("Видалити операцію", del_ids, format_func=lambda x: del_labels[del_ids.index(x)], key="del_tx_sel")
    with col_d2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Видалити", key="del_tx_btn"):
            data["transactions"] = [t for t in data["transactions"] if t["id"] != del_sel]
            save_data(data)
            st.success("Видалено")
            st.rerun()

# ── PAGE: ACCOUNTS ────────────────────────────────────────────────────────────
def page_accounts(data, user_filter):
    st.markdown('<div class="h1-title">💳 Рахунки</div>', unsafe_allow_html=True)

    accs = data["accounts"]
    if user_filter != "family":
        accs = [a for a in accs if a["user"] in (user_filter,"family")]

    net = sum(to_uah(a["balance"],a["currency"]) for a in accs)
    st.markdown(f"""
    <div class="wallet-card-hero" style="text-align:center">
        <div class="section-label">Загальний баланс</div>
        <div class="h1-title" style="font-size:38px">{fmt(net)}</div>
        <div style="color:#6b6b90;font-size:14px;margin-top:6px">≈ ${round(net/USD):,} USD · €{round(net/EUR):,} EUR</div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(accs) if accs else 1)
    GRAD = {"card":"#1a1a40,#2d1f6e","cash":"#0d2818,#1a5c30","crypto":"#2a1f00,#5a3d00","savings":"#0d1a2e,#1a3a5c"}
    for i, a in enumerate(accs):
        g = GRAD.get(a["type"], GRAD["card"])
        with cols[i]:
            uah_eq = f"<div style='font-size:12px;color:#ffffff66;margin-bottom:8px'>≈ {fmt(to_uah(a['balance'],a['currency']))}</div>" if a["currency"]!="₴" else ""
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{g});border:1px solid #ffffff18;border-radius:18px;padding:20px;position:relative;overflow:hidden">
                <div style="position:absolute;top:-20px;right:-20px;width:80px;height:80px;border-radius:50%;background:#ffffff06"></div>
                <div style="font-size:28px;margin-bottom:16px">{a['icon']}</div>
                <div style="font-family:'Unbounded',sans-serif;font-size:20px;font-weight:800;margin-bottom:4px">{a['balance']:,.0f} {a['currency']}</div>
                {uah_eq}
                <div style="font-size:14px;color:#ffffffaa;font-weight:600">{a['name']}</div>
                <div style="font-size:11px;color:#ffffff55;margin-top:2px">{a.get('note','')}</div>
                <div style="margin-top:10px"><span class="user-badge-{a.get('user','family')}">{USERS.get(a.get('user','family'),{}).get('name','')}</span></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("➕ Додати / Редагувати рахунок"):
        c1, c2 = st.columns(2)
        with c1:
            acc_name = st.text_input("Назва рахунку", key="acc_name")
            acc_type = st.selectbox("Тип", ["card","cash","crypto","savings"],
                                    format_func=lambda x:{"card":"💳 Картка","cash":"💵 Готівка","crypto":"🔐 Крипто","savings":"🏦 Депозит"}[x], key="acc_type")
            acc_icon = st.text_input("Іконка (емодзі)", value="💳", key="acc_icon")
        with c2:
            acc_bal  = st.number_input("Баланс", step=100.0, key="acc_bal")
            acc_cur  = st.selectbox("Валюта", ["₴","$","€"], key="acc_cur")
            acc_user = st.selectbox("Власник", list(USERS.keys()), format_func=lambda x: USERS[x]["name"], key="acc_user")
            acc_note = st.text_input("Примітка", key="acc_note")
        if st.button("💾 Зберегти рахунок"):
            if acc_name:
                data["accounts"].append({"id":uid(),"name":acc_name,"type":acc_type,"currency":acc_cur,"balance":acc_bal,"icon":acc_icon,"note":acc_note,"user":acc_user})
                save_data(data)
                st.success("Рахунок додано!"); st.rerun()

# ── PAGE: BUDGET ──────────────────────────────────────────────────────────────
def page_budget(data, user_filter):
    st.markdown('<div class="h1-title">📊 Бюджет</div>', unsafe_allow_html=True)

    bm = st.text_input("Місяць (РРРР-ММ)", value=THIS_MONTH, key="bm")
    txs = filter_tx(data, user_filter, bm, "expense")
    spent = {}
    for t in txs:
        spent[t["cat"]] = spent.get(t["cat"], 0) + to_uah(t["amount"], t["currency"])

    budgets = data.get("budgets", {c["id"]: c["budget"] for c in EXP_CATS})
    total_b = sum(budgets.values())
    total_s = sum(spent.values())
    over_cats = [c for c in EXP_CATS if spent.get(c["id"],0) > budgets.get(c["id"],0) > 0]

    c1, c2, c3 = st.columns(3)
    c1.metric("💸 Витрачено", fmt(total_s), f"з {fmt(total_b)} бюджету", delta_color="inverse" if total_s > total_b else "off")
    c2.metric("📋 Залишок бюджету", fmt(max(0, total_b - total_s)))
    c3.metric("⚠️ Перевищено", f"{len(over_cats)} категорій", delta_color="inverse" if over_cats else "off")

    if over_cats:
        st.warning(f"Перевищено бюджет: {', '.join(c['label'] for c in over_cats)}")

    # Pie chart
    if spent:
        pie_labels = [cat_label(k) for k in spent]
        pie_vals   = list(spent.values())
        pie_colors = [CAT_MAP.get(k,{}).get("color","#888") for k in spent]
        fig = go.Figure(go.Pie(labels=pie_labels, values=pie_vals, hole=0.5, marker_colors=pie_colors, textinfo="percent+label", textfont_size=10))
        chart_layout(fig, "Розподіл витрат", 300)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="section-label">Бюджет по категоріях</div>', unsafe_allow_html=True)

    updated = False
    for cat in EXP_CATS:
        s = spent.get(cat["id"], 0)
        b = budgets.get(cat["id"], 0)
        pct = min(100, round(s/b*100)) if b > 0 else 0
        is_over = s > b > 0

        col_icon, col_info, col_budget = st.columns([0.5, 3, 1.5])
        with col_icon:
            st.markdown(f"<div style='font-size:22px;margin-top:8px'>{cat['icon']}</div>", unsafe_allow_html=True)
        with col_info:
            bar_color = "#FF4757" if is_over else ("#ffa502" if pct > 80 else cat["color"])
            st.markdown(f"""
            <div style="margin-top:6px">
                <div style="font-size:13px;font-weight:500;margin-bottom:4px">{cat['label']}
                    <span style="color:#6b6b90;font-size:12px;margin-left:8px">{fmt(s)} / {fmt(b)}</span>
                    {'<span style="color:#FF4757;font-size:11px;margin-left:6px">⚠ перевищено</span>' if is_over else ''}
                </div>
                <div style="background:#1e1e3a;border-radius:99px;height:6px;overflow:hidden">
                    <div style="width:{pct}%;height:100%;background:{bar_color};border-radius:99px"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_budget:
            new_b = st.number_input("", value=b, min_value=0, step=500, label_visibility="collapsed", key=f"b_{cat['id']}")
            if new_b != b:
                budgets[cat["id"]] = new_b
                updated = True

    if updated:
        data["budgets"] = budgets
        save_data(data)

# ── PAGE: DEBTS ───────────────────────────────────────────────────────────────
def page_debts(data, user_filter):
    st.markdown('<div class="h1-title">🔴 Борги</div>', unsafe_allow_html=True)

    debts = data["debts"]
    owe   = [d for d in debts if d["dir"]=="owe"]
    owed  = [d for d in debts if d["dir"]=="owed"]
    total_owe  = sum(to_uah(d["amount"]-d["paid"], d["currency"]) for d in owe)
    total_owed = sum(to_uah(d["amount"]-d["paid"], d["currency"]) for d in owed)

    c1, c2, c3 = st.columns(3)
    c1.metric("😟 Я винен",   fmt(total_owe),  f"{len(owe)} боргів",  delta_color="inverse")
    c2.metric("😊 Мені винні",fmt(total_owed), f"{len(owed)} боргів")
    c3.metric("⚖️ Нетто",    fmt(total_owed - total_owe), delta_color="normal" if total_owed >= total_owe else "inverse")

    for title, group, border in [("😟 Я винен", owe, "#FF4757"), ("😊 Мені винні", owed, "#00D084")]:
        if group:
            st.markdown(f'<div class="section-label" style="margin-top:16px">{title}</div>', unsafe_allow_html=True)
            for d in group:
                remaining = d["amount"] - d["paid"]
                pct = min(100, round(d["paid"]/d["amount"]*100)) if d["amount"] > 0 else 0
                user_badge = f'<span class="user-badge-{d.get("user","family")}">{USERS.get(d.get("user","family"),{}).get("name","")}</span>'
                st.markdown(f"""
                <div class="wallet-card" style="border-left:3px solid {border}">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
                        <div>
                            <div style="font-weight:600;font-size:15px">{d['label']}</div>
                            <div style="font-size:12px;color:#6b6b90;margin-top:2px">{d.get('note','')} {user_badge}</div>
                            {'<div style="font-size:12px;color:#ffa502;margin-top:2px">📅 До: '+d['due']+'</div>' if d.get('due') else ''}
                        </div>
                        <div style="text-align:right">
                            <div style="font-family:Unbounded,sans-serif;font-size:20px;font-weight:800;color:{border}">{remaining:,.0f} {d['currency']}</div>
                            <div style="font-size:12px;color:#6b6b90">з {d['amount']:,.0f} {d['currency']}</div>
                        </div>
                    </div>
                    <div style="background:#1e1e3a;border-radius:99px;height:6px;overflow:hidden;margin-bottom:8px">
                        <div style="width:{pct}%;height:100%;background:{border};border-radius:99px"></div>
                    </div>
                    <div style="font-size:12px;color:#6b6b90">Погашено: {pct}% · {fmt(d['paid'], d['currency'])}</div>
                </div>
                """, unsafe_allow_html=True)

                new_paid = st.number_input(f"Оновити сплачену суму ({d['label']})", min_value=0.0, max_value=float(d["amount"]), value=float(d["paid"]), step=100.0, key=f"paid_{d['id']}")
                if new_paid != d["paid"]:
                    d["paid"] = new_paid
                    save_data(data)
                    st.rerun()

    st.markdown("---")
    with st.expander("➕ Додати борг"):
        c1, c2 = st.columns(2)
        with c1:
            d_dir    = st.selectbox("Напрямок", ["owe","owed"], format_func=lambda x: "😟 Я винен" if x=="owe" else "😊 Мені винні", key="d_dir")
            d_label  = st.text_input("Назва / Кому", key="d_label")
            d_amount = st.number_input("Сума", min_value=0.0, step=100.0, key="d_amount")
            d_cur    = st.selectbox("Валюта", ["₴","$","€"], key="d_cur")
        with c2:
            d_user   = st.selectbox("Хто", list(USERS.keys()), format_func=lambda x: USERS[x]["name"], key="d_user")
            d_due    = st.text_input("Дедлайн (РРРР-ММ-ДД)", key="d_due")
            d_note   = st.text_input("Примітка", key="d_note")
        if st.button("💾 Додати борг"):
            if d_label and d_amount > 0:
                data["debts"].append({"id":uid(),"dir":d_dir,"label":d_label,"amount":d_amount,"currency":d_cur,"paid":0,"due":d_due,"note":d_note,"user":d_user})
                save_data(data); st.success("Додано!"); st.rerun()

# ── PAGE: SAVINGS ─────────────────────────────────────────────────────────────
def page_savings(data, user_filter):
    st.markdown('<div class="h1-title">📈 Інвестиції та заощадження</div>', unsafe_allow_html=True)

    savs = data["savings"]
    if user_filter != "family":
        savs = [s for s in savs if s.get("user","family") in (user_filter,"family")]

    by_instr = {}
    for s in savs:
        if s["instrument"] not in by_instr:
            by_instr[s["instrument"]] = {"uah": 0, "items": []}
        by_instr[s["instrument"]]["uah"] += to_uah(s["amount"], s["currency"])
        by_instr[s["instrument"]]["items"].append(s)

    total_uah = sum(v["uah"] for v in by_instr.values())
    total_usd = total_uah / USD
    w_rate = 0
    if total_usd > 0:
        for inst in INSTRUMENTS:
            usd = by_instr.get(inst["id"], {}).get("uah", 0) / USD
            w_rate += usd * inst["rate"]
        w_rate /= total_usd
    annual_usd = total_usd * (w_rate / 100)

    c1, c2, c3 = st.columns(3)
    c1.metric("💼 Портфель",      f"${round(total_usd):,}", fmt(total_uah))
    c2.metric("📊 Сер. дохідність", f"{w_rate:.1f}%",       "річних у $")
    c3.metric("💰 Дохід/рік",      f"${round(annual_usd):,}", "прогноз")

    # Portfolio pie
    if by_instr:
        pie_labels = [INSTR_MAP.get(k,{}).get("label",k) for k in by_instr]
        pie_vals   = [v["uah"]/USD for v in by_instr.values()]
        pie_colors = [INSTR_MAP.get(k,{}).get("color","#888") for k in by_instr]
        fig = go.Figure(go.Pie(labels=pie_labels, values=pie_vals, hole=0.55, marker_colors=pie_colors,
                               textinfo="percent+label", textfont_size=11,
                               hovertemplate="%{label}: $%{value:,.0f}<extra></extra>"))
        chart_layout(fig, "Розподіл портфелю ($)", 280)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    for inst in INSTRUMENTS:
        d = by_instr.get(inst["id"])
        usd = (d["uah"]/USD) if d else 0
        ann = usd * (inst["rate"]/100)
        share = round(usd/total_usd*100) if total_usd > 0 else 0

        with st.expander(f"{inst['icon']} {inst['label']} — ${round(usd):,} · {inst['rate']}% річних"):
            col_a, col_b = st.columns([3,1])
            with col_a:
                if usd > 0:
                    st.markdown(f"""
                    <div style="display:flex;gap:24px;margin-bottom:10px">
                        <div><div class="section-label">Сума</div><div style="font-family:Unbounded;font-size:18px;font-weight:700;color:{inst['color']}">${round(usd):,}</div></div>
                        <div><div class="section-label">Дохід/рік</div><div style="font-size:16px;font-weight:600;color:#00D084">+${round(ann):,}</div></div>
                        <div><div class="section-label">Частка</div><div style="font-size:16px;font-weight:600">{share}%</div></div>
                    </div>
                    <div style="background:#1e1e3a;border-radius:99px;height:6px;overflow:hidden">
                        <div style="width:{share}%;height:100%;background:{inst['color']};border-radius:99px"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    for item in d["items"]:
                        st.markdown(f"<div style='font-size:12px;color:#6b6b90;border-top:1px solid #1e1e3a;margin-top:6px;padding-top:6px'>{item['date']} · {item['amount']} {item['currency']} · {item.get('note','')}</div>", unsafe_allow_html=True)
                else:
                    st.info("Немає позицій")
            with col_b:
                new_amt = st.number_input("Поповнити", min_value=0.0, step=100.0, key=f"sav_{inst['id']}_amt")
                new_cur = st.selectbox("Валюта", ["₴","$"], key=f"sav_{inst['id']}_cur")
                new_user = st.selectbox("Хто", list(USERS.keys()), format_func=lambda x: USERS[x]["name"], key=f"sav_{inst['id']}_user")
                new_note = st.text_input("Примітка", key=f"sav_{inst['id']}_note")
                if st.button("➕ Додати", key=f"sav_{inst['id']}_btn"):
                    if new_amt > 0:
                        data["savings"].append({"id":uid(),"instrument":inst["id"],"amount":new_amt,"currency":new_cur,"date":TODAY,"note":new_note,"user":new_user})
                        save_data(data); st.success("Додано!"); st.rerun()

    # Risk matrix
    st.markdown("---")
    st.markdown('<div class="section-label">Матриця ризику та ліквідності</div>', unsafe_allow_html=True)
    RISK_DATA = [
        {"inst":"inzhur_reit",   "risk":2,"liquid":4,"desc":"Реальний досвід виводу протягом дня"},
        {"inst":"binance_flex",  "risk":3,"liquid":5,"desc":"Платформний ризик, миттєвий вивід"},
        {"inst":"inzhur_energy", "risk":3,"liquid":2,"desc":"Вищий % але нижча ліквідність"},
        {"inst":"mono_jar",      "risk":1,"liquid":5,"desc":"Мінімальний ризик, страхування НГФ"},
        {"inst":"ovdp",          "risk":1,"liquid":3,"desc":"Держгарантія, фіксований термін"},
    ]
    for r in RISK_DATA:
        inst = INSTR_MAP.get(r["inst"], {})
        risk_dots   = "🔴"*r["risk"]   + "⚫"*(5-r["risk"])
        liquid_dots = "🟢"*r["liquid"] + "⚫"*(5-r["liquid"])
        st.markdown(f"""
        <div class="wallet-card" style="margin-bottom:8px">
            <div style="display:flex;align-items:center;gap:12px">
                <span style="font-size:22px">{inst.get('icon','')}</span>
                <div style="flex:1">
                    <div style="font-weight:600;font-size:13px">{inst.get('label','')} <span style="color:{inst.get('color','')};margin-left:8px">{inst.get('rate',0)}% річних</span></div>
                    <div style="font-size:11px;color:#6b6b90;margin-top:2px">{r['desc']}</div>
                    <div style="font-size:12px;margin-top:4px">Ризик: {risk_dots} &nbsp;&nbsp; Ліквідність: {liquid_dots}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── PAGE: GOALS ───────────────────────────────────────────────────────────────
def page_goals(data, user_filter):
    st.markdown('<div class="h1-title">🎯 Фінансові цілі</div>', unsafe_allow_html=True)

    if "roadmap" not in data:
        data["roadmap"] = []

    goals = data["goals"]
    total_pct = 0
    if goals:
        nums = [min(1, g["saved"]/g["target"]) if g["target"] > 0 else 0 for g in goals]
        total_pct = round(sum(nums)/len(nums)*100)

    done_count = sum(1 for g in goals if g["saved"] >= g["target"])
    st.markdown(f"""
    <div class="wallet-card-hero" style="text-align:center">
        <div class="section-label">Загальний прогрес цілей</div>
        <div class="h1-title" style="font-size:52px;color:#a78bfa;letter-spacing:-.04em">{total_pct}%</div>
        <div style="background:#1e1e3a;border-radius:99px;height:8px;overflow:hidden;margin-top:16px">
            <div style="width:{total_pct}%;height:100%;background:linear-gradient(90deg,#7B61FF,#a78bfa,#00D084);border-radius:99px"></div>
        </div>
        <div style="color:#6b6b90;font-size:13px;margin-top:10px">{len(goals)} цілей · {done_count} виконано</div>
    </div>
    """, unsafe_allow_html=True)

    for g in list(goals):
        pct = min(100, round(g["saved"]/g["target"]*100)) if g["target"] > 0 else 0
        done = pct >= 100
        remaining = max(0, g["target"] - g["saved"])
        label = f"{g['icon']} {g['label']} — {pct}%  {'✅' if done else ''}"

        with st.expander(label, expanded=not done):
            col_prog, col_edit = st.columns([3, 2])
            with col_prog:
                bar_html = f"""
                <div style="margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                        <span style="font-size:13px;color:#6b6b90">Накопичено: <strong style="color:{g['color']}">{fmt(g['saved'],g['currency'])}</strong></span>
                        <span style="font-size:13px;color:#6b6b90">Ціль: <strong>{fmt(g['target'],g['currency'])}</strong></span>
                    </div>
                    <div style="background:#1e1e3a;border-radius:99px;height:10px;overflow:hidden">
                        <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{g['color']}88,{g['color']});border-radius:99px"></div>
                    </div>
                    <div style="font-size:12px;color:#6b6b90;margin-top:8px">
                        Залишилось: <strong style="color:{g['color']}">{fmt(remaining,g['currency'])}</strong> · До: {g['deadline']}
                    </div>
                </div>
                """
                st.markdown(bar_html, unsafe_allow_html=True)
            with col_edit:
                gid = g['id']
                new_saved  = st.number_input("Накопичено",  value=float(g["saved"]),  min_value=0.0,  step=100.0, key=f"gs_{gid}_sav")
                new_target = st.number_input("Ціль",        value=float(g["target"]), min_value=1.0,  step=100.0, key=f"gs_{gid}_tgt")
                new_label  = st.text_input("Назва",         value=g["label"],  key=f"gs_{gid}_lbl")
                col_ic, col_cl = st.columns(2)
                with col_ic:
                    new_icon  = st.text_input("Іконка", value=g["icon"],  key=f"gs_{gid}_ico")
                with col_cl:
                    new_color = st.color_picker("Колір", value=g["color"], key=f"gs_{gid}_col")
                new_dl  = st.text_input("Дедлайн",    value=g["deadline"], key=f"gs_{gid}_dl")
                new_cur = st.selectbox("Валюта", ["₴","$"], index=0 if g["currency"]=="₴" else 1, key=f"gs_{gid}_cur")
                col_sv, col_dl2 = st.columns(2)
                with col_sv:
                    if st.button("💾 Зберегти", key=f"gs_{gid}_save", use_container_width=True):
                        g["saved"]    = new_saved
                        g["target"]   = new_target
                        g["label"]    = new_label
                        g["icon"]     = new_icon
                        g["color"]    = new_color
                        g["deadline"] = new_dl
                        g["currency"] = new_cur
                        save_data(data)
                        st.success("Збережено!")
                        st.rerun()
                with col_dl2:
                    if st.button("🗑️ Видалити", key=f"gs_{gid}_del", use_container_width=True):
                        data["goals"] = [x for x in data["goals"] if x["id"] != gid]
                        save_data(data)
                        st.warning("Видалено!")
                        st.rerun()

    st.markdown("---")
    with st.expander("➕ Додати нову ціль"):
        c1, c2 = st.columns(2)
        with c1:
            ng_label  = st.text_input("Назва цілі", key="ng_label")
            ng_target = st.number_input("Сума цілі", min_value=1.0, step=100.0, key="ng_target")
            ng_cur    = st.selectbox("Валюта", ["₴","$"], key="ng_cur")
            ng_saved  = st.number_input("Вже накопичено", min_value=0.0, step=100.0, key="ng_saved")
        with c2:
            ng_icon  = st.text_input("Іконка (емодзі)", value="🎯", key="ng_icon")
            ng_color = st.color_picker("Колір", value="#7B61FF", key="ng_color")
            ng_dl    = st.text_input("Дедлайн (РРРР-ММ-ДД)", value="2027-12-01", key="ng_dl")
        if st.button("✅ Створити ціль", use_container_width=True, key="ng_create"):
            if ng_label and ng_target > 0:
                data["goals"].append({
                    "id": uid(), "label": ng_label, "target": ng_target,
                    "currency": ng_cur, "icon": ng_icon, "color": ng_color,
                    "deadline": ng_dl, "saved": ng_saved,
                })
                save_data(data)
                st.success(f"Ціль додано!")
                st.rerun()

    st.markdown("---")
    st.markdown('<div class="h1-title" style="font-size:22px;margin-bottom:4px">🗺️ Дорожня карта</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6b6b90;font-size:13px;margin-bottom:16px">Відстежуй виконання плану по місяцях. Пересувай повзунок — виконані кроки підсвічуються.</div>', unsafe_allow_html=True)

    plan_month = st.slider("Поточний місяць плану", 1, 60, 1, key="roadmap_slider")
    roadmap = sorted(data.get("roadmap", []), key=lambda x: x["month"])

    if not roadmap:
        st.info("Дорожня карта порожня. Додай перший крок нижче.")

    for item in roadmap:
        done  = item["month"] <= plan_month
        color = "#7B61FF" if done else "#4a4880"
        glow  = "0 0 12px #7B61FF66" if done else "none"
        bg    = "#7B61FF22" if done else "#1e1e3a"
        tc    = "#f0efff" if done else "#6b6b90"
        col_item, col_del = st.columns([6, 1])
        with col_item:
            st.markdown(f"""
            <div style="display:flex;gap:14px;padding:10px 0;border-bottom:1px solid #1e1e3a;align-items:center">
                <div style="width:40px;height:40px;border-radius:50%;background:{bg};border:2px solid {color};
                    display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;box-shadow:{glow}">{item['icon']}</div>
                <div>
                    <div style="font-size:11px;color:{color};font-weight:700;letter-spacing:.08em;margin-bottom:2px">МІСЯЦЬ {item['month']}</div>
                    <div style="font-size:13px;color:{tc};line-height:1.4">{item['text']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_del:
            st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"rd_{item['id']}", help="Видалити крок"):
                data["roadmap"] = [r for r in data["roadmap"] if r["id"] != item["id"]]
                save_data(data)
                st.rerun()

    st.markdown("---")
    with st.expander("➕ Додати крок до дорожньої карти"):
        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            rm_month = st.number_input("Місяць", min_value=1, max_value=120, value=1, key="rm_month")
        with c2:
            rm_icon = st.text_input("Іконка", value="📌", key="rm_icon")
        with c3:
            rm_text = st.text_input("Опис кроку", placeholder="Що має статись?", key="rm_text")
        if st.button("✅ Додати крок", use_container_width=True, key="rm_add"):
            if rm_text:
                data["roadmap"].append({"id": uid(), "month": rm_month, "icon": rm_icon, "text": rm_text})
                save_data(data)
                st.success(f"Крок для місяця {rm_month} додано!")
                st.rerun()


# ── PAGE: ANALYTICS ───────────────────────────────────────────────────────────
def page_analytics(data, user_filter):
    st.markdown('<div class="h1-title">🔍 Аналітика</div>', unsafe_allow_html=True)

    # 6-month area chart
    months_data = []
    for i in range(5, -1, -1):
        mo = CM - i
        yr = CY
        if mo < 0: mo += 12; yr -= 1
        mk = f"{yr}-{str(mo+1).zfill(2)}"
        mi, me = month_stats(data, user_filter, mk)
        months_data.append({"month": SHORT_UA[mo], "Доходи": round(mi), "Витрати": round(me), "Заощадження": round(mi-me)})

    df = pd.DataFrame(months_data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["month"], y=df["Доходи"],    fill="tozeroy", name="Доходи",    line=dict(color="#00D084",width=2), fillcolor="#00D08422"))
    fig.add_trace(go.Scatter(x=df["month"], y=df["Витрати"],   fill="tozeroy", name="Витрати",   line=dict(color="#FF4757",width=2), fillcolor="#FF475722"))
    fig.add_trace(go.Scatter(x=df["month"], y=df["Заощадження"],name="Заощадження",line=dict(color="#7B61FF",width=2,dash="dot")))
    chart_layout(fig, "Рух коштів за 6 місяців", 300)
    st.plotly_chart(fig, use_container_width=True)

    # Who spends what
    col_l, col_r = st.columns(2)
    with col_l:
        by_user = {}
        for t in filter_tx(data, "family", THIS_MONTH, "expense"):
            u = t.get("user","family")
            by_user[u] = by_user.get(u, 0) + to_uah(t["amount"], t["currency"])
        if by_user:
            fig2 = go.Figure(go.Bar(
                x=[USERS.get(u,{}).get("name",u) for u in by_user],
                y=list(by_user.values()),
                marker_color=[USERS.get(u,{}).get("color","#888") for u in by_user],
                marker_cornerradius=6,
            ))
            chart_layout(fig2, "Витрати по членах сім'ї (цей місяць, ₴)", 260)
            st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        # Savings bar
        sav_fig = go.Figure()
        for row in months_data:
            color = "#7B61FF" if row["Заощадження"] >= 0 else "#FF4757"
        sav_fig.add_trace(go.Bar(
            x=df["month"], y=df["Заощадження"],
            marker_color=["#7B61FF" if v >= 0 else "#FF4757" for v in df["Заощадження"]],
            marker_cornerradius=5, name="Накопичення",
        ))
        chart_layout(sav_fig, "Накопичення по місяцях (₴)", 260)
        st.plotly_chart(sav_fig, use_container_width=True)

    # Key insights
    st.markdown("---")
    st.markdown('<div class="section-label">Ключові інсайти</div>', unsafe_allow_html=True)

    all_exp = filter_tx(data, user_filter, tx_type="expense")
    cig_total  = sum(to_uah(t["amount"],t["currency"]) for t in all_exp if t["cat"]=="cigs")
    auto_total = sum(to_uah(t["amount"],t["currency"]) for t in all_exp if t["cat"] in ("fuel","car"))
    subs_total = sum(to_uah(t["amount"],t["currency"]) for t in all_exp if t["cat"] in ("subs","mobile"))
    inc_total  = sum(to_uah(t["amount"],t["currency"]) for t in filter_tx(data, user_filter, tx_type="income"))

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🚬 Цигарки",       fmt(cig_total),  "за весь час")
    c2.metric("🚗 Авто",          fmt(auto_total), "пальне + ремонт")
    c3.metric("📱 Підписки",      fmt(subs_total), "за весь час")
    c4.metric("💰 Загальний дохід",fmt(inc_total),  "за весь час")

    # Cigarettes what-if
    st.markdown(f"""
    <div class="wallet-card" style="background:#0d1a14;border-color:#00D08433;margin-top:16px">
        <div style="font-weight:700;font-size:15px;color:#00D084;margin-bottom:12px">💡 Якби кинути цигарки...</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:16px">
            <div><div class="section-label">Економія/міс</div><div style="font-size:18px;font-weight:700;color:#00D084">{fmt(4800)}</div></div>
            <div><div class="section-label">Економія/рік</div><div style="font-size:18px;font-weight:700;color:#00D084">{fmt(57600)}</div></div>
            <div><div class="section-label">За 2 роки ($)</div><div style="font-size:18px;font-weight:700;color:#00D084">${round(57600*2/USD):,}</div></div>
            <div><div class="section-label">Ремонт швидше</div><div style="font-size:18px;font-weight:700;color:#00D084">~6 міс.</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    inject_css()

    if "data" not in st.session_state:
        st.session_state.data = load_data()

    data = st.session_state.data

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="font-family:'Unbounded',sans-serif;font-size:22px;font-weight:800;margin-bottom:4px">
            <span style="color:#a78bfa">Wallet</span>UA
        </div>
        <div style="font-size:11px;color:#4a4880;margin-bottom:24px">Сімейний бюджет</div>
        """, unsafe_allow_html=True)

        # User selector
        st.markdown('<div style="font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4a4880;margin-bottom:8px">ПЕРЕГЛЯДАЄ</div>', unsafe_allow_html=True)
        user_filter = st.radio(
            "",
            list(USERS.keys()),
            format_func=lambda x: USERS[x]["name"],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Navigation
        st.markdown('<div style="font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4a4880;margin-bottom:8px">НАВІГАЦІЯ</div>', unsafe_allow_html=True)
        pages = [
            ("dashboard",    "⚡ Головна"),
            ("accounts",     "💳 Рахунки"),
            ("transactions", "📋 Операції"),
            ("budget",       "📊 Бюджет"),
            ("debts",        "🔴 Борги"),
            ("savings",      "📈 Інвестиції"),
            ("goals",        "🎯 Цілі"),
            ("analytics",    "🔍 Аналітика"),
        ]
        if "page" not in st.session_state:
            st.session_state.page = "dashboard"

        for page_id, page_name in pages:
            is_active = st.session_state.page == page_id
            if st.button(page_name, key=f"nav_{page_id}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.page = page_id
                st.rerun()

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:11px;color:#4a4880;text-align:center">
            1$ = {USD} ₴ · 1€ = {EUR} ₴<br>
            <span style="color:#6b6b90">{MONTHS_UA[CM]} {CY}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Скинути до початку", type="secondary", use_container_width=True):
            st.session_state.data = default_data()
            save_data(st.session_state.data)
            st.rerun()

    # Main content
    page = st.session_state.get("page", "dashboard")

    if page == "dashboard":    page_dashboard(data, user_filter)
    elif page == "accounts":   page_accounts(data, user_filter)
    elif page == "transactions": page_transactions(data, user_filter)
    elif page == "budget":     page_budget(data, user_filter)
    elif page == "debts":      page_debts(data, user_filter)
    elif page == "savings":    page_savings(data, user_filter)
    elif page == "goals":      page_goals(data, user_filter)
    elif page == "analytics":  page_analytics(data, user_filter)

    # Save any changes
    save_data(st.session_state.data)

if __name__ == "__main__":
    main()
