import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Wallet Budget",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# DB
# -------------------------
conn = sqlite3.connect("wallet.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    category TEXT,
    amount REAL,
    date TEXT
)
""")
conn.commit()

# -------------------------
# FUNCTIONS
# -------------------------
def add_tx(t, cat, amt):
    c.execute(
        "INSERT INTO transactions(type,category,amount,date) VALUES (?,?,?,?)",
        (t, cat, amt, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()

def load():
    return pd.read_sql("SELECT * FROM transactions", conn)

df = load()

# -------------------------
# STYLE (Budget App look)
# -------------------------
st.markdown("""
<style>
    body {
        background-color: #f6f7fb;
    }

    .card {
        background: white;
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        text-align: center;
    }

    .title {
        font-size: 14px;
        color: #6b7280;
    }

    .value {
        font-size: 28px;
        font-weight: 700;
        margin-top: 5px;
    }

    .income { color: #16a34a; }
    .expense { color: #ef4444; }

    .stButton button {
        background: #4f46e5;
        color: white;
        border-radius: 12px;
        padding: 10px;
        font-weight: 600;
        width: 100%;
    }

    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# DATA
# -------------------------
income = df[df["type"] == "income"]["amount"].sum() if not df.empty else 0
expense = df[df["type"] == "expense"]["amount"].sum() if not df.empty else 0
balance = income - expense

# -------------------------
# HEADER
# -------------------------
st.title("💼 Wallet Budget")

st.write("Track your money simply & clean.")

# -------------------------
# CARDS
# -------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="card">
        <div class="title">Balance</div>
        <div class="value">{balance:.2f} ₴</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <div class="title">Income</div>
        <div class="value income">{income:.2f} ₴</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <div class="title">Expenses</div>
        <div class="value expense">{expense:.2f} ₴</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# -------------------------
# QUICK ADD (Budget style)
# -------------------------
st.subheader("➕ Add expense / income")

col1, col2, col3 = st.columns(3)

with col1:
    ttype = st.selectbox("Type", ["income", "expense"])

with col2:
    category = st.selectbox("Category", [
        "Food", "Home", "Transport", "Fun", "Health", "Other"
    ])

with col3:
    amount = st.number_input("Amount", min_value=0.0)

if st.button("Add transaction"):
    add_tx(ttype, category, amount)
    st.rerun()

# -------------------------
# CATEGORY OVERVIEW (Budget vibe)
# -------------------------
st.subheader("📊 Spending by category")

if not df.empty:
    expense_df = df[df["type"] == "expense"]
    cat = expense_df.groupby("category")["amount"].sum()
    st.bar_chart(cat)

# -------------------------
# RECENT TRANSACTIONS
# -------------------------
st.subheader("🧾 Recent transactions")

if df.empty:
    st.info("No transactions yet")
else:
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)