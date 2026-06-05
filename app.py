import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import uuid
import requests

# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(page_title="Wallet Salyvon V14", layout="wide")

# =========================================================
# DB
# =========================================================
conn = sqlite3.connect("wallet_salyvon_v14.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    name TEXT PRIMARY KEY,
    type TEXT,
    currency TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    person TEXT,
    account TEXT,
    type TEXT,
    category TEXT,
    amount REAL,
    currency TEXT,
    date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS budgets (
    category TEXT PRIMARY KEY,
    limit_amount REAL
)
""")

conn.commit()

# =========================================================
# LIVE NBU FX
# =========================================================
@st.cache_data(ttl=3600)
def get_nbu():
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    data = requests.get(url).json()
    rates = {"UAH": 1}
    for i in data:
        rates[i["cc"]] = i["rate"]
    return rates

FX = get_nbu()

def to_uah(amount, currency):
    return amount * FX.get(currency, 1)

# =========================================================
# BINANCE CRYPTO
# =========================================================
@st.cache_data(ttl=30)
def get_binance():
    url = "https://api.binance.com/api/v3/ticker/price"
    data = requests.get(url).json()
    return {i["symbol"]: float(i["price"]) for i in data}

CRYPTO = get_binance()

def crypto_to_uah(amount, coin):
    usd_uah = FX.get("USD", 40)
    price = CRYPTO.get(coin + "USDT")
    if price:
        return amount * price * usd_uah
    return 0

# =========================================================
# HELPERS
# =========================================================
def add_tx(person, account, t, cat, amt, cur):
    c.execute("""
        INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)
    """, (
        str(uuid.uuid4()),
        person,
        account,
        t,
        cat,
        amt,
        cur,
        datetime.now().strftime("%Y-%m-%d")
    ))
    conn.commit()

def load_df():
    df = pd.read_sql("SELECT * FROM transactions", conn)
    df["date"] = pd.to_datetime(df["date"])

    def convert(r):
        if r["currency"] in ["BTC", "ETH"]:
            return crypto_to_uah(r["amount"], r["currency"])
        return to_uah(r["amount"], r["currency"])

    df["uah"] = df.apply(convert, axis=1)
    return df

df = load_df()

# =========================================================
# TITLE
# =========================================================
st.title("💼 Wallet Salyvon V14")

# =========================================================
# FILTERS
# =========================================================
period = st.selectbox("📅 Період", ["Сьогодні","7 днів","Місяць","Рік","Все"])

now = datetime.now()

if period == "Сьогодні":
    filtered = df[df["date"] >= now - timedelta(days=1)]
elif period == "7 днів":
    filtered = df[df["date"] >= now - timedelta(days=7)]
elif period == "Місяць":
    filtered = df[df["date"] >= now - timedelta(days=30)]
elif period == "Рік":
    filtered = df[df["date"] >= now - timedelta(days=365)]
else:
    filtered = df

# =========================================================
# KPI
# =========================================================
income = filtered[filtered.type=="income"]["uah"].sum()
expense = filtered[filtered.type=="expense"]["uah"].sum()
balance = income - expense

st.metric("💰 Net Worth (UAH)", f"{balance:,.0f}")

# =========================================================
# BREAKDOWN (IMPORTANT UPGRADE)
# =========================================================
st.subheader("🏦 Структура активів")

cards = filtered[filtered.account.str.contains("Карт")]["uah"].sum()
cash = filtered[filtered.account.str.contains("Готів")]["uah"].sum()
crypto = filtered[filtered.currency.isin(["BTC","ETH"])]["uah"].sum()
fx = filtered[filtered.currency.isin(["USD","EUR","PLN"])]["uah"].sum()

c1,c2,c3,c4 = st.columns(4)

c1.metric("💳 Карти", f"{cards:,.0f} ₴")
c2.metric("💵 Готівка", f"{cash:,.0f} ₴")
c3.metric("💱 Валюта", f"{fx:,.0f} ₴")
c4.metric("₿ Крипта", f"{crypto:,.0f} ₴")

st.divider()

# =========================================================
# ANALYTICS
# =========================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("👨‍👩‍👧 Сім’я")
    st.bar_chart(filtered.groupby("person")["uah"].sum())

with col2:
    st.subheader("📊 Категорії витрат")
    st.bar_chart(filtered[filtered.type=="expense"].groupby("category")["uah"].sum())

# =========================================================
# BUDGET ENGINE
# =========================================================
st.subheader("🎯 Бюджети")

cat = st.text_input("Категорія", key="b1")
lim = st.number_input("Ліміт", key="b2", min_value=0.0)

if st.button("Зберегти бюджет"):
    c.execute("INSERT OR REPLACE INTO budgets VALUES (?,?)", (cat, lim))
    conn.commit()
    st.rerun()

budgets = pd.read_sql("SELECT * FROM budgets", conn)
st.dataframe(budgets)

for _, b in budgets.iterrows():
    spent = filtered[(filtered.category==b.category)&(filtered.type=="expense")]["uah"].sum()

    if spent > b.limit_amount:
        st.error(f"🔥 {b.category}: {spent:,.0f} / {b.limit_amount}")
    else:
        st.write(f"{b.category}: {spent:,.0f} / {b.limit_amount}")

st.divider()

# =========================================================
# TRANSACTIONS
# =========================================================
st.subheader("➕ Додати транзакцію")

person = st.selectbox("Хто", ["Влад","Сонечко"])
account = st.text_input("Рахунок")
t = st.selectbox("Тип", ["income","expense"])
cat = st.text_input("Категорія")
cur = st.selectbox("Валюта", ["UAH","USD","EUR","PLN","BTC","ETH"])
amt = st.number_input("Сума", min_value=0.0)

if st.button("Додати"):
    add_tx(person, account, t, cat, amt, cur)
    st.rerun()

st.subheader("🧾 Історія")
st.dataframe(filtered.sort_values("date", ascending=False))