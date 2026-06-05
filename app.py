import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import uuid
import requests

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Wallet Salyvon V16", layout="wide")

# =========================================================
# DB
# =========================================================
conn = sqlite3.connect("wallet_v16.db", check_same_thread=False)
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

c.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    name TEXT PRIMARY KEY,
    type TEXT,
    currency TEXT
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
# FX (NBU SAFE)
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
# DATA
# =========================================================
def load_df():
    df = pd.read_sql("SELECT * FROM transactions", conn)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["uah"] = df.apply(lambda r: to_uah(r["amount"], r["currency"]), axis=1)
    return df

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
# SIDEBAR NAVIGATION (FIX UI STRUCTURE)
# =========================================================
page = st.sidebar.radio(
    "💼 Wallet Salyvon",
    ["📊 Dashboard", "➕ Transactions", "🏦 Accounts", "🎯 Budgets", "👨‍👩‍👧 Family", "💰 Assets"]
)

st.title("💼 Wallet Salyvon V16")

# =========================================================
# FILTER (GLOBAL)
# =========================================================
period = st.sidebar.selectbox("📅 Period", ["Today","7D","Month","Year","All"])

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
# DASHBOARD
# =========================================================
if page == "📊 Dashboard":

    income = filtered[filtered.type=="income"]["uah"].sum()
    expense = filtered[filtered.type=="expense"]["uah"].sum()
    balance = income - expense

    st.metric("💰 Net Balance (UAH)", f"{balance:,.0f}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Income", f"{income:,.0f}")
    c2.metric("Expense", f"{expense:,.0f}")
    c3.metric("Tx Count", len(filtered))

    st.divider()

    st.subheader("📊 Expenses by Category")
    if not filtered.empty:
        st.bar_chart(filtered[filtered.type=="expense"].groupby("category")["uah"].sum())

# =========================================================
# TRANSACTIONS
# =========================================================
elif page == "➕ Transactions":

    st.subheader("➕ Add Transaction")

    person = st.selectbox("Person", ["Влад","Сонечко"])
    account = st.text_input("Account")
    t = st.selectbox("Type", ["income","expense"])
    cat = st.text_input("Category")
    cur = st.selectbox("Currency", ["UAH","USD","EUR","PLN"])
    amt = st.number_input("Amount", min_value=0.0)

    if st.button("Add"):
        add_tx(person, account, t, cat, amt, cur)
        st.rerun()

    st.subheader("📜 History")
    st.dataframe(filtered.sort_values("date", ascending=False))

# =========================================================
# ACCOUNTS
# =========================================================
elif page == "🏦 Accounts":

    st.subheader("🏦 Accounts")

    name = st.text_input("Name")
    type_ = st.selectbox("Type", ["card","cash","crypto","investment"])
    cur = st.selectbox("Currency", ["UAH","USD","EUR","PLN"])

    if st.button("Add account"):
        c.execute("INSERT OR IGNORE INTO accounts VALUES (?,?,?)", (name,type_,cur))
        conn.commit()
        st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM accounts", conn))

# =========================================================
# BUDGETS
# =========================================================
elif page == "🎯 Budgets":

    st.subheader("🎯 Budgets")

    cat = st.text_input("Category")
    lim = st.number_input("Limit", min_value=0.0)

    if st.button("Save budget"):
        c.execute("INSERT OR REPLACE INTO budgets VALUES (?,?)", (cat, lim))
        conn.commit()
        st.rerun()

    budgets = pd.read_sql("SELECT * FROM budgets", conn)
    st.dataframe(budgets)

    st.subheader("⚠️ Control")

    for _, b in budgets.iterrows():
        spent = filtered[(filtered.category==b.category)&(filtered.type=="expense")]["uah"].sum()

        if spent > b.limit_amount:
            st.error(f"🔥 {b.category}: {spent:,.0f}/{b.limit_amount}")
        else:
            st.write(f"{b.category}: {spent:,.0f}/{b.limit_amount}")

# =========================================================
# FAMILY
# =========================================================
elif page == "👨‍👩‍👧 Family":

    st.subheader("Family Overview (Влад / Сонечко)")

    if not filtered.empty:
        st.bar_chart(filtered.groupby("person")["uah"].sum())

# =========================================================
# ASSETS
# =========================================================
elif page == "💰 Assets":

    st.subheader("💰 Assets Breakdown")

    if not filtered.empty:
        cards = filtered[filtered.account.str.contains("card", case=False, na=False)]["uah"].sum()
        cash = filtered[filtered.account.str.contains("cash", case=False, na=False)]["uah"].sum()
        fx = filtered[filtered.currency.isin(["USD","EUR","PLN"])]["uah"].sum()

        c1,c2,c3 = st.columns(3)
        c1.metric("Cards", f"{cards:,.0f}")
        c2.metric("Cash", f"{cash:,.0f}")
        c3.metric("FX", f"{fx:,.0f}")

        st.subheader("FX Exposure")
        st.bar_chart(filtered.groupby("currency")["uah"].sum())