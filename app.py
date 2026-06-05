import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import uuid

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Wallet Pro V6", layout="wide")

# =========================================================
# DB LAYER
# =========================================================
conn = sqlite3.connect("wallet_v6.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    person TEXT,
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

c.execute("""
CREATE TABLE IF NOT EXISTS people (
    name TEXT PRIMARY KEY
)
""")

conn.commit()

# =========================================================
# HELPERS
# =========================================================
def add_tx(person, t, cat, amt):
    c.execute("""
    INSERT INTO transactions VALUES (?,?,?,?,?,?)
    """, (
        str(uuid.uuid4()),
        person,
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

def load_budgets():
    return pd.read_sql("SELECT * FROM budgets", conn)

df = load_df()

# =========================================================
# UI STYLE
# =========================================================
st.markdown("""
<style>
body { background:#f6f7fb; }

.card {
    background:white;
    padding:18px;
    border-radius:18px;
    box-shadow:0 4px 16px rgba(0,0,0,0.08);
}

.big {
    font-size:28px;
    font-weight:700;
}

.small {
    color:#6b7280;
}

.good { color:#16a34a; }
.bad { color:#ef4444; }

.section-title {
    font-size:18px;
    font-weight:600;
    margin-top:20px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.title("💼 Wallet Pro V6 — Fintech Level App")

# =========================================================
# KPI DASHBOARD
# =========================================================
income = df[df.type=="income"]["amount"].sum() if not df.empty else 0
expense = df[df.type=="expense"]["amount"].sum() if not df.empty else 0
balance = income - expense

c1,c2,c3 = st.columns(3)

with c1:
    st.markdown(f"<div class='card'><div class='small'>Баланс</div><div class='big'>{balance:.2f}</div></div>", unsafe_allow_html=True)

with c2:
    st.markdown(f"<div class='card'><div class='small'>Дохід</div><div class='big good'>{income:.2f}</div></div>", unsafe_allow_html=True)

with c3:
    st.markdown(f"<div class='card'><div class='small'>Витрати</div><div class='big bad'>{expense:.2f}</div></div>", unsafe_allow_html=True)

st.divider()

# =========================================================
# TABS (APP STRUCTURE)
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Дашборд",
    "➕ Транзакції",
    "👨‍👩‍👧 Сім’я",
    "🎯 Бюджети"
])

# =========================================================
# TAB 1 - DASHBOARD
# =========================================================
with tab1:
    st.subheader("Фінансовий огляд")

    if not df.empty:
        st.bar_chart(df[df.type=="expense"].groupby("category")["amount"].sum())

        st.line_chart(df.groupby("date")["amount"].sum())

    st.write("Топ витрати:")
    if not df.empty:
        st.write(df[df.type=="expense"].groupby("category")["amount"].sum().sort_values(ascending=False))

# =========================================================
# TAB 2 - TRANSACTIONS (FULL CONTROL)
# =========================================================
with tab2:
    st.subheader("➕ Додати транзакцію")

    col1,col2,col3,col4 = st.columns(4)

    with col1:
        person = st.text_input("Хто", "Я")

    with col2:
        t = st.selectbox("Тип", ["income","expense"])

    with col3:
        cat = st.text_input("Категорія")

    with col4:
        amt = st.number_input("Сума", min_value=0.0)

    if st.button("Додати транзакцію"):
        add_tx(person,t,cat,amt)
        st.rerun()

    st.divider()
    st.subheader("🧾 Історія")

    if not df.empty:
        for _, row in df.sort_values("date", ascending=False).iterrows():

            colA,colB,colC,colD,colE = st.columns(5)

            with colA:
                st.write(row["person"])
            with colB:
                st.write(row["type"])
            with colC:
                st.write(row["category"])
            with colD:
                st.write(row["amount"])
            with colE:
                if st.button("❌", key=row["id"]):
                    delete_tx(row["id"])
                    st.rerun()

# =========================================================
# TAB 3 - FAMILY VIEW
# =========================================================
with tab3:
    st.subheader("👨‍👩‍👧 Сімейний бюджет")

    if not df.empty:
        st.bar_chart(df.groupby("person")["amount"].sum())

        st.write(df.groupby("person")["amount"].sum())

# =========================================================
# TAB 4 - BUDGETS
# =========================================================
with tab4:
    st.subheader("🎯 Бюджети")

    cat = st.text_input("Категорія бюджету")
    limit = st.number_input("Ліміт", min_value=0.0)

    if st.button("Зберегти"):
        c.execute("INSERT OR REPLACE INTO budgets VALUES (?,?)", (cat, limit))
        conn.commit()
        st.rerun()

    budgets = load_budgets()
    st.dataframe(budgets)

    st.subheader("⚠️ Контроль")

    for _,b in budgets.iterrows():
        spent = df[(df.category==b.category)&(df.type=="expense")]["amount"].sum()

        if spent > b.limit_amount:
            st.error(f"{b.category}: {spent}/{b.limit_amount} 🔥 перевищено")
        else:
            st.write(f"{b.category}: {spent}/{b.limit_amount}")