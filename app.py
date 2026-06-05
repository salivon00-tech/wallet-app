import streamlit as st
import json, os
from datetime import datetime
from uuid import uuid4
import plotly.graph_objects as go
import pandas as pd

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="WalletUA 💸", page_icon="💸", layout="wide")

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
USD, EUR = 44.38, 51.67
DATA_FILE = "wallet_data.json"
NOW = datetime.now()
CY, CM = NOW.year, NOW.month
TODAY = NOW.strftime("%Y-%m-%d")
CUR_MONTH = f"{CY}-{str(CM).zfill(2)}"
MONTHS_UA = ["Січ","Лют","Бер","Кві","Тра","Чер","Лип","Сер","Вер","Жов","Лис","Гру"]
MONTHS_FULL = ["Січень","Лютий","Березень","Квітень","Травень","Червень","Липень","Серпень","Вересень","Жовтень","Листопад","Грудень"]
USERS = ["Назар", "Дружина", "Спільне"]
USER_ICONS = {"Назар":"👨","Дружина":"👩","Спільне":"👨‍👩‍👧"}
USER_COLORS = {"Назар":"#7B61FF","Дружина":"#ec4899","Спільне":"#00D084"}

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
    {"id":"rent",     "label":"Оренда",             "icon":"🏠","color":"#FF4757","budget":13314},
    {"id":"mortgage", "label":"Іпотека",             "icon":"🏦","color":"#ff6b81","budget":8000},
    {"id":"utils",    "label":"Комуналка",           "icon":"💡","color":"#ffa502","budget":2000},
    {"id":"food",     "label":"Продукти",            "icon":"🛒","color":"#84cc16","budget":5000},
    {"id":"cafe",     "label":"Кафе/Ресторани",      "icon":"☕","color":"#22c55e","budget":1500},
    {"id":"child",    "label":"Дитяче",              "icon":"👶","color":"#06b6d4","budget":2000},
    {"id":"fuel",     "label":"Пальне",              "icon":"⛽","color":"#3b82f6","budget":2000},
    {"id":"car",      "label":"Ремонт авто",         "icon":"🔧","color":"#6366f1","budget":1000},
    {"id":"mobile",   "label":"Мобільний зв'язок",   "icon":"📞","color":"#a855f7","budget":850},
    {"id":"subs",     "label":"Підписки",            "icon":"📱","color":"#8b5cf6","budget":1641},
    {"id":"cigs",     "label":"Цигарки",             "icon":"🚬","color":"#ec4899","budget":4800},
    {"id":"clothes",  "label":"Одяг",                "icon":"👕","color":"#f43f5e","budget":1000},
    {"id":"health",   "label":"Здоров'я",            "icon":"💊","color":"#14b8a6","budget":500},
    {"id":"entertain","label":"Розваги",             "icon":"🎮","color":"#f59e0b","budget":500},
    {"id":"edu",      "label":"Освіта",              "icon":"📚","color":"#0ea5e9","budget":0},
    {"id":"gifts",    "label":"Подарунки",           "icon":"🎀","color":"#e879f9","budget":0},
    {"id":"travel",   "label":"Подорожі",            "icon":"✈️","color":"#38bdf8","budget":0},
    {"id":"other_e",  "label":"Інше",                "icon":"💸","color":"#6b7280","budget":1000},
]
ALL_CATS = INC_CATS + EXP_CATS

INSTRUMENTS = [
    {"id":"inzhur_reit",   "label":"Inzhur REIT",          "icon":"🏪","color":"#7B61FF","rate":9.5, "cur":"$"},
    {"id":"inzhur_energy", "label":"Inzhur Energy",         "icon":"⚡","color":"#ffa502","rate":15,  "cur":"$"},
    {"id":"binance_flex",  "label":"Binance Earn Flexible", "icon":"🟡","color":"#f0b90b","rate":6,   "cur":"$"},
    {"id":"mono_jar",      "label":"Monobank Скарбничка",   "icon":"🐱","color":"#34d399","rate":13,  "cur":"₴"},
    {"id":"ovdp",          "label":"ОВДП",                  "icon":"📜","color":"#60a5fa","rate":17,  "cur":"₴"},
    {"id":"other_sav",     "label":"Інше",                  "icon":"💼","color":"#6b7280","rate":0,   "cur":"₴"},
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def uid(): return str(uuid4())[:8]
def to_uah(a, c): return a*USD if c=="$" else a*EUR if c=="€" else a
def cat_by_id(cid):
    for c in ALL_CATS:
        if c["id"]==cid: return c
    return {"id":cid,"label":cid,"icon":"❓","color":"#888","budget":0}
def instr_by_id(iid):
    for i in INSTRUMENTS:
        if i["id"]==iid: return i
    return INSTRUMENTS[-1]
def fmt(n, cur="₴", short=False):
    n = abs(float(n or 0))
    if short and n>=1000000: s=f"{n/1000000:.1f}M"
    elif short and n>=1000: s=f"{n/1000:.1f}K"
    else: s=f"{n:,.0f}".replace(",","_").replace(".",",").replace("_"," ")
    return f"${s}" if cur=="$" else f"€{s}" if cur=="€" else f"{s} ₴"

def user_filter(items, user):
    if user=="Сім'я": return items
    return [i for i in items if i.get("user")==user or i.get("user")=="Спільне"]

PLOT_L = dict(
    paper_bgcolor="#06060f", plot_bgcolor="#06060f",
    font=dict(family="Inter",color="#9896c8",size=11),
    margin=dict(l=10,r=10,t=10,b=10),
    xaxis=dict(showgrid=False,zeroline=False,color="#4a4880"),
    yaxis=dict(showgrid=True,gridcolor="#1e1e3a",zeroline=False,color="#4a4880"),
)

# ── DATA ──────────────────────────────────────────────────────────────────────
def make_init():
    return {
        "accounts":[
            {"id":"mono",     "name":"Monobank",   "type":"card",  "currency":"₴","balance":4200, "icon":"🐱","user":"Назар",  "note":"Чорна картка"},
            {"id":"privat",   "name":"ПриватБанк", "type":"card",  "currency":"₴","balance":1850, "icon":"🏦","user":"Назар",  "note":""},
            {"id":"cash",     "name":"Готівка",     "type":"cash",  "currency":"₴","balance":3500, "icon":"💵","user":"Спільне","note":""},
            {"id":"binance",  "name":"Binance",     "type":"crypto","currency":"$","balance":68,   "icon":"🟡","user":"Назар",  "note":"Earn Flexible"},
            {"id":"wife_mono","name":"Monobank",    "type":"card",  "currency":"₴","balance":2100, "icon":"🐱","user":"Дружина","note":""},
        ],
        "transactions":[
            {"id":uid(),"type":"income", "cat":"salary",  "acc":"mono",     "amount":35000,"currency":"₴","note":"Зарплата",          "date":f"{CY}-06-01","user":"Назар"},
            {"id":uid(),"type":"income", "cat":"housing", "acc":"mono",     "amount":2300, "currency":"₴","note":"Компенсація найму",   "date":f"{CY}-06-01","user":"Назар"},
            {"id":uid(),"type":"income", "cat":"parents", "acc":"cash",     "amount":100,  "currency":"$","note":"Батьки",             "date":f"{CY}-06-02","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"rent",    "acc":"mono",     "amount":300,  "currency":"$","note":"Оренда червень",      "date":f"{CY}-06-03","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"utils",   "acc":"mono",     "amount":1800, "currency":"₴","note":"Комуналка",           "date":f"{CY}-06-05","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"mobile",  "acc":"mono",     "amount":450,  "currency":"₴","note":"Київстар",            "date":f"{CY}-06-05","user":"Назар"},
            {"id":uid(),"type":"expense","cat":"mobile",  "acc":"wife_mono","amount":400,  "currency":"₴","note":"Київстар",            "date":f"{CY}-06-05","user":"Дружина"},
            {"id":uid(),"type":"expense","cat":"subs",    "acc":"mono",     "amount":1641, "currency":"₴","note":"Netflix+YT+iCloud+G1","date":f"{CY}-06-05","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"food",    "acc":"privat",   "amount":3800, "currency":"₴","note":"Сільпо + Новус",      "date":f"{CY}-06-10","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"cigs",    "acc":"cash",     "amount":4800, "currency":"₴","note":"Цигарки",             "date":f"{CY}-06-15","user":"Назар"},
            {"id":uid(),"type":"expense","cat":"child",   "acc":"mono",     "amount":1500, "currency":"₴","note":"Дитячі витрати",      "date":f"{CY}-06-12","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"fuel",    "acc":"cash",     "amount":1800, "currency":"₴","note":"Пальне Audi",         "date":f"{CY}-06-14","user":"Назар"},
            {"id":uid(),"type":"income", "cat":"salary",  "acc":"mono",     "amount":35000,"currency":"₴","note":"Зарплата травень",    "date":f"{CY}-05-01","user":"Назар"},
            {"id":uid(),"type":"income", "cat":"housing", "acc":"mono",     "amount":2300, "currency":"₴","note":"Компенсація",          "date":f"{CY}-05-01","user":"Назар"},
            {"id":uid(),"type":"expense","cat":"rent",    "acc":"mono",     "amount":300,  "currency":"$","note":"Оренда",              "date":f"{CY}-05-03","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"utils",   "acc":"mono",     "amount":2100, "currency":"₴","note":"Комуналка",           "date":f"{CY}-05-05","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"cigs",    "acc":"cash",     "amount":4800, "currency":"₴","note":"Цигарки",             "date":f"{CY}-05-15","user":"Назар"},
            {"id":uid(),"type":"expense","cat":"food",    "acc":"privat",   "amount":4200, "currency":"₴","note":"Продукти",            "date":f"{CY}-05-10","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"car",     "acc":"cash",     "amount":3200, "currency":"₴","note":"Ремонт Audi",         "date":f"{CY}-05-20","user":"Назар"},
            {"id":uid(),"type":"expense","cat":"fuel",    "acc":"cash",     "amount":1900, "currency":"₴","note":"Пальне",              "date":f"{CY}-05-14","user":"Назар"},
        ],
        "debts":[
            {"id":uid(),"dir":"owe", "label":"Кредитна картка","amount":12260,"currency":"₴","dueDate":"","note":"Monobank кредитка","paid":0,"user":"Назар"},
            {"id":uid(),"dir":"owe", "label":"Іпотека єОселя", "amount":8000, "currency":"₴","dueDate":"","note":"Щомісячний платіж", "paid":0,"user":"Спільне"},
            {"id":uid(),"dir":"owed","label":"Весільні кошти", "amount":2000, "currency":"$","dueDate":"","note":"Повернути",          "paid":0,"user":"Спільне"},
        ],
        "savings":[
            {"id":uid(),"instrument":"inzhur_reit",  "amount":2150,"currency":"₴","date":f"{CY}-01-01","note":"Початкова позиція","user":"Назар"},
            {"id":uid(),"instrument":"binance_flex", "amount":68,  "currency":"$","date":f"{CY}-03-01","note":"Earn USDT",         "user":"Назар"},
        ],
        "goals":[
            {"id":"credit", "label":"Закрити кредитку","target":12260,"currency":"₴","icon":"💳","color":"#FF4757","deadline":"2026-07-01","saved":0},
            {"id":"cashpad","label":"Швидка каса",      "target":20000,"currency":"₴","icon":"🚨","color":"#ffa502","deadline":"2026-12-01","saved":0},
            {"id":"wedding","label":"Весільні кошти",   "target":2000, "currency":"$","icon":"💍","color":"#8b5cf6","deadline":"2027-06-01","saved":0},
            {"id":"cushion","label":"Подушка сім'ї",    "target":1500, "currency":"$","icon":"🛡","color":"#3b82f6","deadline":"2027-09-01","saved":0},
            {"id":"repair", "label":"Ремонт квартири",  "target":3000, "currency":"$","icon":"🏠","color":"#00D084","deadline":"2028-12-01","saved":0},
        ],
        "budgets":{c["id"]:c["budget"] for c in EXP_CATS},
    }

def load_data():
    if "data" not in st.session_state:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, encoding="utf-8") as f:
                    st.session_state.data = json.load(f)
            except Exception:
                st.session_state.data = make_init()
        else:
            st.session_state.data = make_init()

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def D(): return st.session_state.data

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@400;600;800&family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[data-testid="stAppViewContainer"]{background:#06060f!important;font-family:'Inter',sans-serif!important}
[data-testid="stAppViewContainer"]>.main{background:#06060f!important}
[data-testid="stSidebar"]{background:#0d0d1c!important;border-right:1px solid #1e1e3a!important}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label{color:#e8e6f5!important}
#MainMenu,footer,header,.stDeployButton{visibility:hidden}
.stTabs [data-baseweb="tab-list"]{background:#0d0d1c;border-radius:12px;padding:4px;border:1px solid #1e1e3a;gap:4px}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:8px;color:#6b6b90!important;font-weight:600;font-size:13px;padding:8px 14px;border:none!important}
.stTabs [aria-selected="true"]{background:#7B61FF!important;color:white!important}
.stTabs [data-baseweb="tab-panel"]{padding-top:20px}
.stTextInput input,.stNumberInput input,.stDateInput input,.stTextArea textarea{background:#131327!important;border:1px solid #1e1e3a!important;border-radius:10px!important;color:#e8e6f5!important;font-family:'Inter',sans-serif!important}
.stSelectbox>div>div{background:#131327!important;border:1px solid #1e1e3a!important;border-radius:10px!important;color:#e8e6f5!important}
.stButton>button{background:#7B61FF!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:600!important;font-family:'Inter',sans-serif!important}
.stButton>button:hover{background:#8a73ff!important;box-shadow:0 4px 20px #7B61FF44!important}
[data-testid="metric-container"]{background:#0d0d1c;border:1px solid #1e1e3a;border-radius:14px;padding:16px}
[data-testid="metric-container"] label{color:#6b6b90!important;font-size:11px!important;font-weight:600!important;letter-spacing:.1em!important;text-transform:uppercase!important}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#e8e6f5!important;font-family:'Unbounded',sans-serif!important;font-size:22px!important}
.streamlit-expanderHeader{background:#0d0d1c!important;border:1px solid #1e1e3a!important;border-radius:10px!important;color:#e8e6f5!important}
.streamlit-expanderContent{background:#0d0d1c!important;border:1px solid #1e1e3a!important;border-top:none!important}
[data-testid="stForm"]{background:#0d0d1c;border:1px solid #1e1e3a;border-radius:14px;padding:20px}
.stRadio [data-testid="stWidgetLabel"] p{color:#9896c8!important;font-size:11px!important;font-weight:600!important;letter-spacing:.1em!important;text-transform:uppercase!important}
.stRadio label{color:#e8e6f5!important}
hr{border-color:#1e1e3a!important}
p,span,div,h1,h2,h3{color:#e8e6f5}
.stSlider [data-baseweb="slider"]{background:#1e1e3a}
.wcard{background:#0d0d1c;border:1px solid #1e1e3a;border-radius:14px;padding:18px;margin-bottom:10px}
.wcard2{background:#131327;border:1px solid #1e1e3a;border-radius:10px;padding:14px;margin-bottom:8px}
.wtitle{font-family:'Unbounded',sans-serif;font-weight:800;color:#f0efff}
.wlabel{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4a4880;margin-bottom:8px}
.wbig{font-family:'Unbounded',sans-serif;font-weight:800;font-size:28px;line-height:1.1}
.wmuted{color:#6b6b90!important;font-size:13px}
.wgreen{color:#00D084!important}
.wred{color:#FF4757!important}
.wpurp{color:#a78bfa!important}
.wyellow{color:#ffa502!important}
</style>""", unsafe_allow_html=True)

# ── UI COMPONENTS ─────────────────────────────────────────────────────────────
def mcard(label, val, sub=None, color="#a78bfa"):
    sub_h = f'<div class="wmuted" style="margin-top:4px;font-size:12px">{sub}</div>' if sub else ""
    st.markdown(f'<div class="wcard" style="text-align:center"><div class="wlabel">{label}</div><div class="wbig" style="color:{color}">{val}</div>{sub_h}</div>', unsafe_allow_html=True)

def pbar_html(pct, color, height=5):
    return f'<div style="background:#1e1e3a;border-radius:99px;height:{height}px;overflow:hidden"><div style="width:{pct}%;height:100%;background:{color};border-radius:99px;transition:width .5s"></div></div>'

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown('<div class="wtitle" style="font-size:22px;margin-bottom:2px">💸 WalletUA</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="wmuted" style="font-size:12px">1$ = {USD} ₴ &nbsp;·&nbsp; 1€ = {EUR} ₴</div>', unsafe_allow_html=True)
        st.markdown("---")
        sel = st.radio("👤 ПРОФІЛЬ", ["Сім'я 👨‍👩‍👧","Назар 👨","Дружина 👩"])
        user = {"Сім'я 👨‍👩‍👧":"Сім'я","Назар 👨":"Назар","Дружина 👩":"Дружина"}[sel]
        st.markdown("---")
        d = D()
        accs = user_filter(d["accounts"], user)
        total = sum(to_uah(a["balance"],a["currency"]) for a in accs)
        txs = user_filter(d["transactions"], user)
        mtxs = [t for t in txs if t["date"].startswith(CUR_MONTH)]
        inc = sum(to_uah(t["amount"],t["currency"]) for t in mtxs if t["type"]=="income")
        exp = sum(to_uah(t["amount"],t["currency"]) for t in mtxs if t["type"]=="expense")
        st.markdown(f'<div class="wlabel">Загальний баланс</div><div class="wbig wpurp">{fmt(total)}</div><div class="wmuted">≈ ${total/USD:,.0f} USD</div>', unsafe_allow_html=True)
        st.markdown("---")
        c1,c2 = st.columns(2)
        with c1: st.markdown(f'<div class="wlabel">Дохід</div><div style="color:#00D084;font-weight:700;font-size:16px">{fmt(inc,short=True)}</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="wlabel">Витрати</div><div style="color:#FF4757;font-weight:700;font-size:16px">{fmt(exp,short=True)}</div>', unsafe_allow_html=True)
        st.markdown("---")
        sav_rate = round((inc-exp)/inc*100) if inc>0 else 0
        color = "#00D084" if sav_rate>=20 else "#ffa502" if sav_rate>=0 else "#FF4757"
        st.markdown(f'<div class="wlabel">Норма заощаджень</div><div style="font-family:Unbounded;font-size:24px;font-weight:800;color:{color}">{sav_rate}%</div>', unsafe_allow_html=True)
        st.markdown(pbar_html(max(0,min(100,sav_rate)), color, 4), unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<div class="wmuted" style="font-size:11px">💾 Дані зберігаються у wallet_data.json</div>', unsafe_allow_html=True)
        return user

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def tab_dashboard(user):
    d = D()
    txs = user_filter(d["transactions"], user)
    accs = user_filter(d["accounts"], user)
    mtxs = [t for t in txs if t["date"].startswith(CUR_MONTH)]
    inc  = sum(to_uah(t["amount"],t["currency"]) for t in mtxs if t["type"]=="income")
    exp  = sum(to_uah(t["amount"],t["currency"]) for t in mtxs if t["type"]=="expense")
    net  = inc-exp
    worth = sum(to_uah(a["balance"],a["currency"]) for a in accs)
    total_debt = sum(to_uah(db["amount"]-db["paid"],db["currency"]) for db in user_filter(d["debts"],user) if db["dir"]=="owe")

    st.markdown(f'''<div class="wcard" style="background:linear-gradient(135deg,#0f0a2e,#1a1050,#0a0a1e);border-color:#7B61FF33">
        <div class="wlabel">Загальний капітал</div>
        <div class="wbig" style="font-size:34px;margin-bottom:4px">{fmt(worth)}</div>
        <div class="wmuted">≈ ${worth/USD:,.0f} USD</div>
        <div style="display:flex;gap:24px;margin-top:16px">
            <div><div class="wlabel">Доходи/міс</div><div class="wgreen" style="font-weight:700;font-size:16px">{fmt(inc,short=True)}</div></div>
            <div><div class="wlabel">Витрати/міс</div><div class="wred" style="font-weight:700;font-size:16px">{fmt(exp,short=True)}</div></div>
            <div><div class="wlabel">Борги</div><div class="wyellow" style="font-weight:700;font-size:16px">{fmt(total_debt,short=True)}</div></div>
        </div>
    </div>''', unsafe_allow_html=True)

    # Last 6 months chart
    mdata = []
    for i in range(5,-1,-1):
        mo=CM-i; yr=CY
        while mo<=0: mo+=12; yr-=1
        k=f"{yr}-{str(mo).zfill(2)}"
        mi=sum(to_uah(t["amount"],t["currency"]) for t in txs if t["type"]=="income" and t["date"].startswith(k))
        me=sum(to_uah(t["amount"],t["currency"]) for t in txs if t["type"]=="expense" and t["date"].startswith(k))
        mdata.append({"m":MONTHS_UA[mo-1],"inc":mi,"exp":me})
    df = pd.DataFrame(mdata)
    fig = go.Figure()
    fig.add_bar(x=df["m"],y=df["inc"],name="Дохід",marker_color="#00D08455",marker_line_width=0)
    fig.add_bar(x=df["m"],y=df["exp"],name="Витрати",marker_color="#FF475755",marker_line_width=0)
    fig.update_layout(**PLOT_L,barmode="group",height=170,showlegend=True,legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#9896c8")))
    st.markdown('<div class="wcard"><div class="wlabel">Доходи vs Витрати (₴)</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    col1,col2 = st.columns(2)
    # Top expenses
    with col1:
        exp_by_cat={}
        for t in mtxs:
            if t["type"]=="expense": exp_by_cat[t["cat"]]=exp_by_cat.get(t["cat"],0)+to_uah(t["amount"],t["currency"])
        top=sorted(exp_by_cat.items(),key=lambda x:-x[1])[:5]
        maxv=top[0][1] if top else 1
        st.markdown('<div class="wcard"><div class="wlabel">Топ витрат цього місяця</div>', unsafe_allow_html=True)
        for cid,val in top:
            c=cat_by_id(cid); pct=int(val/maxv*100)
            st.markdown(f'''<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
                <span style="font-size:16px">{c["icon"]}</span>
                <div style="flex:1"><div style="font-size:12px;font-weight:500;margin-bottom:3px">{c["label"]}</div>
                {pbar_html(pct,c["color"],3)}</div>
                <div style="font-size:12px;color:#9896c8;white-space:nowrap">{fmt(val)}</div>
            </div>''', unsafe_allow_html=True)
        if not top: st.markdown('<div class="wmuted">Немає витрат</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Recent transactions
    with col2:
        recent=sorted(txs,key=lambda t:t["date"],reverse=True)[:5]
        st.markdown('<div class="wcard"><div class="wlabel">Останні операції</div>', unsafe_allow_html=True)
        for t in recent:
            c=cat_by_id(t["cat"])
            sign="+"; color="#00D084"
            if t["type"]=="expense": sign="−"; color="#FF4757"
            ui=USER_ICONS.get(t.get("user",""),"")
            st.markdown(f'''<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
                <div style="width:34px;height:34px;border-radius:9px;background:{c["color"]}22;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">{c["icon"]}</div>
                <div style="flex:1"><div style="font-size:12px;font-weight:500">{c["label"]} {ui}</div>
                <div style="font-size:11px;color:#6b6b90">{t["date"][5:]}{" · "+t["note"] if t["note"] else ""}</div></div>
                <div style="font-weight:700;font-size:13px;color:{color}">{sign}{t["amount"]}{t["currency"]}</div>
            </div>''', unsafe_allow_html=True)
        if not recent: st.markdown('<div class="wmuted">Немає операцій</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Goals
    st.markdown('<div class="wcard"><div class="wlabel">Фінансові цілі</div>', unsafe_allow_html=True)
    for g in d["goals"]:
        pct=min(100,round(g["saved"]/g["target"]*100)) if g["target"]>0 else 0
        st.markdown(f'''<div style="margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                <span style="font-size:12px;font-weight:500">{g["icon"]} {g["label"]}</span>
                <span style="font-size:12px;color:#9896c8">{pct}%</span>
            </div>{pbar_html(pct,g["color"],5)}</div>''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── ACCOUNTS ──────────────────────────────────────────────────────────────────
def tab_accounts(user):
    d = D()
    accs = user_filter(d["accounts"], user)
    total = sum(to_uah(a["balance"],a["currency"]) for a in accs)
    mcard("Загальний баланс", fmt(total), f"≈ ${total/USD:,.0f} · €{total/EUR:,.0f}", "#a78bfa")

    with st.expander("➕ Додати рахунок"):
        with st.form("add_acc"):
            c1,c2,c3 = st.columns(3)
            with c1: name=st.text_input("Назва")
            with c2: atype=st.selectbox("Тип",["card","cash","crypto","savings"])
            with c3: icon=st.text_input("Іконка","💳")
            c4,c5,c6,c7 = st.columns(4)
            with c4: bal=st.number_input("Баланс",value=0.0)
            with c5: cur=st.selectbox("Валюта",["₴","$","€"])
            with c6: auser=st.selectbox("Власник",USERS)
            with c7: note=st.text_input("Примітка")
            if st.form_submit_button("Додати"):
                d["accounts"].append({"id":uid(),"name":name,"type":atype,"currency":cur,"balance":bal,"icon":icon,"user":auser,"note":note})
                save_data(); st.rerun()

    GRAD={"card":"linear-gradient(135deg,#1a1a40,#2d1f6e)","cash":"linear-gradient(135deg,#0d2818,#1a5c30)","crypto":"linear-gradient(135deg,#2a1f00,#5a3d00)","savings":"linear-gradient(135deg,#0d1a2e,#1a3a5c)"}
    for a in accs:
        uah_v=to_uah(a["balance"],a["currency"])
        ub=f'<span style="font-size:11px;background:#1e1e3a;padding:2px 8px;border-radius:99px">{USER_ICONS.get(a.get("user",""),"")} {a.get("user","")}</span>'
        st.markdown(f'''<div style="background:{GRAD.get(a["type"],GRAD["card"])};border:1px solid #ffffff18;border-radius:18px;padding:22px;margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                    <div style="font-size:26px;margin-bottom:10px">{a["icon"]}</div>
                    <div style="font-family:Unbounded,sans-serif;font-size:22px;font-weight:800;margin-bottom:4px">{a["balance"]:,.0f} {a["currency"]}</div>
                    {f'<div style="font-size:12px;color:#ffffff66;margin-bottom:6px">≈ {fmt(uah_v)}</div>' if a["currency"]!="₴" else ""}
                    <div style="font-size:13px;color:#ffffffaa;font-weight:500">{a["name"]} {ub}</div>
                    {f'<div style="font-size:11px;color:#ffffff55;margin-top:2px">{a["note"]}</div>' if a["note"] else ""}
                </div>
                <span style="font-size:11px;color:#ffffff55;text-transform:uppercase;letter-spacing:.06em">{a["type"]}</span>
            </div>
        </div>''', unsafe_allow_html=True)
        c1,c2,c3 = st.columns([3,1,1])
        with c1: new_b=st.number_input(f"Баланс {a['name']}",value=float(a["balance"]),key=f"b_{a['id']}",label_visibility="collapsed")
        with c2:
            if st.button("💾 Оновити",key=f"u_{a['id']}"):
                for acc in d["accounts"]:
                    if acc["id"]==a["id"]: acc["balance"]=new_b
                save_data(); st.rerun()
        with c3:
            if st.button("🗑 Видалити",key=f"da_{a['id']}"):
                d["accounts"]=[x for x in d["accounts"] if x["id"]!=a["id"]]
                save_data(); st.rerun()

# ── TRANSACTIONS ──────────────────────────────────────────────────────────────
def tab_transactions(user):
    d = D()
    with st.expander("➕ Нова операція", expanded=False):
        with st.form("add_tx"):
            c1,c2 = st.columns(2)
            with c1: ttype=st.selectbox("Тип",["expense","income"],format_func=lambda x:"💸 Витрата" if x=="expense" else "💰 Дохід")
            with c2: tuser=st.selectbox("Хто",USERS,key="tu")
            cats=EXP_CATS if ttype=="expense" else INC_CATS
            c3,c4 = st.columns(2)
            with c3: tcat=st.selectbox("Категорія",[c["id"] for c in cats],format_func=lambda x:f'{cat_by_id(x)["icon"]} {cat_by_id(x)["label"]}')
            accs_opts={a["id"]:f'{a["icon"]} {a["name"]}' for a in d["accounts"]}
            with c4: tacc=st.selectbox("Рахунок",list(accs_opts.keys()),format_func=lambda x:accs_opts.get(x,x))
            c5,c6,c7,c8 = st.columns(4)
            with c5: tamount=st.number_input("Сума",min_value=0.0,value=0.0)
            with c6: tcur=st.selectbox("Валюта",["₴","$","€"])
            with c7: tdate=st.date_input("Дата")
            with c8: tnote=st.text_input("Примітка")
            if st.form_submit_button("✅ Додати"):
                d["transactions"].append({"id":uid(),"type":ttype,"cat":tcat,"acc":tacc,"amount":tamount,"currency":tcur,"note":tnote,"date":str(tdate),"user":tuser})
                save_data(); st.rerun()

    txs = user_filter(d["transactions"], user)
    c1,c2,c3 = st.columns(3)
    with c1: ftype=st.selectbox("Тип",["all","income","expense"],format_func=lambda x:{"all":"Всі","income":"Доходи","expense":"Витрати"}[x])
    with c2: fsearch=st.text_input("🔍 Пошук",placeholder="Примітка...")
    with c3: fmonth=st.text_input("Місяць (РРРР-ММ)",value=CUR_MONTH)

    filtered=[t for t in txs if
        (ftype=="all" or t["type"]==ftype) and
        (not fsearch or fsearch.lower() in (t.get("note","") or "").lower()) and
        (not fmonth or t["date"].startswith(fmonth))
    ]
    filtered=sorted(filtered,key=lambda t:t["date"],reverse=True)

    grouped={}
    for t in filtered: grouped.setdefault(t["date"][:7],[]).append(t)

    for mk in sorted(grouped.keys(),reverse=True):
        items=grouped[mk]; yr,mo=int(mk[:4]),int(mk[5:])
        mi=sum(to_uah(t["amount"],t["currency"]) for t in items if t["type"]=="income")
        me=sum(to_uah(t["amount"],t["currency"]) for t in items if t["type"]=="expense")
        st.markdown(f'''<div style="display:flex;justify-content:space-between;align-items:center;margin:16px 0 8px">
            <span style="font-family:Unbounded,sans-serif;font-size:14px;font-weight:600">{MONTHS_FULL[mo-1]} {yr}</span>
            <span style="font-size:12px"><span style="color:#00D084">+{fmt(mi)}</span> · <span style="color:#FF4757">-{fmt(me)}</span></span>
        </div>''', unsafe_allow_html=True)
        for t in items:
            c=cat_by_id(t["cat"]); sign="+"; color="#00D084"
            if t["type"]=="expense": sign="−"; color="#FF4757"
            ui=USER_ICONS.get(t.get("user",""),"")
            col1,col2 = st.columns([5,1])
            with col1:
                st.markdown(f'''<div class="wcard2" style="display:flex;align-items:center;gap:12px">
                    <div style="width:36px;height:36px;border-radius:9px;background:{c["color"]}22;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0">{c["icon"]}</div>
                    <div style="flex:1"><div style="font-size:13px;font-weight:500">{c["label"]} {ui}</div>
                    <div style="font-size:11px;color:#6b6b90">{t["date"]}{(" · "+t["note"]) if t["note"] else ""}</div></div>
                    <div style="text-align:right"><div style="font-weight:700;font-size:14px;color:{color}">{sign}{t["amount"]}{t["currency"]}</div>
                    {f'<div style="font-size:10px;color:#6b6b90">≈{fmt(to_uah(t["amount"],t["currency"]))}</div>' if t["currency"]!="₴" else ""}</div>
                </div>''', unsafe_allow_html=True)
            with col2:
                if st.button("🗑",key=f"dt_{t['id']}"):
                    d["transactions"]=[x for x in d["transactions"] if x["id"]!=t["id"]]
                    save_data(); st.rerun()
    if not filtered: st.markdown('<div style="text-align:center;padding:40px;color:#6b6b90">Немає операцій</div>', unsafe_allow_html=True)

# ── BUDGET ────────────────────────────────────────────────────────────────────
def tab_budget(user):
    d = D()
    txs = user_filter(d["transactions"], user)
    c1,_ = st.columns([1,2])
    with c1: bm=st.text_input("Місяць",value=CUR_MONTH,key="bm")
    mtxs=[t for t in txs if t["type"]=="expense" and t["date"].startswith(bm)]
    spent={}
    for t in mtxs: spent[t["cat"]]=spent.get(t["cat"],0)+to_uah(t["amount"],t["currency"])
    tb=sum(d["budgets"].get(c["id"],0) for c in EXP_CATS); ts=sum(spent.values())
    over=sum(1 for c in EXP_CATS if spent.get(c["id"],0)>d["budgets"].get(c["id"],0) and d["budgets"].get(c["id"],0)>0)
    c1,c2,c3=st.columns(3)
    with c1: mcard("Витрачено",fmt(ts),f"з {fmt(tb)} бюджету","#FF4757" if ts>tb else "#e8e6f5")
    with c2: mcard("Залишок",fmt(max(0,tb-ts)),"бюджету","#00D084")
    with c3: mcard("Перевищень",str(over),"категорій","#ffa502" if over>0 else "#00D084")

    pie=[{"label":cat_by_id(k)["label"],"v":v,"color":cat_by_id(k)["color"]} for k,v in spent.items() if v>0]
    if pie:
        fig=go.Figure(go.Pie(labels=[p["label"] for p in pie],values=[p["v"] for p in pie],hole=.45,marker_colors=[p["color"] for p in pie],textinfo="none",hovertemplate="%{label}: %{value:,.0f} ₴<extra></extra>"))
        fig.update_layout(**{**PLOT_L,"height":200})
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    st.markdown('<div class="wlabel" style="margin-top:8px">Категорії</div>', unsafe_allow_html=True)
    for c in EXP_CATS:
        s=spent.get(c["id"],0); b=d["budgets"].get(c["id"],0)
        pct=min(100,round(s/b*100)) if b>0 else 0; isover=s>b and b>0
        col1,col2,col3=st.columns([4,1,1])
        with col1:
            st.markdown(f'''<div style="margin-bottom:4px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                    <span style="font-size:13px">{c["icon"]} {c["label"]}</span>
                    <span style="font-size:12px;color:{"#FF4757" if isover else "#9896c8"}">{fmt(s)} / {fmt(b)}</span>
                </div>{pbar_html(pct,"#FF4757" if isover else c["color"],5)}
                {"<div style='font-size:11px;color:#FF4757;margin-top:2px'>⚠ Перевищено на "+fmt(s-b)+"</div>" if isover else ""}
            </div>''', unsafe_allow_html=True)
        with col2: new_b=st.number_input("₴",value=float(b),key=f"bg_{c['id']}",label_visibility="collapsed")
        with col3:
            if st.button("💾",key=f"sb_{c['id']}"):
                d["budgets"][c["id"]]=new_b; save_data(); st.rerun()

# ── DEBTS ─────────────────────────────────────────────────────────────────────
def tab_debts(user):
    d = D()
    with st.expander("➕ Додати борг"):
        with st.form("add_debt"):
            c1,c2=st.columns(2)
            with c1: ddir=st.selectbox("Тип",["owe","owed"],format_func=lambda x:"😟 Я винен" if x=="owe" else "😊 Мені винні")
            with c2: duser=st.selectbox("Хто",USERS,key="du")
            c3,c4=st.columns(2)
            with c3: dlabel=st.text_input("Назва / Кому")
            with c4: dnote=st.text_input("Примітка")
            c5,c6,c7=st.columns(3)
            with c5: damount=st.number_input("Сума",min_value=0.0)
            with c6: dcur=st.selectbox("Валюта",["₴","$","€"])
            with c7: ddue=st.text_input("Дедлайн")
            if st.form_submit_button("Додати"):
                d["debts"].append({"id":uid(),"dir":ddir,"label":dlabel,"amount":damount,"currency":dcur,"dueDate":ddue,"note":dnote,"paid":0,"user":duser})
                save_data(); st.rerun()

    debts=user_filter(d["debts"],user)
    owe=[x for x in debts if x["dir"]=="owe"]; owed=[x for x in debts if x["dir"]=="owed"]
    to_owe=sum(to_uah(x["amount"]-x["paid"],x["currency"]) for x in owe)
    to_owed=sum(to_uah(x["amount"]-x["paid"],x["currency"]) for x in owed)
    c1,c2=st.columns(2)
    with c1: st.markdown(f'<div class="wcard" style="text-align:center;border-color:#FF475730"><div class="wlabel">Я винен</div><div class="wbig wred">{fmt(to_owe)}</div><div class="wmuted">{len(owe)} боргів</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="wcard" style="text-align:center;border-color:#00D08430"><div class="wlabel">Мені винні</div><div class="wbig wgreen">{fmt(to_owed)}</div><div class="wmuted">{len(owed)} боргів</div></div>', unsafe_allow_html=True)

    def show_debt_list(items, title, color):
        if not items: return
        st.markdown(f'<div class="wlabel" style="margin:12px 0 8px">{title}</div>', unsafe_allow_html=True)
        for debt in items:
            rem=debt["amount"]-debt["paid"]; pct=min(100,round(debt["paid"]/debt["amount"]*100)) if debt["amount"]>0 else 0
            ui=USER_ICONS.get(debt.get("user",""),"")
            col1,col2,col3=st.columns([4,1,1])
            with col1:
                st.markdown(f'''<div class="wcard2" style="border-left:3px solid {color}">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
                        <div><div style="font-weight:600;font-size:14px">{debt["label"]} {ui}</div>
                        {f'<div style="font-size:11px;color:#9896c8">{debt["note"]}</div>' if debt["note"] else ""}
                        {f'<div style="font-size:11px;color:#ffa502">📅 {debt["dueDate"]}</div>' if debt["dueDate"] else ""}</div>
                        <div style="text-align:right"><div style="font-family:Unbounded,sans-serif;font-size:16px;font-weight:700;color:{color}">{rem:,.0f} {debt["currency"]}</div>
                        {f'<div style="font-size:11px;color:#9896c8">≈{fmt(to_uah(rem,debt["currency"]))}</div>' if debt["currency"]!="₴" else ""}</div>
                    </div>
                    {pbar_html(pct,color,5)}
                    <div style="font-size:11px;color:#9896c8;margin-top:4px">Сплачено: {pct}%</div>
                </div>''', unsafe_allow_html=True)
            with col2:
                np=st.number_input("Сплачено",value=float(debt["paid"]),key=f"p_{debt['id']}",label_visibility="collapsed")
                if np!=debt["paid"]:
                    for x in d["debts"]:
                        if x["id"]==debt["id"]: x["paid"]=np
                    save_data()
            with col3:
                if st.button("🗑",key=f"dd_{debt['id']}"):
                    d["debts"]=[x for x in d["debts"] if x["id"]!=debt["id"]]
                    save_data(); st.rerun()

    show_debt_list(owe,"😟 Я винен","#FF4757")
    show_debt_list(owed,"😊 Мені винні","#00D084")
    if not debts: st.markdown('<div style="text-align:center;padding:40px;color:#6b6b90">Немає боргів 🎉</div>', unsafe_allow_html=True)

# ── SAVINGS / INVESTMENTS ─────────────────────────────────────────────────────
def tab_savings(user):
    d = D()
    savs=user_filter(d["savings"],user)
    with st.expander("➕ Поповнити"):
        with st.form("add_sav"):
            c1,c2=st.columns(2)
            with c1: sinstr=st.selectbox("Інструмент",[i["id"] for i in INSTRUMENTS],format_func=lambda x:f'{instr_by_id(x)["icon"]} {instr_by_id(x)["label"]} ({instr_by_id(x)["rate"]}%)')
            with c2: suser=st.selectbox("Хто",USERS,key="su")
            c3,c4,c5=st.columns(3)
            with c3: samount=st.number_input("Сума",min_value=0.0)
            with c4: scur=st.selectbox("Валюта",["₴","$"])
            with c5: sdate=st.date_input("Дата",key="sd")
            snote=st.text_input("Примітка")
            if st.form_submit_button("Додати"):
                d["savings"].append({"id":uid(),"instrument":sinstr,"amount":samount,"currency":scur,"date":str(sdate),"note":snote,"user":suser})
                save_data(); st.rerun()

    by_i={}
    for s in savs:
        i=s["instrument"]; by_i.setdefault(i,{"uah":0,"items":[]})
        by_i[i]["uah"]+=to_uah(s["amount"],s["currency"]); by_i[i]["items"].append(s)
    tuah=sum(v["uah"] for v in by_i.values()); tusd=tuah/USD
    wrate=sum((by_i.get(i["id"],{"uah":0})["uah"]/USD)*i["rate"] for i in INSTRUMENTS)/tusd if tusd>0 else 0
    ann=tusd*(wrate/100)
    c1,c2,c3=st.columns(3)
    with c1: mcard("Портфель",f"${tusd:,.0f}",fmt(tuah),"#a78bfa")
    with c2: mcard("Сер. дохідність",f"{wrate:.1f}%","річних у $","#00D084")
    with c3: mcard("Дохід/рік",f"${ann:,.0f}","прогноз","#ffa502")

    for inst in INSTRUMENTS:
        data=by_i.get(inst["id"]); usd=(data["uah"] if data else 0)/USD
        share=round(usd/tusd*100) if tusd>0 else 0; ann_i=usd*(inst["rate"]/100)
        st.markdown(f'''<div class="wcard" style="border-left:3px solid {inst["color"]}">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:{"10px" if data else "0"}">
                <div style="width:42px;height:42px;border-radius:11px;background:{inst["color"]}22;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0">{inst["icon"]}</div>
                <div style="flex:1"><div style="font-weight:600;font-size:14px">{inst["label"]}</div>
                <div style="font-size:11px;color:#9896c8">{inst["rate"]}% річних · {inst["cur"]}</div></div>
                <div style="text-align:right"><div style="font-family:Unbounded,sans-serif;font-size:16px;font-weight:700;color:{inst["color"]}">${usd:,.0f}</div>
                {f'<div style="font-size:11px;color:#9896c8">+${ann_i:,.0f}/рік</div>' if ann_i>0 else ""}
                {f'<div style="font-size:10px;color:#9896c8">{share}% портфелю</div>' if share>0 else ""}</div>
            </div>
            {pbar_html(share,inst["color"],4) if data else ""}
        </div>''', unsafe_allow_html=True)
        if data:
            for s in data["items"]:
                col1,col2=st.columns([5,1])
                with col1:
                    ui=USER_ICONS.get(s.get("user",""),"")
                    st.markdown(f'<div style="font-size:12px;color:#9896c8;padding:4px 0 4px 16px;border-left:2px solid {inst["color"]}44">{s["date"]} {ui} {s.get("note","") or ""} · <b style="color:#e8e6f5">{s["amount"]} {s["currency"]}</b></div>', unsafe_allow_html=True)
                with col2:
                    if st.button("🗑",key=f"ds_{s['id']}"):
                        d["savings"]=[x for x in d["savings"] if x["id"]!=s["id"]]
                        save_data(); st.rerun()

    st.markdown("---")
    st.markdown('<div class="wlabel">Матриця ризиків</div>', unsafe_allow_html=True)
    for rid,risk,liq,desc in [("inzhur_reit",2,4,"Реальний досвід виводу за день"),("binance_flex",3,5,"Платформний ризик, миттєвий вивід"),("inzhur_energy",3,2,"15% але нижча ліквідність"),("mono_jar",1,5,"Мінімальний ризик, страхування НГФ"),("ovdp",1,3,"Держгарантія, фіксований термін")]:
        inst=instr_by_id(rid)
        st.markdown(f'''<div class="wcard2" style="margin-bottom:6px">
            <div style="display:flex;align-items:center;gap:10px">
                <span style="font-size:18px">{inst["icon"]}</span>
                <div style="flex:1"><div style="font-size:13px;font-weight:500">{inst["label"]}</div>
                <div style="font-size:11px;color:#9896c8">{desc}</div>
                <div style="font-size:12px;margin-top:4px">Ризик: {"🔴"*risk+"⚪"*(5-risk)} &nbsp; Ліквідність: {"🟢"*liq+"⚪"*(5-liq)}</div></div>
                <div style="font-family:Unbounded,sans-serif;font-size:14px;font-weight:700;color:{inst["color"]}">{inst["rate"]}%</div>
            </div>
        </div>''', unsafe_allow_html=True)

# ── GOALS ─────────────────────────────────────────────────────────────────────
def tab_goals(user):
    d = D()
    goals=d["goals"]
    parts=sum(min(g["saved"] if g["currency"]=="$" else g["saved"]/USD, g["target"] if g["currency"]=="$" else g["target"]/USD) for g in goals)
    total_t=sum(g["target"] if g["currency"]=="$" else g["target"]/USD for g in goals)
    overall=round(parts/total_t*100) if total_t>0 else 0

    st.markdown(f'''<div class="wcard" style="text-align:center;background:linear-gradient(135deg,#0f0a2e,#1a1050,#0a0a1e);border-color:#7B61FF33">
        <div class="wlabel">Загальний прогрес</div>
        <div class="wbig wpurp" style="font-size:52px">{overall}%</div>
        {pbar_html(overall,"linear-gradient(90deg,#7B61FF,#a78bfa,#00D084)",6)}
    </div>''', unsafe_allow_html=True)

    for g in goals:
        pct=min(100,round(g["saved"]/g["target"]*100)) if g["target"]>0 else 0
        done=pct>=100; rem=max(0,g["target"]-g["saved"])
        st.markdown(f'''<div class="wcard" style="border-color:{"#1e1e3a"}">
            <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:12px">
                <div style="width:46px;height:46px;border-radius:13px;background:{g["color"]}22;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0">{g["icon"]}</div>
                <div style="flex:1"><div style="font-weight:600;font-size:14px;color:{"#"+g["color"][1:] if done else "#f0efff"}">{"✓ " if done else ""}{g["label"]}</div>
                <div style="font-size:11px;color:#9896c8;margin-top:2px">До: {g["deadline"]}</div>
                {"" if done else f'<div style="font-size:12px;color:#9896c8;margin-top:4px">Залишилось: <b style="color:{g["color"]}">{rem:,.0f} {g["currency"]}</b></div>'}
                </div>
                <div style="font-family:Unbounded,sans-serif;font-size:22px;font-weight:800;color:{"#"+g["color"][1:] if done else "#a78bfa"}">{pct}%</div>
            </div>
            {pbar_html(pct,g["color"],6)}
        </div>''', unsafe_allow_html=True)
        col1,col2,col3=st.columns(3)
        with col1: ns=st.number_input("Накопичено",value=float(g["saved"]),key=f"gs_{g['id']}")
        with col2: nt=st.number_input("Ціль",value=float(g["target"]),key=f"gt_{g['id']}")
        with col3: nd=st.text_input("Дедлайн",value=g["deadline"],key=f"gd_{g['id']}")
        if st.button(f"💾 {g['label']}",key=f"sg_{g['id']}"):
            for gg in d["goals"]:
                if gg["id"]==g["id"]: gg["saved"]=ns; gg["target"]=nt; gg["deadline"]=nd
            save_data(); st.rerun()

    st.markdown("---")
    st.markdown('<div class="wlabel">🗺 Дорожня карта</div>', unsafe_allow_html=True)
    pm=st.slider("Поточний місяць плану",1,36,1)
    for month,icon,text in [(1,"💳","Закрити кредитку 12 260 ₴ одним платежем"),(2,"🚀","7 400 ₴ → Binance · 4 400 ₴ → Inzhur REIT · 3 200 ₴ → Monobank"),(6,"🚨","Швидка каса 20 000 ₴ набрана ✓"),(12,"💍","Весільні 2 000$ на Binance Flexible"),(15,"🛡","Подушка 1 500$ в Inzhur REIT"),(14,"🏗","8 000 ₴/міс ремонт + 4 000 ₴ → Inzhur Energy"),(30,"🏠","Ремонт готовий, квартира здається в оренду")]:
        done=month<=pm; c="#7B61FF" if done else "#1e1e3a"; tc="#f0efff" if done else "#6b6b90"
        st.markdown(f'<div style="display:flex;gap:14px;padding:10px 0;border-left:2px solid {c};padding-left:16px;margin-left:8px"><div><div style="font-size:10px;font-weight:700;letter-spacing:.08em;color:{"#a78bfa" if done else "#6b6b90"};margin-bottom:3px">МІСЯЦЬ {month} {icon}</div><div style="font-size:13px;color:{tc};line-height:1.5">{text}</div></div></div>', unsafe_allow_html=True)

# ── ANALYTICS ─────────────────────────────────────────────────────────────────
def tab_analytics(user):
    d = D()
    txs=user_filter(d["transactions"],user)
    mdata=[]
    for i in range(5,-1,-1):
        mo=CM-i; yr=CY
        while mo<=0: mo+=12; yr-=1
        k=f"{yr}-{str(mo).zfill(2)}"
        mi=sum(to_uah(t["amount"],t["currency"]) for t in txs if t["type"]=="income" and t["date"].startswith(k))
        me=sum(to_uah(t["amount"],t["currency"]) for t in txs if t["type"]=="expense" and t["date"].startswith(k))
        mdata.append({"m":MONTHS_UA[mo-1],"Дохід":mi,"Витрати":me,"Різниця":mi-me})
    df=pd.DataFrame(mdata)

    fig=go.Figure()
    fig.add_trace(go.Scatter(x=df["m"],y=df["Дохід"],name="Дохід",line=dict(color="#00D084",width=2),fill="tozeroy",fillcolor="#00D08420"))
    fig.add_trace(go.Scatter(x=df["m"],y=df["Витрати"],name="Витрати",line=dict(color="#FF4757",width=2),fill="tozeroy",fillcolor="#FF475720"))
    fig.update_layout(**PLOT_L,height=200,showlegend=True,legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#9896c8")))
    st.markdown('<div class="wcard"><div class="wlabel">Рух коштів (₴)</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    mtxs=[t for t in txs if t["type"]=="expense" and t["date"].startswith(CUR_MONTH)]
    exp_cat={}
    for t in mtxs: exp_cat[t["cat"]]=exp_cat.get(t["cat"],0)+to_uah(t["amount"],t["currency"])
    user_exp={}
    for t in txs:
        if t["type"]=="expense" and t["date"].startswith(CUR_MONTH):
            u=t.get("user","?"); user_exp[u]=user_exp.get(u,0)+to_uah(t["amount"],t["currency"])

    col1,col2=st.columns(2)
    with col1:
        if exp_cat:
            cl=[(cat_by_id(k),v) for k,v in sorted(exp_cat.items(),key=lambda x:-x[1])]
            fig2=go.Figure(go.Pie(labels=[c["label"] for c,_ in cl],values=[v for _,v in cl],hole=.45,marker_colors=[c["color"] for c,_ in cl],textinfo="none",hovertemplate="%{label}: %{value:,.0f} ₴<extra></extra>"))
            fig2.update_layout(**{**PLOT_L,"height":220})
            st.markdown('<div class="wcard"><div class="wlabel">Структура витрат</div>', unsafe_allow_html=True)
            st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
            st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        te=sum(user_exp.values())
        st.markdown('<div class="wcard"><div class="wlabel">Витрати по особі</div>', unsafe_allow_html=True)
        for u,v in sorted(user_exp.items(),key=lambda x:-x[1]):
            pct=round(v/te*100) if te>0 else 0; color=USER_COLORS.get(u,"#888")
            st.markdown(f'''<div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:13px">{USER_ICONS.get(u,"👤")} {u}</span>
                    <span style="font-size:12px;color:#9896c8">{fmt(v)} · {pct}%</span>
                </div>{pbar_html(pct,color,5)}</div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    cig=sum(to_uah(t["amount"],t["currency"]) for t in txs if t["cat"]=="cigs")
    auto=sum(to_uah(t["amount"],t["currency"]) for t in txs if t["cat"] in ["fuel","car"])
    subs=sum(to_uah(t["amount"],t["currency"]) for t in txs if t["cat"] in ["subs","mobile"])
    tinc=sum(to_uah(t["amount"],t["currency"]) for t in txs if t["type"]=="income")
    c1,c2=st.columns(2)
    for idx,(icon,label,val,sub,color) in enumerate([("🚬","Цигарки (всього)",fmt(cig),f"~{fmt(cig/max(1,sum(1 for t in txs if t['cat']=='cigs')))}/раз","#ec4899"),("🚗","Авто (всього)",fmt(auto),"пальне + ремонт","#3b82f6"),("📱","Підписки + зв'язок",fmt(subs),"за весь час","#a78bfa"),("💰","Загальний дохід",fmt(tinc,short=True),"за весь час","#00D084")]):
        with (c1 if idx%2==0 else c2):
            st.markdown(f'<div class="wcard"><span style="font-size:24px">{icon}</span><div style="font-size:11px;color:#9896c8;margin:6px 0 4px">{label}</div><div style="font-family:Unbounded,sans-serif;font-size:18px;font-weight:800;color:{color}">{val}</div><div style="font-size:11px;color:#9896c8">{sub}</div></div>', unsafe_allow_html=True)

    rows="".join(f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #00D08422"><span style="font-size:13px;color:#9896c8">{l}</span><span style="font-size:13px;font-weight:700;color:#00D084">{v}</span></div>' for l,v in [("Економія/міс",fmt(4800)),("Економія/рік",fmt(57600)),("За 2 роки у $",f"${57600*2/USD:,.0f}"),("Ремонт квартири швидше","~6 місяців")])
    st.markdown(f'<div class="wcard" style="background:#0d1a14;border-color:#00D08433"><div style="font-weight:700;font-size:14px;color:#00D084;margin-bottom:12px">💡 Якби кинути цигарки</div>{rows}</div>', unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    inject_css()
    load_data()
    user=sidebar()

    st.markdown(f'<div class="wtitle" style="font-size:24px;margin-bottom:2px">💸 WalletUA</div><div class="wmuted" style="margin-bottom:16px">Сімейний фінансовий трекер · {USER_ICONS.get(user,"👨‍👩‍👧")} {user}</div>', unsafe_allow_html=True)

    tabs=st.tabs(["⚡ Головна","💳 Рахунки","📋 Операції","📊 Бюджет","🔴 Борги","📈 Інвестиції","🎯 Цілі","🔍 Аналітика"])
    with tabs[0]: tab_dashboard(user)
    with tabs[1]: tab_accounts(user)
    with tabs[2]: tab_transactions(user)
    with tabs[3]: tab_budget(user)
    with tabs[4]: tab_debts(user)
    with tabs[5]: tab_savings(user)
    with tabs[6]: tab_goals(user)
    with tabs[7]: tab_analytics(user)

if __name__=="__main__":
    main()