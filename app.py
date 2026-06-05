import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import uuid
import requests

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Wallet Salyvon V16.1", layout="wide")

# =========================================================
# DB
# =========================================================
conn = sqlite3.connect("wallet_v16_1.db", check_same_thread=False)
c = conn.cursor()

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

conn.commit()

# =========================================================
# FX (SAFE NBU)
# =========================================================
@st.cache_data(ttl=3600)
def get_nbu():
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
        data = requests.get(url, timeout=5).json()

        rates = {"UAH": 1}

        if isinstance(data, list):
            for i in data:
                rates[i["cc"]] = i["rate"]

        return rates

    except:
        return {"UAH": 1, "USD": 41, "EUR": 44, "PLN": 10}

FX = get_nbu()

def to_uah(amount, cur):
    return amount * FX.get(cur, 1)

# =========================================================
# SAFE LOAD (CRASH-PROOF)
# =========================================================
def load_df():

    df = pd.read_sql("SELECT * FROM transactions", conn)

    # 🧠 EMPTY SAFE STATE
    if df.empty:
        return pd.DataFrame(columns=[
            "id","person","account","type",
            "category","amount","currency","date","uah"
        ])

    # DATE SAFE
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # UAH ALWAYS EXISTS
    df["uah"] = df.apply(
        lambda r: to_uah(r["amount"], r["currency"]),
        axis=1
    )

    return df

# =========================================================
# ADD TX SAFE
# =========================================================
def add_tx(p, acc, t, cat, amt, cur):
    c.execute("""
        INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)
    """, (
        str(uuid.uuid4()),
        p, acc, t, cat, amt, cur,
        datetime.now().strftime("%Y-%m-%d")
    ))
    conn.commit()

df = load_df()

# =========================================================
# UI
# =========================================================
st.title("💼 Wallet Salyvon V16.1 — Stable UX")

# =========================================================
# FILTER SAFE
# =========================================================
page = st.sidebar.radio(
    "Menu",
    ["📊 Dashboard", "➕ Transactions"]
)

period = st.sidebar.selectbox(
    "Period",
    ["Today","7D","Month","Year","All"]
)

now = datetime.now()

if df.empty:
    filtered = df
else:
    if period == "Today":
        filtered = df[df["date"] >= now - timedelta(days=1)]
    elif period == "7D":
        filtered = df[df["date"] >= now - timedelta(days=7)]
    elif period == "Month":
        filtered = df[df["date"] >= now - timedelta(days=30)]
    elif period == "Year":
        filtered = df[df["date"] >= now - timedelta(days=365)]
    else:
        filtered = df

# =========================================================
# SAFE METRICS (NO CRASH EVER)
# =========================================================
def safe_sum(df, t):
    if df.empty or "uah" not in df.columns:
        return 0
    return df[df.type==t]["uah"].sum()

income = safe_sum(filtered, "income")
expense = safe_sum(filtered, "expense")
balance = income - expense

# =========================================================
# DASHBOARD
# =========================================================
if page == "📊 Dashboard":

    st.metric("💰 Balance (UAH)", f"{balance:,.0f}")

    c1,c2,c3 = st.columns(3)
    c1.metric("Income", f"{income:,.0f}")
    c2.metric("Expense", f"{expense:,.0f}")
    c3.metric("Transactions", len(filtered))

    st.divider()

    st.subheader("📊 Expenses by Category")

    if filtered.empty:
        st.info("No data yet — add your first transaction 💡")
    else:
        exp = filtered[filtered.type=="expense"]
        if not exp.empty:
            st.bar_chart(exp.groupby("category")["uah"].sum())
        else:
            st.info("No expenses yet")

# =========================================================
# TRANSACTIONS
# =========================================================
elif page == "➕ Transactions":

    st.subheader("➕ Add transaction")

    person = st.selectbox("Person", ["Влад","Сонечко"])
    account = st.text_input("Account")
    t = st.selectbox("Type", ["income","expense"])
    cat = st.text_input("Category")
    cur = st.selectbox("Currency", ["UAH","USD","EUR","PLN"])
    amt = st.number_input("Amount", min_value=0.0)

    if st.button("Add"):
        add_tx(person, account, t, cat, amt, cur)
        st.rerun()

    if filtered.empty:
        st.info("No transactions yet")
    else:
        st.dataframe(filtered.sort_values("date", ascending=False))

# =========================================================
# FOOTER SAFE STATE
# =========================================================
st.sidebar.markdown("---")
st.sidebar.info("V16.1 Stable UX — no crashes mode 🧠")