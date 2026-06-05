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
CUR_MONTH = f"{CY}-{str(CM).zfill(2)}"
MONTHS_UA = ["Січ","Лют","Бер","Кві","Тра","Чер","Лип","Сер","Вер","Жов","Лис","Гру"]
MONTHS_FULL = ["Січень","Лютий","Березень","Квітень","Травень","Червень","Липень","Серпень","Вересень","Жовтень","Листопад","Грудень"]
USERS = ["Влад", "Лізонька", "Спільне"]
USER_ICONS = {"Влад":"👨","Лізонька":"👩","Спільне":"👨‍👩‍👧"}
USER_COLORS = {"Влад":"#7B61FF","Лізонька":"#ec4899","Спільне":"#00D084"}

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
            {"id":"mono",     "name":"Monobank",   "type":"card",  "currency":"₴","balance":4200, "icon":"🐱","user":"Влад",  "note":"Чорна картка"},
            {"id":"privat",   "name":"ПриватБанк", "type":"card",  "currency":"₴","balance":1850, "icon":"🏦","user":"Влад",  "note":""},
            {"id":"cash",     "name":"Готівка",     "type":"cash",  "currency":"₴","balance":3500, "icon":"💵","user":"Спільне","note":""},
            {"id":"binance",  "name":"Binance",     "type":"crypto","currency":"$","balance":68,   "icon":"🟡","user":"Влад",  "note":"Earn Flexible"},
            {"id":"wife_mono","name":"Monobank",    "type":"card",  "currency":"₴","balance":2100, "icon":"🐱","user":"Лізонька","note":""},
        ],
        "transactions":[
            {"id":uid(),"type":"income", "cat":"salary",  "acc":"mono",     "amount":35000,"currency":"₴","note":"Зарплата",          "date":f"{CY}-06-01","user":"Влад"},
            {"id":uid(),"type":"income", "cat":"housing", "acc":"mono",     "amount":2300, "currency":"₴","note":"Компенсація найму",   "date":f"{CY}-06-01","user":"Влад"},
            {"id":uid(),"type":"income", "cat":"parents", "acc":"cash",     "amount":100,  "currency":"$","note":"Батьки",             "date":f"{CY}-06-02","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"rent",    "acc":"mono",     "amount":300,  "currency":"$","note":"Оренда червень",      "date":f"{CY}-06-03","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"utils",   "acc":"mono",     "amount":1800, "currency":"₴","note":"Комуналка",           "date":f"{CY}-06-05","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"mobile",  "acc":"mono",     "amount":450,  "currency":"₴","note":"Київстар",            "date":f"{CY}-06-05","user":"Влад"},
            {"id":uid(),"type":"expense","cat":"mobile",  "acc":"wife_mono","amount":400,  "currency":"₴","note":"Київстар",            "date":f"{CY}-06-05","user":"Лізонька"},
            {"id":uid(),"type":"expense","cat":"subs",    "acc":"mono",     "amount":1641, "currency":"₴","note":"Netflix+YT+iCloud+G1","date":f"{CY}-06-05","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"food",    "acc":"privat",   "amount":3800, "currency":"₴","note":"Сільпо + Новус",      "date":f"{CY}-06-10","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"cigs",    "acc":"cash",     "amount":4800, "currency":"₴","note":"Цигарки",             "date":f"{CY}-06-15","user":"Влад"},
            {"id":uid(),"type":"expense","cat":"child",   "acc":"mono",     "amount":1500, "currency":"₴","note":"Дитячі витрати",      "date":f"{CY}-06-12","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"fuel",    "acc":"cash",     "amount":1800, "currency":"₴","note":"Пальне Audi",         "date":f"{CY}-06-14","user":"Влад"},
            {"id":uid(),"type":"income", "cat":"salary",  "acc":"mono",     "amount":35000,"currency":"₴","note":"Зарплата травень",    "date":f"{CY}-05-01","user":"Влад"},
            {"id":uid(),"type":"income", "cat":"housing", "acc":"mono",     "amount":2300, "currency":"₴","note":"Компенсація",          "date":f"{CY}-05-01","user":"Влад"},
            {"id":uid(),"type":"expense","cat":"rent",    "acc":"mono",     "amount":300,  "currency":"$","note":"Оренда",              "date":f"{CY}-05-03","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"utils",   "acc":"mono",     "amount":2100, "currency":"₴","note":"Комуналка",           "date":f"{CY}-05-05","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"cigs",    "acc":"cash",     "amount":4800, "currency":"₴","note":"Цигарки",             "date":f"{CY}-05-15","user":"Влад"},
            {"id":uid(),"type":"expense","cat":"food",    "acc":"privat",   "amount":4200, "currency":"₴","note":"Продукти",            "date":f"{CY}-05-10","user":"Спільне"},
            {"id":uid(),"type":"expense","cat":"car",     "acc":"cash",     "amount":3200, "currency":"₴","note":"Ремонт Audi",         "date":f"{CY}-05-20","user":"Влад"},
            {"id":uid(),"type":"expense","cat":"fuel",    "acc":"cash",     "amount":1900, "currency":"₴","note":"Пальне",              "date":f"{CY}-05-14","user":"Влад"},
        ],
        "debts":[
            {"id":uid(),"dir":"owe", "label":"Кредитна картка","amount":12260,"currency":"₴","dueDate":"","note":"Monobank кредитка","paid":0,"user":"Влад"},
            {"id":uid(),"dir":"owe", "label":"Іпотека єОселя", "amount":8000, "currency":"₴","dueDate":"","note":"Щомісячний платіж", "paid":0,"user":"Спільне"},
            {"id":uid(),"dir":"owed","label":"Весільні кошти", "amount":2000, "currency":"$","dueDate":"","note":"Повернути",          "paid":0,"user":"Спільне"},
        ],
        "savings":[
            {"id":uid(),"instrument":"inzhur_reit",  "amount":2150,"currency":"₴","date":f"{CY}-01-01","note":"Початкова позиція","user":"Влад"},
            {"id":uid(),"instrument":"binance_flex", "amount":68,  "currency":"$","date":f"{CY}-03-01","note":"Earn USDT",         "user":"Влад"},
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
                with open(DATA_FILE,encoding="utf-8") as f:
                    st.session_state.data = json.load(f)
            except Exception:
                st.session_state.data = make_init()
        else:
            st.session_state.data = make_init()

def save_data():
    try:
        with open(DATA_FILE,"w",encoding="utf-8") as f:
            json.dump(st.session_state.data,f,ensure_ascii=False,indent=2)
    except Exception:
        pass

def D(): return st.session_state.data