import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import uuid

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Wallet", layout="wide")

conn = sqlite3.connect("wallet_v7.db", check_same_thread=False)
c = conn.cursor()

# =========================================================
# TABLES
# =========================================================
c.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    name TEXT PRIMARY KEY,
    type TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    account TEXT,
    type TEXT,
    category TEXT,
    amount REAL,
    date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS debts (
    name TEXT,
    total REAL,
    remaining REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS savings (
    name TEXT,
    goal REAL,
    saved REAL
)
""")

conn.commit()

# =========================================================
# HELPERS
# =========================================================
def add_account(name, type_):
    c.execute("INSERT OR IGNORE INTO accounts VALUES (?,?)", (name,type_))
    conn.commit()

def add_tx(acc,t,cat,amt):
    c.execute("""
    INSERT INTO transactions VALUES (?,?,?,?,?,?)
    """, (
        str(uuid.uuid4()),
        acc,t,cat,amt,
        datetime.now().strftime("%Y-%m-%d")
    ))
    conn.commit()

def df_tx():
    return pd.read_sql("SELECT * FROM transactions", conn)

def df_acc():
    return pd.read_sql("SELECT * FROM accounts", conn)

# =========================================================
# UI
# =========================================================
st.title("💼 Wallet Salyvon")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Дашборд",
    "🏦 Рахунки",
    "➕ Транзакції",
    "💳 Борги",
    "💰 Заощадження"
])

df = df_tx()
acc = df_acc()

# =========================================================
# DASHBOARD
# =========================================================
with tab1:
    st.subheader("Net Worth")

    if not df.empty:
        st.metric("Загальний баланс", df[df.type=="income"]["amount"].sum() -
                  df[df.type=="expense"]["amount"].sum())

        st.bar_chart(df.groupby("account")["amount"].sum())

# =========================================================
# ACCOUNTS
# =========================================================
with tab2:
    st.subheader("🏦 Рахунки")

    name = st.text_input("Назва рахунку")
    type_ = st.selectbox("Тип", ["card","credit","cash","crypto","investment"])

    if st.button("Додати рахунок"):
        add_account(name,type_)
        st.rerun()

    st.dataframe(acc)

# =========================================================
# TRANSACTIONS
# =========================================================
with tab3:
    st.subheader("➕ Транзакції")

    account = st.text_input("Рахунок")
    t = st.selectbox("Тип", ["income","expense"])
    cat = st.text_input("Категорія")
    amt = st.number_input("Сума", min_value=0.0)

    if st.button("Додати"):
        add_tx(account,t,cat,amt)
        st.rerun()

    st.subheader("Історія")
    st.dataframe(df.sort_values("date", ascending=False))

# =========================================================
# DEBTS
# =========================================================
with tab4:
    st.subheader("💳 Борги")

    dname = st.text_input("Назва боргу")
    total = st.number_input("Загальна сума", min_value=0.0)
    remaining = st.number_input("Залишок", min_value=0.0)

    if st.button("Додати борг"):
        c.execute("INSERT INTO debts VALUES (?,?,?)", (dname,total,remaining))
        conn.commit()
        st.rerun()

    debts = pd.read_sql("SELECT * FROM debts", conn)
    st.dataframe(debts)

    st.subheader("⚠️ Структура боргу")

    if not debts.empty:
        st.bar_chart(debts.set_index("name")["remaining"])

# =========================================================
# SAVINGS
# =========================================================
with tab5:
    st.subheader("💰 Заощадження")

    sname = st.text_input("Ціль")
    goal = st.number_input("Мета", min_value=0.0)
    saved = st.number_input("Накопичено", min_value=0.0)

    if st.button("Додати заощадження"):
        c.execute("INSERT INTO savings VALUES (?,?,?)", (sname,goal,saved))
        conn.commit()
        st.rerun()

    savings = pd.read_sql("SELECT * FROM savings", conn)
    st.dataframe(savings)

    if not savings.empty:
        st.subheader("📊 Прогрес цілей")
        st.bar_chart(savings.set_index("name")["saved"])