import streamlit as st
import json, os, uuid
from datetime import datetime, date
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="WalletUA", page_icon="💸", layout="wide", initial_sidebar_state="expanded")

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
USD = 44.38; EUR = 51.67
DATA_FILE = "wallet_data.json"
MONTHS_UA = ["Січень","Лютий","Березень","Квітень","Травень","Червень",
             "Липень","Серпень","Вересень","Жовтень","Листопад","Грудень"]
SHORT_UA  = ["Січ","Лют","Бер","Кві","Тра","Чер","Лип","Сер","Вер","Жов","Лис","Гру"]
CY = datetime.now().year; CM = datetime.now().month - 1
TODAY = date.today().isoformat()
THIS_MONTH = f"{CY}-{str(CM+1).zfill(2)}"
PREV_MONTH = f"{CY}-{str(CM).zfill(2)}" if CM > 0 else f"{CY-1}-12"

USERS = {
    "family": {"name": "👨‍👩‍👧 Сім'я", "color": "#7B61FF"},
    "me":     {"name": "👤 Я",        "color": "#00D084"},
    "wife":   {"name": "👩 Дружина",  "color": "#ec4899"},
}

INC_CATS = [
    {"id":"salary",   "label":"Зарплата",          "icon":"💼","color":"#00D084"},
    {"id":"housing",  "label":"Компенсація найму",  "icon":"🏠","color":"#00b872"},
    {"id":"parents",  "label":"Допомога батьків",   "icon":"👨‍👩‍👧","color":"#34d399"},
    {"id":"rental",   "label":"Дохід від оренди",   "icon":"🏢","color":"#059669"},
    {"id":"divid",    "label":"Дивіденди",          "icon":"📈","color":"#10b981"},
    {"id":"freelance","label":"Фріланс",            "icon":"💻","color":"#6ee7b7"},
    {"id":"cashback", "label":"Кешбек",             "icon":"🎁","color":"#a7f3d0"},
    {"id":"other_i",  "label":"Інші доходи",        "icon":"➕","color":"#6b7280"},
]
EXP_CATS = [
    {"id":"rent",     "label":"Оренда",            "icon":"🏠","color":"#FF4757","budget":13314},
    {"id":"mortgage", "label":"Іпотека",           "icon":"🏦","color":"#ff6b81","budget":8000},
    {"id":"utils",    "label":"Комуналка",         "icon":"💡","color":"#ffa502","budget":2000},
    {"id":"food",     "label":"Продукти",          "icon":"🛒","color":"#84cc16","budget":5000},
    {"id":"cafe",     "label":"Кафе / Ресторани",  "icon":"☕","color":"#22c55e","budget":1500},
    {"id":"child",    "label":"Дитяче",            "icon":"👶","color":"#06b6d4","budget":2000},
    {"id":"fuel",     "label":"Пальне",            "icon":"⛽","color":"#3b82f6","budget":2000},
    {"id":"car",      "label":"Ремонт авто",       "icon":"🔧","color":"#6366f1","budget":1000},
    {"id":"mobile",   "label":"Мобільний зв'язок", "icon":"📞","color":"#a855f7","budget":850},
    {"id":"subs",     "label":"Підписки",          "icon":"📱","color":"#8b5cf6","budget":1641},
    {"id":"cigs",     "label":"Цигарки",           "icon":"🚬","color":"#ec4899","budget":4800},
    {"id":"clothes",  "label":"Одяг",              "icon":"👕","color":"#f43f5e","budget":1000},
    {"id":"health",   "label":"Здоров'я",          "icon":"💊","color":"#14b8a6","budget":500},
    {"id":"entertain","label":"Розваги",           "icon":"🎮","color":"#f59e0b","budget":500},
    {"id":"edu",      "label":"Освіта",            "icon":"📚","color":"#0ea5e9","budget":0},
    {"id":"gifts",    "label":"Подарунки",         "icon":"🎀","color":"#e879f9","budget":0},
    {"id":"travel",   "label":"Подорожі",          "icon":"✈️","color":"#38bdf8","budget":0},
    {"id":"other_e",  "label":"Інше",              "icon":"💸","color":"#6b7280","budget":1000},
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
def to_uah(a, c): return a*USD if c=="$" else a*EUR if c=="€" else a
def fmt(n, cur="₴"):
    n = abs(float(n)); s = f"{n:,.0f}".replace(",", "\u202f")
    return f"${s}" if cur=="$" else f"€{s}" if cur=="€" else f"{s} ₴"
def uid(): return str(uuid.uuid4())[:8]
def cat_info(cat_id): return CAT_MAP.get(cat_id, {"label":cat_id,"icon":"❓","color":"#888"})

def rgba(hex6, alpha):
    h = hex6.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

# ── DATA ──────────────────────────────────────────────────────────────────────
def default_data():
    return {
        "accounts": [
            {"id":uid(),"name":"Monobank",   "type":"card",  "currency":"₴","balance":4200, "icon":"🐱","note":"Чорна картка","user":"me"},
            {"id":uid(),"name":"ПриватБанк", "type":"card",  "currency":"₴","balance":1850, "icon":"🏦","note":"",            "user":"wife"},
            {"id":uid(),"name":"Готівка",    "type":"cash",  "currency":"₴","balance":3500, "icon":"💵","note":"",            "user":"family"},
            {"id":uid(),"name":"Binance",    "type":"crypto","currency":"$", "balance":68,   "icon":"🟡","note":"Earn Flexible","user":"me"},
        ],
        "transactions": [
            {"id":uid(),"type":"income", "cat":"salary",  "amount":35000,"currency":"₴","note":"Зарплата",         "date":f"{THIS_MONTH}-01","user":"me"},
            {"id":uid(),"type":"income", "cat":"housing", "amount":2300, "currency":"₴","note":"Компенсація найму","date":f"{THIS_MONTH}-01","user":"me"},
            {"id":uid(),"type":"income", "cat":"parents", "amount":100,  "currency":"$","note":"Батьки",           "date":f"{THIS_MONTH}-02","user":"family"},
            {"id":uid(),"type":"expense","cat":"rent",    "amount":300,  "currency":"$","note":"Оренда",           "date":f"{THIS_MONTH}-03","user":"family"},
            {"id":uid(),"type":"expense","cat":"utils",   "amount":1800, "currency":"₴","note":"Комуналка",        "date":f"{THIS_MONTH}-05","user":"family"},
            {"id":uid(),"type":"expense","cat":"mobile",  "amount":850,  "currency":"₴","note":"Київстар ×2",      "date":f"{THIS_MONTH}-05","user":"family"},
            {"id":uid(),"type":"expense","cat":"subs",    "amount":1641, "currency":"₴","note":"Netflix+YT+iCloud","date":f"{THIS_MONTH}-05","user":"family"},
            {"id":uid(),"type":"expense","cat":"food",    "amount":3800, "currency":"₴","note":"Сільпо",           "date":f"{THIS_MONTH}-10","user":"wife"},
            {"id":uid(),"type":"expense","cat":"cigs",    "amount":4800, "currency":"₴","note":"Цигарки",          "date":f"{THIS_MONTH}-15","user":"me"},
            {"id":uid(),"type":"expense","cat":"child",   "amount":1500, "currency":"₴","note":"Дитяче",           "date":f"{THIS_MONTH}-12","user":"wife"},
            {"id":uid(),"type":"expense","cat":"fuel",    "amount":1800, "currency":"₴","note":"Пальне Audi",      "date":f"{THIS_MONTH}-14","user":"me"},
            {"id":uid(),"type":"expense","cat":"cafe",    "amount":680,  "currency":"₴","note":"Кав'ярня",         "date":f"{THIS_MONTH}-18","user":"wife"},
            {"id":uid(),"type":"income", "cat":"salary",  "amount":35000,"currency":"₴","note":"Зарплата травень","date":f"{PREV_MONTH}-01","user":"me"},
            {"id":uid(),"type":"expense","cat":"cigs",    "amount":4800, "currency":"₴","note":"Цигарки",          "date":f"{PREV_MONTH}-15","user":"me"},
            {"id":uid(),"type":"expense","cat":"food",    "amount":4200, "currency":"₴","note":"Продукти",         "date":f"{PREV_MONTH}-10","user":"wife"},
            {"id":uid(),"type":"expense","cat":"car",     "amount":3200, "currency":"₴","note":"Ремонт Audi",      "date":f"{PREV_MONTH}-20","user":"me"},
            {"id":uid(),"type":"expense","cat":"rent",    "amount":300,  "currency":"$","note":"Оренда",           "date":f"{PREV_MONTH}-03","user":"family"},
        ],
        "debts": [
            {"id":uid(),"dir":"owe", "label":"Кредитна картка","amount":12260,"currency":"₴","paid":0,"due":"","note":"Monobank кредитка",       "user":"me"},
            {"id":uid(),"dir":"owe", "label":"Іпотека єОселя", "amount":8000, "currency":"₴","paid":0,"due":"","note":"Щомісячний платіж ~20 р.","user":"family"},
            {"id":uid(),"dir":"owed","label":"Весільні кошти",  "amount":2000, "currency":"$","paid":0,"due":"","note":"Повернути в спільний фонд","user":"me"},
        ],
        "savings": [
            {"id":uid(),"instrument":"inzhur_reit",  "amount":2150,"currency":"₴","date":f"{CY}-01-01","note":"Початкова позиція","user":"me",
             "dividends_received":0,"price_growth_pct":0},
            {"id":uid(),"instrument":"binance_flex", "amount":68,  "currency":"$","date":f"{CY}-03-01","note":"Earn USDT","user":"me",
             "dividends_received":0,"price_growth_pct":0},
        ],
        "instrument_rates": {i["id"]: i["rate"] for i in INSTRUMENTS},
        "goals": [
            {"id":"credit", "label":"Закрити кредитку","target":12260,"currency":"₴","icon":"💳","color":"#FF4757","deadline":"2026-07-01","saved":0},
            {"id":"cashpad","label":"Швидка каса",      "target":20000,"currency":"₴","icon":"🚨","color":"#ffa502","deadline":"2026-12-01","saved":0},
            {"id":"wedding","label":"Весільні кошти",   "target":2000, "currency":"$","icon":"💍","color":"#8b5cf6","deadline":"2027-06-01","saved":0},
            {"id":"cushion","label":"Подушка сім'ї",    "target":1500, "currency":"$","icon":"🛡️","color":"#3b82f6","deadline":"2027-09-01","saved":0},
            {"id":"repair", "label":"Ремонт квартири",  "target":3000, "currency":"$","icon":"🏠","color":"#00D084","deadline":"2028-12-01","saved":0},
        ],
        "roadmap": [
            {"id":uid(),"month":1, "icon":"💳","text":"Закрити кредитку 12 260 ₴ одним платежем"},
            {"id":uid(),"month":2, "icon":"🚀","text":"Старт: 7 400 ₴ → Binance (весільні), 4 400 ₴ → Inzhur REIT, 3 200 ₴ → Mono"},
            {"id":uid(),"month":6, "icon":"🚨","text":"Швидка каса 20 000 ₴ набрана"},
            {"id":uid(),"month":12,"icon":"💍","text":"Весільні 2 000$ повернуті на Binance Flexible"},
            {"id":uid(),"month":14,"icon":"🏗️","text":"Старт: 8 000 ₴/міс ремонт + 4 000 ₴ → Inzhur Energy"},
            {"id":uid(),"month":15,"icon":"🛡️","text":"Подушка сім'ї 1 500$ в Inzhur REIT"},
            {"id":uid(),"month":30,"icon":"🏠","text":"Косметичний ремонт готовий, квартира здається в оренду"},
        ],
        "budgets": {c["id"]: c["budget"] for c in EXP_CATS},
        "budget_month": THIS_MONTH,
    }

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,"r",encoding="utf-8") as f:
                d = json.load(f)
            # Migrate missing keys
            if "roadmap" not in d: d["roadmap"] = default_data()["roadmap"]
            if "instrument_rates" not in d: d["instrument_rates"] = {i["id"]:i["rate"] for i in INSTRUMENTS}
            for s in d.get("savings",[]):
                if "dividends_received" not in s: s["dividends_received"] = 0
                if "price_growth_pct"   not in s: s["price_growth_pct"]   = 0
            return d
        except: pass
    return default_data()

def save_data(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Unbounded:wght@600;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#06060f;color:#f0efff}
.stApp{background:#06060f}
.main .block-container{padding:1.5rem 2rem 3rem;max-width:1200px}
section[data-testid="stSidebar"]{background:#0d0d1c;border-right:1px solid #1e1e3a}
[data-testid="stMetric"]{background:#0f0f1c;border:1px solid #1e1e3a;border-radius:14px;padding:16px 20px}
[data-testid="stMetricLabel"] p{color:#6b6b90!important;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}
[data-testid="stMetricValue"]{font-family:'Unbounded',sans-serif;font-size:22px;color:#f0efff}
.stButton>button{background:#7B61FF;color:#fff;border:none;border-radius:10px;font-weight:600;font-size:13px;padding:10px 20px;transition:all .2s}
.stButton>button:hover{background:#8a73ff;box-shadow:0 4px 20px rgba(123,97,255,.3)}
.stButton>button[kind="secondary"]{background:#131327;border:1px solid #1e1e3a;color:#9896c8}
.stButton>button[kind="secondary"]:hover{border-color:#7B61FF;color:#a78bfa}
.stSelectbox>div>div,.stTextInput>div>div>input,.stNumberInput>div>div>input,.stDateInput>div>div>input{background:#131327!important;border:1px solid #1e1e3a!important;border-radius:10px!important;color:#f0efff!important}
.stTextArea>div>div>textarea{background:#131327!important;border:1px solid #1e1e3a!important;color:#f0efff!important}
.stColorPicker>div>div{background:#131327!important;border:1px solid #1e1e3a!important;border-radius:10px!important}
.stTabs [data-baseweb="tab-list"]{background:#0d0d1c;border-radius:12px;padding:4px;gap:4px;border:1px solid #1e1e3a}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:9px;color:#6b6b90;font-weight:600;font-size:13px;padding:8px 16px}
.stTabs [aria-selected="true"]{background:#7B61FF!important;color:#fff!important}
div[data-testid="stExpander"]{background:#0f0f1c;border:1px solid #1e1e3a!important;border-radius:12px}
div[data-testid="stExpander"] summary{color:#9896c8}
.stProgress>div>div>div{background:#7B61FF!important;border-radius:99px!important}
.stProgress>div>div{background:#1e1e3a!important;border-radius:99px!important}
hr{border-color:#1e1e3a}
[data-testid="stSlider"]>div>div>div{background:#7B61FF!important}
</style>""", unsafe_allow_html=True)

# ── PLOTLY THEME ──────────────────────────────────────────────────────────────
PBG = "#0f0f1c"; PPAPER = "#06060f"; PGRID = "#1e1e3a"; PTXT = "#6b6b90"

def apply_theme(fig, title="", height=280):
    fig.update_layout(
        title=dict(text=title, font=dict(color="#9896c8", size=13)),
        plot_bgcolor=PBG, paper_bgcolor=PPAPER,
        font=dict(family="Inter", color=PTXT, size=11),
        margin=dict(l=10,r=10,t=30 if title else 10,b=10),
        height=height, legend=dict(font=dict(color="#9896c8"), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor=PGRID, zerolinecolor=PGRID, linecolor=PGRID),
        yaxis=dict(gridcolor=PGRID, zerolinecolor=PGRID, linecolor=PGRID),
    )
    return fig

# ── TX HELPERS ────────────────────────────────────────────────────────────────
def filter_tx(data, user_filter, month=None, tx_type=None):
    txs = data["transactions"]
    if user_filter != "family":
        txs = [t for t in txs if t["user"] in (user_filter,"family")]
    if month:   txs = [t for t in txs if t["date"].startswith(month)]
    if tx_type: txs = [t for t in txs if t["type"] == tx_type]
    return txs

def month_stats(data, user_filter, month):
    txs = filter_tx(data, user_filter, month)
    inc = sum(to_uah(t["amount"],t["currency"]) for t in txs if t["type"]=="income")
    exp = sum(to_uah(t["amount"],t["currency"]) for t in txs if t["type"]=="expense")
    return inc, exp

def progress_bar(pct, color="#7B61FF", height=6):
    pct = max(0, min(100, pct))
    st.markdown(
        f'<div style="background:#1e1e3a;border-radius:99px;height:{height}px;overflow:hidden;margin:4px 0">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:99px;transition:width .4s ease"></div>'
        f'</div>', unsafe_allow_html=True
    )

def hero_card(content_html):
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0f0a2e,#1a1050,#0a0a1e);border:1px solid rgba(123,97,255,.2);'
        f'border-radius:20px;padding:24px;margin-bottom:16px">{content_html}</div>',
        unsafe_allow_html=True
    )

def wallet_card(content_html, border_color="#1e1e3a", extra_style=""):
    st.markdown(
        f'<div style="background:#0f0f1c;border:1px solid {border_color};border-radius:14px;'
        f'padding:16px 18px;margin-bottom:10px;{extra_style}">{content_html}</div>',
        unsafe_allow_html=True
    )

def section_label(text):
    st.markdown(f'<p style="font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4a4880;margin:0 0 8px">{text}</p>', unsafe_allow_html=True)

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def page_dashboard(data, user):
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:26px;font-weight:800;margin-bottom:4px">⚡ Головна</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#6b6b90;font-size:13px;margin-bottom:20px">1$ = {USD} ₴ · 1€ = {EUR} ₴ · {MONTHS_UA[CM]} {CY}</p>', unsafe_allow_html=True)

    accs = data["accounts"] if user=="family" else [a for a in data["accounts"] if a["user"] in (user,"family")]
    net_worth = sum(to_uah(a["balance"],a["currency"]) for a in accs)
    inc, exp = month_stats(data, user, THIS_MONTH)
    net = inc - exp
    sav_rate = round(net/inc*100) if inc>0 else 0
    savs = data["savings"] if user=="family" else [s for s in data["savings"] if s.get("user","family") in (user,"family")]
    total_sav_uah = sum(to_uah(s["amount"],s["currency"]) for s in savs)
    total_debt = sum(to_uah(d["amount"]-d["paid"],d["currency"]) for d in data["debts"] if d["dir"]=="owe")

    hero_card(
        f'<p style="font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#6b6b90;margin:0 0 8px">Загальний капітал</p>'
        f'<p style="font-family:Unbounded,sans-serif;font-size:34px;font-weight:800;margin:0 0 4px">{fmt(net_worth)}</p>'
        f'<p style="color:#6b6b90;font-size:13px;margin:0 0 20px">≈ ${round(net_worth/USD):,} USD</p>'
        f'<div style="display:flex;gap:32px">'
        f'<div><p style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:0 0 4px">Доходи/міс</p><p style="font-size:18px;font-weight:700;color:#00D084;margin:0">{fmt(inc)}</p></div>'
        f'<div><p style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:0 0 4px">Витрати/міс</p><p style="font-size:18px;font-weight:700;color:#FF4757;margin:0">{fmt(exp)}</p></div>'
        f'<div><p style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:0 0 4px">Інвестиції</p><p style="font-size:18px;font-weight:700;color:#7B61FF;margin:0">≈${round(total_sav_uah/USD):,}</p></div>'
        f'</div>'
    )

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💰 Дохід місяця", fmt(inc), f"норма заощаджень {sav_rate}%")
    c2.metric("💸 Витрати",      fmt(exp), f"залишок {fmt(net)}", delta_color="inverse" if net<0 else "normal")
    c3.metric("📈 Інвестиції",   f"${round(total_sav_uah/USD):,}", f"{len(savs)} позицій")
    c4.metric("🔴 Борги",        fmt(total_debt), "до погашення", delta_color="inverse")
    st.markdown("---")

    col_l, col_r = st.columns([3,2])
    with col_l:
        rows = []
        for i in range(5,-1,-1):
            mo = CM-i; yr = CY
            if mo < 0: mo+=12; yr-=1
            mk = f"{yr}-{str(mo+1).zfill(2)}"
            mi,me = month_stats(data, user, mk)
            rows.append({"m":SHORT_UA[mo],"Доходи":round(mi/1000,1),"Витрати":round(me/1000,1)})
        df = pd.DataFrame(rows)
        fig = go.Figure()
        fig.add_bar(name="Доходи",  x=df["m"], y=df["Доходи"],  marker_color=rgba("#00D084",.55))
        fig.add_bar(name="Витрати", x=df["m"], y=df["Витрати"], marker_color=rgba("#FF4757",.55))
        apply_theme(fig, "Доходи vs Витрати (тис. ₴)", 240)
        fig.update_layout(barmode="group", bargap=0.2)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        txs = filter_tx(data, user, THIS_MONTH, "expense")
        by_cat = {}
        for t in txs: by_cat[t["cat"]] = by_cat.get(t["cat"],0)+to_uah(t["amount"],t["currency"])
        if by_cat:
            labels = [f"{cat_info(k)['icon']} {cat_info(k)['label']}" for k in by_cat]
            colors = [cat_info(k)["color"] for k in by_cat]
            fig2 = go.Figure(go.Pie(labels=labels, values=list(by_cat.values()), hole=0.55,
                                    marker_colors=colors, textinfo="percent", textfont_size=10,
                                    hovertemplate="%{label}: %{value:,.0f} ₴<extra></extra>"))
            apply_theme(fig2, "Структура витрат", 240)
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Немає витрат цього місяця")

    col_tl, col_tr = st.columns(2)
    with col_tl:
        section_label("Топ витрат місяця")
        top = sorted(by_cat.items(), key=lambda x:x[1], reverse=True)[:5] if by_cat else []
        for cat_id, val in top:
            c = cat_info(cat_id)
            pct = round(val/top[0][1]*100) if top else 0
            st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
                        f'<span style="font-size:20px">{c["icon"]}</span>'
                        f'<div style="flex:1"><p style="font-size:13px;font-weight:500;margin:0 0 3px">{c["label"]}</p>', unsafe_allow_html=True)
            progress_bar(pct, c["color"])
            st.markdown(f'</div><span style="font-size:13px;color:#9896c8;font-weight:600;white-space:nowrap">{fmt(val)}</span></div>', unsafe_allow_html=True)

    with col_tr:
        section_label("Останні операції")
        recent = sorted(filter_tx(data,user), key=lambda x:x["date"], reverse=True)[:6]
        for t in recent:
            c = cat_info(t["cat"])
            uc = USERS.get(t.get("user","family"),{}).get("color","#888")
            un = USERS.get(t.get("user","family"),{}).get("name","")
            color = "#00D084" if t["type"]=="income" else "#FF4757"
            sign  = "+" if t["type"]=="income" else "−"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
                f'<div style="width:36px;height:36px;border-radius:10px;background:{c["color"]}22;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0">{c["icon"]}</div>'
                f'<div style="flex:1">'
                f'<p style="font-size:13px;font-weight:500;margin:0">{c["label"]}</p>'
                f'<p style="font-size:11px;color:#6b6b90;margin:0">{t["date"]} · <span style="color:{uc}">{un}</span></p>'
                f'</div>'
                f'<span style="font-weight:700;font-size:14px;color:{color}">{sign}{t["amount"]}{t["currency"]}</span>'
                f'</div>', unsafe_allow_html=True)

    st.markdown("---")
    section_label("Фінансові цілі")
    gcols = st.columns(len(data["goals"]))
    for i,g in enumerate(data["goals"]):
        pct = min(100, round(g["saved"]/g["target"]*100)) if g["target"]>0 else 0
        with gcols[i]:
            st.markdown(
                f'<div style="background:#0f0f1c;border:1px solid {g["color"]}33;border-radius:14px;padding:14px;text-align:center">'
                f'<p style="font-size:22px;margin:0 0 4px">{g["icon"]}</p>'
                f'<p style="font-size:12px;font-weight:600;margin:0 0 4px">{g["label"]}</p>'
                f'<p style="font-family:Unbounded,sans-serif;font-size:20px;font-weight:800;color:{g["color"]};margin:0">{pct}%</p>'
                f'</div>', unsafe_allow_html=True)
            progress_bar(pct, g["color"], 5)
            st.markdown(f'<p style="font-size:11px;color:#6b6b90;text-align:center;margin:0">{fmt(g["saved"],g["currency"])} / {fmt(g["target"],g["currency"])}</p>', unsafe_allow_html=True)

# ── ACCOUNTS ──────────────────────────────────────────────────────────────────
def page_accounts(data, user):
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:26px;font-weight:800;margin-bottom:20px">💳 Рахунки</p>', unsafe_allow_html=True)

    accs = data["accounts"] if user=="family" else [a for a in data["accounts"] if a["user"] in (user,"family")]
    net = sum(to_uah(a["balance"],a["currency"]) for a in accs)

    hero_card(
        f'<p style="font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#6b6b90;margin:0 0 8px">Загальний баланс</p>'
        f'<p style="font-family:Unbounded,sans-serif;font-size:34px;font-weight:800;margin:0 0 4px">{fmt(net)}</p>'
        f'<p style="color:#6b6b90;font-size:13px;margin:0">≈ ${round(net/USD):,} · €{round(net/EUR):,}</p>'
    )

    GRAD = {"card":"135deg,#1a1a40,#2d1f6e","cash":"135deg,#0d2818,#1a5c30",
            "crypto":"135deg,#2a1f00,#5a3d00","savings":"135deg,#0d1a2e,#1a3a5c"}
    cols = st.columns(max(1, len(accs)))
    for i,a in enumerate(accs):
        g = GRAD.get(a["type"], GRAD["card"])
        uah_line = f'<p style="font-size:12px;color:rgba(255,255,255,.4);margin:0 0 8px">≈ {fmt(to_uah(a["balance"],a["currency"]))}</p>' if a["currency"]!="₴" else ""
        user_color = USERS.get(a.get("user","family"),{}).get("color","#888")
        user_name  = USERS.get(a.get("user","family"),{}).get("name","")
        with cols[i]:
            st.markdown(
                f'<div style="background:linear-gradient({g});border:1px solid rgba(255,255,255,.1);border-radius:18px;padding:20px;position:relative;overflow:hidden;min-height:160px">'
                f'<div style="position:absolute;top:-20px;right:-20px;width:80px;height:80px;border-radius:50%;background:rgba(255,255,255,.04)"></div>'
                f'<p style="font-size:26px;margin:0 0 16px">{a["icon"]}</p>'
                f'<p style="font-family:Unbounded,sans-serif;font-size:20px;font-weight:800;margin:0 0 2px">{a["balance"]:,.0f} {a["currency"]}</p>'
                f'{uah_line}'
                f'<p style="font-size:14px;color:rgba(255,255,255,.7);font-weight:600;margin:0">{a["name"]}</p>'
                f'<p style="font-size:11px;color:rgba(255,255,255,.35);margin:0 0 10px">{a.get("note","")}</p>'
                f'<span style="background:{user_color}22;border:1px solid {user_color}44;border-radius:99px;padding:2px 10px;color:{user_color};font-size:11px;font-weight:600">{user_name}</span>'
                f'</div>', unsafe_allow_html=True)

    st.markdown("---")
    section_label("Деталі по рахунках")
    for a in accs:
        mi = sum(to_uah(t["amount"],t["currency"]) for t in data["transactions"] if t["acc_id"]==a["id"] and t["date"].startswith(THIS_MONTH) and t["type"]=="income") if "acc_id" in data["transactions"][0] else 0
        uc = USERS.get(a.get("user","family"),{}).get("color","#888")
        un = USERS.get(a.get("user","family"),{}).get("name","")
        type_icon = {"card":"💳","cash":"💵","crypto":"🔐","savings":"🏦"}.get(a["type"],"💼")
        st.markdown(
            f'<div style="background:#0f0f1c;border:1px solid #1e1e3a;border-radius:12px;padding:14px 18px;display:flex;align-items:center;gap:14px;margin-bottom:8px">'
            f'<div style="width:44px;height:44px;border-radius:12px;background:#7B61FF22;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">{a["icon"]}</div>'
            f'<div style="flex:1">'
            f'<p style="font-weight:600;font-size:14px;margin:0">{a["name"]} <span style="font-size:12px;color:#4a4880">{type_icon}</span></p>'
            f'<p style="font-size:11px;color:#6b6b90;margin:0">{a.get("note","") or a["type"]} · <span style="color:{uc}">{un}</span></p>'
            f'</div>'
            f'<div style="text-align:right">'
            f'<p style="font-family:Unbounded,sans-serif;font-size:18px;font-weight:700;margin:0">{a["balance"]:,.0f} {a["currency"]}</p>'
            f'{"<p style=font-size:11px;color:#6b6b90;margin:0>≈"+fmt(to_uah(a["balance"],a["currency"]))+"</p>" if a["currency"]!="₴" else ""}'
            f'</div>'
            f'</div>', unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("➕ Додати рахунок"):
        c1,c2 = st.columns(2)
        with c1:
            an = st.text_input("Назва", key="acc_n")
            at = st.selectbox("Тип", ["card","cash","crypto","savings"],
                              format_func=lambda x:{"card":"💳 Картка","cash":"💵 Готівка","crypto":"🔐 Крипто","savings":"🏦 Депозит"}[x], key="acc_t")
            ai = st.text_input("Іконка", value="💳", key="acc_i")
        with c2:
            ab = st.number_input("Баланс", step=100.0, key="acc_b")
            ac = st.selectbox("Валюта", ["₴","$","€"], key="acc_c")
            au = st.selectbox("Власник", list(USERS.keys()), format_func=lambda x:USERS[x]["name"], key="acc_u")
            ano = st.text_input("Примітка", key="acc_no")
        if st.button("💾 Зберегти рахунок", key="acc_save"):
            if an:
                data["accounts"].append({"id":uid(),"name":an,"type":at,"currency":ac,"balance":ab,"icon":ai,"note":ano,"user":au})
                save_data(data); st.success("Рахунок додано!"); st.rerun()

    if len(data["accounts"]) > 0:
        with st.expander("🗑️ Видалити рахунок"):
            ids   = [a["id"]   for a in data["accounts"]]
            names = [f"{a['icon']} {a['name']}" for a in data["accounts"]]
            sel = st.selectbox("Оберіть рахунок", ids, format_func=lambda x:names[ids.index(x)], key="acc_del_sel")
            if st.button("🗑️ Видалити", key="acc_del_btn"):
                data["accounts"] = [a for a in data["accounts"] if a["id"]!=sel]
                save_data(data); st.success("Видалено!"); st.rerun()

# ── TRANSACTIONS ──────────────────────────────────────────────────────────────
def page_transactions(data, user):
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:26px;font-weight:800;margin-bottom:20px">📋 Операції</p>', unsafe_allow_html=True)

    with st.expander("➕ Додати операцію", expanded=False):
        c1,c2 = st.columns(2)
        with c1:
            tt = st.selectbox("Тип", ["expense","income"], format_func=lambda x:"💸 Витрата" if x=="expense" else "💰 Дохід", key="tx_t")
            cats = EXP_CATS if tt=="expense" else INC_CATS
            tc = st.selectbox("Категорія", [c["id"] for c in cats], format_func=lambda x:f"{cat_info(x)['icon']} {cat_info(x)['label']}", key="tx_c")
            ta = st.number_input("Сума", min_value=0.0, step=100.0, key="tx_a")
            tcu = st.selectbox("Валюта", ["₴","$","€"], key="tx_cu")
        with c2:
            tu = st.selectbox("Хто", list(USERS.keys()), format_func=lambda x:USERS[x]["name"], key="tx_u")
            td = st.date_input("Дата", value=date.today(), key="tx_d")
            tn = st.text_input("Примітка", key="tx_n")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Зберегти", use_container_width=True, key="tx_save"):
                if ta > 0:
                    data["transactions"].append({"id":uid(),"type":tt,"cat":tc,"amount":ta,"currency":tcu,"note":tn,"date":td.isoformat(),"user":tu})
                    save_data(data); st.success("Додано!"); st.rerun()

    st.markdown("---")
    c1,c2,c3 = st.columns(3)
    with c1: ft = st.selectbox("Тип", ["all","income","expense"], format_func=lambda x:{"all":"Всі","income":"💰 Доходи","expense":"💸 Витрати"}[x], key="f_t")
    with c2: fm = st.text_input("Місяць (РРРР-ММ)", value=THIS_MONTH, key="f_m")
    with c3: fs = st.text_input("🔍 Пошук", key="f_s")

    txs = filter_tx(data, user)
    if ft!="all": txs=[t for t in txs if t["type"]==ft]
    if fm: txs=[t for t in txs if t["date"].startswith(fm)]
    if fs: txs=[t for t in txs if fs.lower() in t.get("note","").lower()]
    txs = sorted(txs, key=lambda x:x["date"], reverse=True)

    if not txs: st.info("Немає операцій"); return

    rows=[]
    for t in txs:
        c = cat_info(t["cat"])
        rows.append({
            "Дата":t["date"],"Тип":"💰" if t["type"]=="income" else "💸",
            "Категорія":f"{c['icon']} {c['label']}",
            "Сума":f"{'+'if t['type']=='income' else '−'}{t['amount']}{t['currency']}",
            "₴ екв.":fmt(to_uah(t["amount"],t["currency"])),
            "Хто":USERS.get(t.get("user","family"),{}).get("name",""),
            "Примітка":t.get("note",""), "_id":t["id"],
        })
    st.dataframe(pd.DataFrame(rows).drop(columns=["_id"]), use_container_width=True, height=380, hide_index=True)

    st.markdown("---")
    ids=[t["id"] for t in txs]
    lbs=[f"{t['date']} · {cat_info(t['cat'])['icon']} {t['amount']}{t['currency']}" for t in txs]
    cd,cb = st.columns([4,1])
    with cd: ds=st.selectbox("Видалити", ids, format_func=lambda x:lbs[ids.index(x)], key="tx_del_s")
    with cb:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Видалити", key="tx_del_b"):
            data["transactions"]=[t for t in data["transactions"] if t["id"]!=ds]
            save_data(data); st.success("Видалено!"); st.rerun()

# ── BUDGET ────────────────────────────────────────────────────────────────────
def page_budget(data, user):
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:26px;font-weight:800;margin-bottom:20px">📊 Бюджет</p>', unsafe_allow_html=True)

    bm = st.text_input("Місяць (РРРР-ММ)", value=THIS_MONTH, key="bm")
    txs = filter_tx(data, user, bm, "expense")
    spent = {}
    for t in txs: spent[t["cat"]]=spent.get(t["cat"],0)+to_uah(t["amount"],t["currency"])
    budgets = data.get("budgets",{c["id"]:c["budget"] for c in EXP_CATS})
    total_b = sum(budgets.values())
    total_s = sum(spent.values())
    over = [c for c in EXP_CATS if spent.get(c["id"],0)>budgets.get(c["id"],0)>0]

    c1,c2,c3 = st.columns(3)
    c1.metric("💸 Витрачено",  fmt(total_s), f"з {fmt(total_b)}", delta_color="inverse" if total_s>total_b else "off")
    c2.metric("✅ Залишок",    fmt(max(0,total_b-total_s)))
    c3.metric("⚠️ Перевищень", str(len(over)), delta_color="inverse" if over else "off")
    if over: st.warning("Перевищено: "+", ".join(c["label"] for c in over))

    if spent:
        fig = go.Figure(go.Pie(
            labels=[f"{cat_info(k)['icon']} {cat_info(k)['label']}" for k in spent],
            values=list(spent.values()), hole=0.5,
            marker_colors=[cat_info(k)["color"] for k in spent],
            textinfo="percent+label", textfont_size=10,
            hovertemplate="%{label}: %{value:,.0f} ₴<extra></extra>",
        ))
        apply_theme(fig, "Розподіл витрат", 280)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    section_label("Бюджет по категоріях")
    updated = False
    for cat in EXP_CATS:
        s = spent.get(cat["id"],0)
        b = budgets.get(cat["id"],0)
        pct = min(100,round(s/b*100)) if b>0 else 0
        is_over = s>b>0
        bar_color = "#FF4757" if is_over else ("#ffa502" if pct>80 else cat["color"])

        col_i, col_info, col_b = st.columns([0.4,3.5,1.5])
        with col_i:
            st.markdown(f'<p style="font-size:22px;margin-top:8px">{cat["icon"]}</p>', unsafe_allow_html=True)
        with col_info:
            over_badge = ' <span style="color:#FF4757;font-size:11px">⚠ перевищено</span>' if is_over else ""
            st.markdown(
                f'<p style="font-size:13px;font-weight:500;margin:6px 0 3px">{cat["label"]}'
                f'<span style="color:#6b6b90;font-size:12px;margin-left:8px">{fmt(s)} / {fmt(b)}</span>'
                f'{over_badge}</p>', unsafe_allow_html=True)
            progress_bar(pct, bar_color)
        with col_b:
            new_b = st.number_input("", value=b, min_value=0, step=500, label_visibility="collapsed", key=f"b_{cat['id']}")
            if new_b != b: budgets[cat["id"]]=new_b; updated=True
    if updated: data["budgets"]=budgets; save_data(data)

# ── DEBTS ─────────────────────────────────────────────────────────────────────
def page_debts(data, user):
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:26px;font-weight:800;margin-bottom:20px">🔴 Борги</p>', unsafe_allow_html=True)

    owe  = [d for d in data["debts"] if d["dir"]=="owe"]
    owed = [d for d in data["debts"] if d["dir"]=="owed"]
    t_owe  = sum(to_uah(d["amount"]-d["paid"],d["currency"]) for d in owe)
    t_owed = sum(to_uah(d["amount"]-d["paid"],d["currency"]) for d in owed)

    c1,c2,c3 = st.columns(3)
    c1.metric("😟 Я винен",    fmt(t_owe),  f"{len(owe)} боргів",  delta_color="inverse")
    c2.metric("😊 Мені винні", fmt(t_owed), f"{len(owed)} боргів")
    c3.metric("⚖️ Нетто",      fmt(t_owed-t_owe), delta_color="normal" if t_owed>=t_owe else "inverse")

    def show_debts(group, border):
        for d in group:
            remaining = d["amount"] - d["paid"]
            pct = min(100, round(d["paid"]/d["amount"]*100)) if d["amount"]>0 else 0
            un  = USERS.get(d.get("user","family"),{}).get("name","")
            uc  = USERS.get(d.get("user","family"),{}).get("color","#888")

            st.markdown(
                f'<div style="background:#0f0f1c;border:1px solid #1e1e3a;border-left:3px solid {border};border-radius:14px;padding:16px 18px;margin-bottom:8px">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
                f'<div>'
                f'<p style="font-weight:600;font-size:15px;margin:0">{d["label"]}</p>'
                f'<p style="font-size:12px;color:#6b6b90;margin:2px 0 0">{d.get("note","")} · <span style="color:{uc}">{un}</span></p>'
                f'{"<p style=font-size:12px;color:#ffa502;margin:2px 0 0>📅 До: "+d["due"]+"</p>" if d.get("due") else ""}'
                f'</div>'
                f'<div style="text-align:right">'
                f'<p style="font-family:Unbounded,sans-serif;font-size:20px;font-weight:800;color:{border};margin:0">{remaining:,.0f} {d["currency"]}</p>'
                f'<p style="font-size:12px;color:#6b6b90;margin:0">з {d["amount"]:,.0f} {d["currency"]}</p>'
                f'</div>'
                f'</div>'
                f'</div>', unsafe_allow_html=True)
            progress_bar(pct, border)
            st.markdown(f'<p style="font-size:12px;color:#6b6b90;margin:0 0 8px">Погашено: {pct}% · {fmt(d["paid"],d["currency"])}</p>', unsafe_allow_html=True)

            col_inp, col_del = st.columns([4,1])
            with col_inp:
                new_paid = st.number_input(f"Сплачено ({d['label']})", min_value=0.0, max_value=float(d["amount"]),
                                           value=float(d["paid"]), step=100.0, key=f"paid_{d['id']}", label_visibility="collapsed")
                if new_paid != d["paid"]:
                    d["paid"] = new_paid; save_data(data); st.rerun()
            with col_del:
                if st.button("🗑️", key=f"debt_del_{d['id']}", help="Видалити"):
                    data["debts"]=[x for x in data["debts"] if x["id"]!=d["id"]]
                    save_data(data); st.rerun()

    if owe:
        st.markdown("---"); section_label("😟 Я винен"); show_debts(owe,"#FF4757")
    if owed:
        st.markdown("---"); section_label("😊 Мені винні"); show_debts(owed,"#00D084")
    if not data["debts"]:
        st.success("🎉 Немає жодного боргу!")

    st.markdown("---")
    with st.expander("➕ Додати борг"):
        c1,c2 = st.columns(2)
        with c1:
            dd = st.selectbox("Напрямок", ["owe","owed"], format_func=lambda x:"😟 Я винен" if x=="owe" else "😊 Мені винні", key="d_dir")
            dl = st.text_input("Назва / Кому", key="d_lbl")
            da = st.number_input("Сума", min_value=0.0, step=100.0, key="d_amt")
            dc = st.selectbox("Валюта", ["₴","$","€"], key="d_cur")
        with c2:
            du = st.selectbox("Хто", list(USERS.keys()), format_func=lambda x:USERS[x]["name"], key="d_usr")
            ddu = st.text_input("Дедлайн (РРРР-ММ-ДД)", key="d_due")
            dn = st.text_input("Примітка", key="d_note")
        if st.button("💾 Додати борг", key="d_add"):
            if dl and da>0:
                data["debts"].append({"id":uid(),"dir":dd,"label":dl,"amount":da,"currency":dc,"paid":0,"due":ddu,"note":dn,"user":du})
                save_data(data); st.success("Додано!"); st.rerun()

# ── SAVINGS / INVESTMENTS ─────────────────────────────────────────────────────
def page_savings(data, user):
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:26px;font-weight:800;margin-bottom:20px">📈 Інвестиції та заощадження</p>', unsafe_allow_html=True)

    if "instrument_rates" not in data:
        data["instrument_rates"] = {i["id"]:i["rate"] for i in INSTRUMENTS}
    rates = data["instrument_rates"]

    savs = data["savings"] if user=="family" else [s for s in data["savings"] if s.get("user","family") in (user,"family")]
    by_i = {}
    for s in savs:
        if s["instrument"] not in by_i: by_i[s["instrument"]]={"uah":0,"items":[]}
        by_i[s["instrument"]]["uah"] += to_uah(s["amount"],s["currency"])
        by_i[s["instrument"]]["items"].append(s)

    total_uah = sum(v["uah"] for v in by_i.values())
    total_usd = total_uah/USD
    w_rate = sum((by_i.get(i["id"],{}).get("uah",0)/USD)*rates.get(i["id"],i["rate"]) for i in INSTRUMENTS)/total_usd if total_usd>0 else 0
    annual_usd = total_usd*(w_rate/100)

    total_div = sum(s.get("dividends_received",0) for s in savs)
    total_growth = sum(by_i.get(iid,{}).get("uah",0)/USD * (s.get("price_growth_pct",0)/100)
                       for iid,v in by_i.items() for s in v["items"])

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💼 Портфель",       f"${round(total_usd):,}", fmt(total_uah))
    c2.metric("📊 Сер. дохідність", f"{w_rate:.1f}%",        "річних у $")
    c3.metric("💰 Дохід/рік",       f"${round(annual_usd):,}", "прогноз")
    c4.metric("🎁 Дивіденди отримано", fmt(total_div),        "всього")

    if by_i:
        pie_l=[INSTR_MAP.get(k,{}).get("label",k) for k in by_i]
        pie_v=[v["uah"]/USD for v in by_i.values()]
        pie_c=[INSTR_MAP.get(k,{}).get("color","#888") for k in by_i]
        fig=go.Figure(go.Pie(labels=pie_l,values=pie_v,hole=0.55,marker_colors=pie_c,
                             textinfo="percent+label",textfont_size=10,
                             hovertemplate="%{label}: $%{value:,.0f}<extra></extra>"))
        apply_theme(fig,"Розподіл портфелю ($)",260); fig.update_layout(showlegend=False)
        st.plotly_chart(fig,use_container_width=True)

    st.markdown("---")

    # ── Editable rate per instrument ──
    with st.expander("⚙️ Редагувати ставки по інструментах"):
        st.markdown('<p style="font-size:12px;color:#6b6b90;margin-bottom:12px">Змінюй актуальні відсоткові ставки — вони впливають на прогнози дохідності</p>', unsafe_allow_html=True)
        r_cols = st.columns(3)
        rate_updated = False
        for idx, inst in enumerate(INSTRUMENTS):
            with r_cols[idx % 3]:
                new_r = st.number_input(f"{inst['icon']} {inst['label']}", value=float(rates.get(inst["id"],inst["rate"])),
                                        min_value=0.0, max_value=100.0, step=0.5, key=f"rate_{inst['id']}")
                if new_r != rates.get(inst["id"],inst["rate"]):
                    rates[inst["id"]] = new_r; rate_updated = True
        if rate_updated: data["instrument_rates"]=rates; save_data(data); st.success("Ставки оновлено!")

    st.markdown("---")

    # ── Instruments ──
    for inst in INSTRUMENTS:
        d = by_i.get(inst["id"])
        usd = (d["uah"]/USD) if d else 0
        rate = rates.get(inst["id"], inst["rate"])
        ann  = usd*(rate/100)
        share= round(usd/total_usd*100) if total_usd>0 else 0
        total_div_inst = sum(s.get("dividends_received",0) for s in (d["items"] if d else []))
        avg_growth = sum(s.get("price_growth_pct",0) for s in (d["items"] if d else []))/len(d["items"]) if d and d["items"] else 0

        with st.expander(f"{inst['icon']} {inst['label']} — ${round(usd):,} · {rate}% річних"):
            if usd > 0:
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Сума", f"${round(usd):,}", fmt(d["uah"]))
                c2.metric("Дохід/рік", f"${round(ann):,}", f"{rate}% ставка")
                c3.metric("Дивіденди отримано", fmt(total_div_inst))
                c4.metric("Зростання ціни (сер.)", f"{avg_growth:.1f}%")
                progress_bar(share, inst["color"])
                st.markdown(f'<p style="font-size:11px;color:#6b6b90;margin:0 0 12px">{share}% портфелю</p>', unsafe_allow_html=True)

                for s in d["items"]:
                    st.markdown("---")
                    r1,r2,r3,r4 = st.columns([2,1.5,1.5,0.5])
                    with r1: st.markdown(f'<p style="font-size:12px;color:#6b6b90;margin:6px 0">{s["date"]} · {s["amount"]} {s["currency"]} · {s.get("note","")}</p>', unsafe_allow_html=True)
                    with r2:
                        new_div = st.number_input("Дивіденди отримано (₴)", value=float(s.get("dividends_received",0)), min_value=0.0, step=10.0, key=f"div_{s['id']}")
                        if new_div != s.get("dividends_received",0): s["dividends_received"]=new_div; save_data(data)
                    with r3:
                        new_gr = st.number_input("Зростання ціни (%)", value=float(s.get("price_growth_pct",0)), min_value=-100.0, max_value=500.0, step=0.5, key=f"gr_{s['id']}")
                        if new_gr != s.get("price_growth_pct",0): s["price_growth_pct"]=new_gr; save_data(data)
                    with r4:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"sav_del_{s['id']}", help="Видалити"):
                            data["savings"]=[x for x in data["savings"] if x["id"]!=s["id"]]
                            save_data(data); st.rerun()
            else:
                st.info("Немає позицій по цьому інструменту")

            st.markdown("---")
            cc1,cc2,cc3,cc4 = st.columns([2,1,1.5,1.5])
            with cc1: new_amt=st.number_input("Сума", min_value=0.0, step=100.0, key=f"si_{inst['id']}_a")
            with cc2: new_cur=st.selectbox("Валюта", ["₴","$"], key=f"si_{inst['id']}_c")
            with cc3: new_u=st.selectbox("Хто", list(USERS.keys()), format_func=lambda x:USERS[x]["name"], key=f"si_{inst['id']}_u")
            with cc4: new_n=st.text_input("Примітка", key=f"si_{inst['id']}_n")
            if st.button(f"➕ Поповнити {inst['label']}", key=f"si_{inst['id']}_add", use_container_width=True):
                if new_amt>0:
                    data["savings"].append({"id":uid(),"instrument":inst["id"],"amount":new_amt,"currency":new_cur,
                                            "date":TODAY,"note":new_n,"user":new_u,"dividends_received":0,"price_growth_pct":0})
                    save_data(data); st.success("Поповнено!"); st.rerun()

    # ── Risk matrix ──
    st.markdown("---")
    section_label("Матриця ризику та ліквідності")
    RISKS=[
        {"id":"inzhur_reit",  "risk":2,"liq":4,"desc":"Реальний досвід виводу протягом дня"},
        {"id":"binance_flex", "risk":3,"liq":5,"desc":"Платформний ризик, миттєвий вивід"},
        {"id":"inzhur_energy","risk":3,"liq":2,"desc":"Вищий % але нижча ліквідність"},
        {"id":"mono_jar",     "risk":1,"liq":5,"desc":"Мінімальний ризик, страхування НГФ"},
        {"id":"ovdp",         "risk":1,"liq":3,"desc":"Держгарантія, фіксований термін"},
    ]
    for r in RISKS:
        inst=INSTR_MAP.get(r["id"],{})
        rate=rates.get(r["id"],inst.get("rate",0))
        st.markdown(
            f'<div style="background:#0f0f1c;border:1px solid #1e1e3a;border-radius:12px;padding:14px 18px;margin-bottom:8px">'
            f'<div style="display:flex;align-items:center;gap:12px">'
            f'<span style="font-size:22px">{inst.get("icon","")}</span>'
            f'<div style="flex:1">'
            f'<p style="font-weight:600;font-size:13px;margin:0">{inst.get("label","")} <span style="color:{inst.get("color","")};margin-left:8px">{rate}% річних</span></p>'
            f'<p style="font-size:11px;color:#6b6b90;margin:2px 0 4px">{r["desc"]}</p>'
            f'<p style="font-size:12px;margin:0">Ризик: {"🔴"*r["risk"]}{"⚫"*(5-r["risk"])} &nbsp; Ліквідність: {"🟢"*r["liq"]}{"⚫"*(5-r["liq"])}</p>'
            f'</div></div></div>', unsafe_allow_html=True)

# ── GOALS ─────────────────────────────────────────────────────────────────────
def page_goals(data, user):
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:26px;font-weight:800;margin-bottom:20px">🎯 Фінансові цілі</p>', unsafe_allow_html=True)

    if "roadmap" not in data: data["roadmap"]=[]

    goals = data["goals"]
    total_pct = 0
    if goals:
        total_pct = round(sum(min(1,g["saved"]/g["target"]) if g["target"]>0 else 0 for g in goals)/len(goals)*100)
    done_count = sum(1 for g in goals if g["saved"]>=g["target"])

    hero_card(
        f'<p style="font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#6b6b90;margin:0 0 8px">Загальний прогрес цілей</p>'
        f'<p style="font-family:Unbounded,sans-serif;font-size:52px;font-weight:800;color:#a78bfa;margin:0 0 4px;letter-spacing:-.04em">{total_pct}%</p>'
        f'<p style="color:#6b6b90;font-size:13px;margin:0">{len(goals)} цілей · {done_count} виконано</p>'
    )
    progress_bar(total_pct, "#7B61FF", 8)

    # ── Goals list ──
    for g in list(goals):
        pct = min(100,round(g["saved"]/g["target"]*100)) if g["target"]>0 else 0
        done = pct>=100
        remaining = max(0,g["target"]-g["saved"])
        gid = g["id"]

        with st.expander(f"{g['icon']} {g['label']} — {pct}%  {'✅' if done else ''}", expanded=not done):
            col_prog, col_edit = st.columns([3,2])
            with col_prog:
                st.markdown(
                    f'<p style="font-size:13px;color:#6b6b90;margin:0 0 4px">'
                    f'Накопичено: <strong style="color:{g["color"]}">{fmt(g["saved"],g["currency"])}</strong> · '
                    f'Ціль: <strong>{fmt(g["target"],g["currency"])}</strong></p>', unsafe_allow_html=True)
                progress_bar(pct, g["color"], 10)
                st.markdown(
                    f'<p style="font-size:12px;color:#6b6b90;margin:4px 0 0">'
                    f'Залишилось: <strong style="color:{g["color"]}">{fmt(remaining,g["currency"])}</strong> · До: {g["deadline"]}</p>',
                    unsafe_allow_html=True)
            with col_edit:
                new_sav = st.number_input("Накопичено", value=float(g["saved"]),  min_value=0.0,  step=100.0, key=f"gs_{gid}_sav")
                new_tgt = st.number_input("Ціль",       value=float(g["target"]), min_value=1.0,  step=100.0, key=f"gs_{gid}_tgt")
                new_lbl = st.text_input("Назва",        value=g["label"],  key=f"gs_{gid}_lbl")
                ci,cc = st.columns(2)
                with ci: new_ico = st.text_input("Іконка", value=g["icon"],  key=f"gs_{gid}_ico")
                with cc: new_clr = st.color_picker("Колір", value=g["color"], key=f"gs_{gid}_clr")
                new_dl  = st.text_input("Дедлайн", value=g["deadline"], key=f"gs_{gid}_dl")
                new_cur = st.selectbox("Валюта", ["₴","$"], index=0 if g["currency"]=="₴" else 1, key=f"gs_{gid}_cur")
                cs,cd = st.columns(2)
                with cs:
                    if st.button("💾 Зберегти", key=f"gs_{gid}_save", use_container_width=True):
                        g.update({"saved":new_sav,"target":new_tgt,"label":new_lbl,"icon":new_ico,"color":new_clr,"deadline":new_dl,"currency":new_cur})
                        save_data(data); st.success("Збережено!"); st.rerun()
                with cd:
                    if st.button("🗑️ Видалити", key=f"gs_{gid}_del", use_container_width=True):
                        data["goals"]=[x for x in data["goals"] if x["id"]!=gid]
                        save_data(data); st.warning("Видалено!"); st.rerun()

    st.markdown("---")
    with st.expander("➕ Додати нову ціль"):
        c1,c2 = st.columns(2)
        with c1:
            ng_l = st.text_input("Назва цілі", key="ng_l")
            ng_t = st.number_input("Сума цілі", min_value=1.0, step=100.0, key="ng_t")
            ng_c = st.selectbox("Валюта", ["₴","$"], key="ng_c")
            ng_s = st.number_input("Вже накопичено", min_value=0.0, step=100.0, key="ng_s")
        with c2:
            ng_i  = st.text_input("Іконка", value="🎯", key="ng_i")
            ng_cl = st.color_picker("Колір", value="#7B61FF", key="ng_cl")
            ng_d  = st.text_input("Дедлайн (РРРР-ММ-ДД)", value="2027-12-01", key="ng_d")
        if st.button("✅ Створити ціль", use_container_width=True, key="ng_create"):
            if ng_l and ng_t>0:
                data["goals"].append({"id":uid(),"label":ng_l,"target":ng_t,"currency":ng_c,"icon":ng_i,"color":ng_cl,"deadline":ng_d,"saved":ng_s})
                save_data(data); st.success(f"Ціль додано!"); st.rerun()

    # ── Roadmap ──
    st.markdown("---")
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:20px;font-weight:800;margin-bottom:4px">🗺️ Дорожня карта</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b6b90;font-size:13px;margin-bottom:16px">Пересувай повзунок — виконані кроки підсвічуються</p>', unsafe_allow_html=True)

    plan_m = st.slider("Поточний місяць плану", 1, 60, 1, key="rm_slider")
    roadmap = sorted(data.get("roadmap",[]), key=lambda x:x["month"])

    if not roadmap: st.info("Дорожня карта порожня. Додай перший крок нижче.")

    for item in roadmap:
        done  = item["month"] <= plan_m
        color = "#7B61FF" if done else "#4a4880"
        bg    = rgba("#7B61FF",.13) if done else "#1e1e3a"
        tc    = "#f0efff" if done else "#6b6b90"
        glow  = f"0 0 12px {rgba('#7B61FF',.4)}" if done else "none"
        col_i, col_d = st.columns([7,1])
        with col_i:
            st.markdown(
                f'<div style="display:flex;gap:14px;padding:10px 0;border-bottom:1px solid #1e1e3a;align-items:center">'
                f'<div style="width:40px;height:40px;border-radius:50%;background:{bg};border:2px solid {color};'
                f'display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;box-shadow:{glow}">{item["icon"]}</div>'
                f'<div>'
                f'<p style="font-size:11px;color:{color};font-weight:700;letter-spacing:.08em;margin:0 0 2px">МІСЯЦЬ {item["month"]}</p>'
                f'<p style="font-size:13px;color:{tc};line-height:1.4;margin:0">{item["text"]}</p>'
                f'</div></div>', unsafe_allow_html=True)
        with col_d:
            st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"rd_{item['id']}", help="Видалити"):
                data["roadmap"]=[r for r in data["roadmap"] if r["id"]!=item["id"]]
                save_data(data); st.rerun()

    st.markdown("---")
    with st.expander("➕ Додати крок до дорожньої карти"):
        c1,c2,c3 = st.columns([1,1,3])
        with c1: rm_m=st.number_input("Місяць",min_value=1,max_value=120,value=1,key="rm_m")
        with c2: rm_i=st.text_input("Іконка",value="📌",key="rm_i")
        with c3: rm_t=st.text_input("Опис кроку",placeholder="Що має статись?",key="rm_t")
        if st.button("✅ Додати крок", use_container_width=True, key="rm_add"):
            if rm_t:
                data["roadmap"].append({"id":uid(),"month":rm_m,"icon":rm_i,"text":rm_t})
                save_data(data); st.success(f"Крок для місяця {rm_m} додано!"); st.rerun()

# ── ANALYTICS ─────────────────────────────────────────────────────────────────
def page_analytics(data, user):
    st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:26px;font-weight:800;margin-bottom:20px">🔍 Аналітика</p>', unsafe_allow_html=True)

    rows=[]
    for i in range(5,-1,-1):
        mo=CM-i; yr=CY
        if mo<0: mo+=12; yr-=1
        mk=f"{yr}-{str(mo+1).zfill(2)}"
        mi,me=month_stats(data,user,mk)
        rows.append({"m":SHORT_UA[mo],"Доходи":round(mi),"Витрати":round(me),"Заощадження":round(mi-me)})
    df=pd.DataFrame(rows)

    fig=go.Figure()
    fig.add_trace(go.Scatter(x=df["m"],y=df["Доходи"],fill="tozeroy",name="Доходи",
                             line=dict(color="#00D084",width=2),fillcolor=rgba("#00D084",.12)))
    fig.add_trace(go.Scatter(x=df["m"],y=df["Витрати"],fill="tozeroy",name="Витрати",
                             line=dict(color="#FF4757",width=2),fillcolor=rgba("#FF4757",.12)))
    fig.add_trace(go.Scatter(x=df["m"],y=df["Заощадження"],name="Заощадження",
                             line=dict(color="#7B61FF",width=2,dash="dot")))
    apply_theme(fig,"Рух коштів за 6 місяців (₴)",300)
    st.plotly_chart(fig,use_container_width=True)

    col_l,col_r=st.columns(2)
    with col_l:
        by_u={}
        for t in filter_tx(data,"family",THIS_MONTH,"expense"):
            u=t.get("user","family"); by_u[u]=by_u.get(u,0)+to_uah(t["amount"],t["currency"])
        if by_u:
            fig2=go.Figure(go.Bar(
                x=[USERS.get(u,{}).get("name",u) for u in by_u],y=list(by_u.values()),
                marker_color=[USERS.get(u,{}).get("color","#888") for u in by_u]))
            apply_theme(fig2,"Витрати по членах сім'ї (цей міс., ₴)",240)
            st.plotly_chart(fig2,use_container_width=True)

    with col_r:
        sav_colors=["#7B61FF" if v>=0 else "#FF4757" for v in df["Заощадження"]]
        fig3=go.Figure(go.Bar(x=df["m"],y=df["Заощадження"],marker_color=sav_colors,name="Накопичення"))
        apply_theme(fig3,"Накопичення по місяцях (₴)",240)
        st.plotly_chart(fig3,use_container_width=True)

    st.markdown("---")
    all_exp=filter_tx(data,user,tx_type="expense")
    cig_t  =sum(to_uah(t["amount"],t["currency"]) for t in all_exp if t["cat"]=="cigs")
    auto_t =sum(to_uah(t["amount"],t["currency"]) for t in all_exp if t["cat"] in ("fuel","car"))
    subs_t =sum(to_uah(t["amount"],t["currency"]) for t in all_exp if t["cat"] in ("subs","mobile"))
    inc_t  =sum(to_uah(t["amount"],t["currency"]) for t in filter_tx(data,user,tx_type="income"))

    c1,c2,c3,c4=st.columns(4)
    c1.metric("🚬 Цигарки (всього)",        fmt(cig_t), "за весь час")
    c2.metric("🚗 Авто",                    fmt(auto_t),"пальне + ремонт")
    c3.metric("📱 Підписки + зв'язок",      fmt(subs_t),"за весь час")
    c4.metric("💰 Загальний дохід",         fmt(inc_t), "за весь час")

    st.markdown("---")
    st.markdown(
        f'<div style="background:#0d1a14;border:1px solid rgba(0,208,132,.2);border-radius:14px;padding:18px">'
        f'<p style="font-weight:700;font-size:15px;color:#00D084;margin:0 0 12px">💡 Якби кинути цигарки...</p>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:16px">'
        f'<div><p style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:0 0 4px">Економія/міс</p><p style="font-size:18px;font-weight:700;color:#00D084;margin:0">{fmt(4800)}</p></div>'
        f'<div><p style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:0 0 4px">Економія/рік</p><p style="font-size:18px;font-weight:700;color:#00D084;margin:0">{fmt(57600)}</p></div>'
        f'<div><p style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:0 0 4px">За 2 роки ($)</p><p style="font-size:18px;font-weight:700;color:#00D084;margin:0">${round(57600*2/USD):,}</p></div>'
        f'<div><p style="font-size:10px;color:#6b6b9088;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:0 0 4px">Ремонт швидше</p><p style="font-size:18px;font-weight:700;color:#00D084;margin:0">~6 міс.</p></div>'
        f'</div></div>', unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    inject_css()
    if "data" not in st.session_state:
        st.session_state.data = load_data()
    data = st.session_state.data

    with st.sidebar:
        st.markdown('<p style="font-family:Unbounded,sans-serif;font-size:22px;font-weight:800;margin-bottom:4px"><span style="color:#a78bfa">Wallet</span>UA</p>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:11px;color:#4a4880;margin-bottom:20px">Сімейний бюджет</p>', unsafe_allow_html=True)

        st.markdown('<p style="font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4a4880;margin-bottom:8px">ПЕРЕГЛЯДАЄ</p>', unsafe_allow_html=True)
        user = st.radio("", list(USERS.keys()), format_func=lambda x:USERS[x]["name"], label_visibility="collapsed")

        st.markdown("---")
        st.markdown('<p style="font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4a4880;margin-bottom:8px">НАВІГАЦІЯ</p>', unsafe_allow_html=True)

        PAGES=[("dashboard","⚡ Головна"),("accounts","💳 Рахунки"),("transactions","📋 Операції"),
               ("budget","📊 Бюджет"),("debts","🔴 Борги"),("savings","📈 Інвестиції"),
               ("goals","🎯 Цілі"),("analytics","🔍 Аналітика")]

        if "page" not in st.session_state: st.session_state.page="dashboard"

        for pid,pname in PAGES:
            is_active = st.session_state.page==pid
            if st.button(pname, key=f"nav_{pid}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.page=pid; st.rerun()

        st.markdown("---")
        st.markdown(f'<p style="font-size:11px;color:#4a4880;text-align:center">1$ = {USD} ₴ · 1€ = {EUR} ₴<br><span style="color:#6b6b90">{MONTHS_UA[CM]} {CY}</span></p>', unsafe_allow_html=True)
        if st.button("🔄 Скинути дані", type="secondary", use_container_width=True):
            st.session_state.data=default_data(); save_data(st.session_state.data); st.rerun()

    page=st.session_state.get("page","dashboard")
    if page=="dashboard":    page_dashboard(data,user)
    elif page=="accounts":   page_accounts(data,user)
    elif page=="transactions":page_transactions(data,user)
    elif page=="budget":     page_budget(data,user)
    elif page=="debts":      page_debts(data,user)
    elif page=="savings":    page_savings(data,user)
    elif page=="goals":      page_goals(data,user)
    elif page=="analytics":  page_analytics(data,user)

    save_data(st.session_state.data)

if __name__=="__main__":
    main()