import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import uuid

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Wallet Salyvon", layout="wide")

conn = sqlite3.connect("wallet_salyvon.db", check_same_thread=False)
c = conn.cursor()

# =========================================================
# DATABASE
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
    person TEXT,
    account TEXT,
    type TEXT,
    category TEXT,
    amount REAL,
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
# HELPERS
# =========================================================
def add_account(name, type_):
    c.execute("INSERT OR IGNORE INTO accounts VALUES (?,?)", (name, type_))
    conn.commit()

def add_tx(person, account, t, cat, amt):
    c.execute("""
        INSERT INTO transactions VALUES (?,?,?,?,?,?,?)
    """, (
        str(uuid.uuid4()),
        person,
        account,
        t,
        cat,
        amt,
        datetime.now().strftime("%Y-%m-%d")
    ))
    conn.commit()

def delete_tx(tx_id):
    c.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()

def load_df():
    return pd.read_sql("SELECT * FROM transactions", conn)

def load_accounts():
    return pd.read_sql("SELECT * FROM accounts", conn)

def load_budgets():
    return pd.read_sql("SELECT * FROM budgets", conn)

df = load_df()
accounts = load_accounts()
budgets = load_budgets()

# =========================================================
# UI STYLE
# =========================================================
st.markdown("""
<style>
body { background:#f6f7fb; }

.card {
    background:white;
    padding:16px;
    border-radius:16px;
    box-shadow:0 4px 14px rgba(0,0,0,0.08);
    text-align:center;
}

.big { font-size:26px; font-weight:700; }
.small { color:#6b7280; }

.good { color:#16a34a; }
.bad { color:#ef4444; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.title("💼 Wallet Salyvon")

# =========================================================
# KPIs
# =========================================================
income = df[df.type=="income"]["amount"].sum() if not df.empty else 0
expense = df[df.type=="expense"]["amount"].sum() if not df.empty else 0
balance = income - expense

c1,c2,c3 = st.columns(3)

with c1:
    st.markdown(f"<div class='card'><div class='small'>Баланс</div><div class='big'>{balance:.2f} ₴</div></div>", unsafe_allow_html=True)

with c2:
    st.markdown(f"<div class='card'><div class='small'>Дохід</div><div class='big good'>{income:.2f} ₴</div></div>", unsafe_allow_html=True)

with c3:
    st.markdown(f"<div class='card'><div class='small'>Витрати</div><div class='big bad'>{expense:.2f} ₴</div></div>", unsafe_allow_html=True)

st.divider()

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Дашборд",
    "➕ Транзакції",
    "🏦 Рахунки",
    "🎯 Бюджети"
])

# =========================================================
# DASHBOARD
# =========================================================
with tab1:
    st.subheader("👨‍👩‍👧 Сімейний розподіл")

    if not df.empty:
        st.bar_chart(df.groupby("person")["amount"].sum())

        st.subheader("Категорії")
        st.bar_chart(df[df.type=="expense"].groupby("category")["amount"].sum())

# =========================================================
# TRANSACTIONS
# =========================================================
with tab2:
    st.subheader("➕ Додати транзакцію")

    person = st.selectbox("Хто", ["Ви", "Дружина"])

    account = st.selectbox(
        "Рахунок",
        ["Картка 1", "Картка 2", "Кредитка", "Готівка", "Крипта", "Інвестиції"]
    )

    t = st.selectbox("Тип", ["income","expense"])

    cat = st.text_input("Категорія")

    amt = st.number_input("Сума", min_value=0.0)

    if st.button("Додати"):
        add_tx(person, account, t, cat, amt)
        st.rerun()

    st.subheader("🧾 Історія")

    if not df.empty:
        for _, row in df.sort_values("date", ascending=False).iterrows():
            col1,col2,col3,col4,col5,col6 = st.columns(6)

            with col1: st.write(row["person"])
            with col2: st.write(row["account"])
            with col3: st.write(row["type"])
            with col4: st.write(row["category"])
            with col5: st.write(row["amount"])

            with col6:
                if st.button("❌", key=row["id"]):
                    delete_tx(row["id"])
                    st.rerun()

# =========================================================
# ACCOUNTS
# =========================================================
with tab3:
    st.subheader("🏦 Рахунки")

    name = st.text_input("Назва рахунку")
    type_ = st.selectbox("Тип", ["card","cash","crypto","investment","credit"])

    if st.button("Додати рахунок"):
        add_account(name,type_)
        st.rerun()

    st.dataframe(accounts)

# =========================================================
# BUDGETS
# =========================================================
with tab4:
    st.subheader("🎯 Бюджети")

    cat = st.text_input("Категорія")
    limit = st.number_input("Ліміт", min_value=0.0)

    if st.button("Зберегти"):
        c.execute("INSERT OR REPLACE INTO budgets VALUES (?,?)", (cat,limit))
        conn.commit()
        st.rerun()

    budgets = load_budgets()
    st.dataframe(budgets)

    st.subheader("⚠️ Контроль бюджету")

    for _,b in budgets.iterrows():
        spent = df[(df.category==b.category)&(df.type=="expense")]["amount"].sum()

        if spent > b.limit_amount:
            st.error(f"{b.category}: {spent}/{b.limit_amount} 🔥 перевищено")
        else:
            st.write(f"{b.category}: {spent}/{b.limit_amount}")