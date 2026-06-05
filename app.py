import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# -------------------------
# НАЛАШТУВАННЯ
# -------------------------
st.set_page_config(page_title="Wallet Pro", layout="wide")

# -------------------------
# БАЗА ДАНИХ
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

c.execute("""
CREATE TABLE IF NOT EXISTS budgets (
    category TEXT PRIMARY KEY,
    limit_amount REAL
)
""")

conn.commit()

# -------------------------
# ФУНКЦІЇ
# -------------------------
def add_transaction(t, cat, amt):
    c.execute(
        "INSERT INTO transactions(type,category,amount,date) VALUES (?,?,?,?)",
        (t, cat, amt, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()

def set_budget(cat, limit):
    c.execute(
        "INSERT OR REPLACE INTO budgets VALUES (?,?)",
        (cat, limit)
    )
    conn.commit()

def load_transactions():
    return pd.read_sql("SELECT * FROM transactions", conn)

def load_budgets():
    return pd.read_sql("SELECT * FROM budgets", conn)

df = load_transactions()
budgets = load_budgets()

# -------------------------
# СТИЛЬ (як Budget apps)
# -------------------------
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

.big {
    font-size:26px;
    font-weight:700;
}

.small {
    color:#6b7280;
    font-size:13px;
}

.good { color:#16a34a; }
.bad { color:#ef4444; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# РОЗРАХУНКИ
# -------------------------
дохід = df[df.type=="income"]["amount"].sum() if not df.empty else 0
витрати = df[df.type=="expense"]["amount"].sum() if not df.empty else 0
баланс = дохід - витрати

# -------------------------
# КАРТКИ
# -------------------------
c1,c2,c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="card">
        <div class="small">Баланс</div>
        <div class="big">{баланс:.2f} ₴</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <div class="small">Дохід</div>
        <div class="big good">{дохід:.2f} ₴</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <div class="small">Витрати</div>
        <div class="big bad">{витрати:.2f} ₴</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# -------------------------
# ДОДАТИ ТРАНЗАКЦІЮ
# -------------------------
st.subheader("➕ Додати транзакцію")

col1,col2,col3 = st.columns(3)

with col1:
    тип = st.selectbox("Тип", ["income","expense"])

with col2:
    категорія = st.selectbox("Категорія", [
        "Їжа","Дім","Транспорт","Розваги","Здоров'я","Підписки","Інше"
    ])

with col3:
    сума = st.number_input("Сума", min_value=0.0)

if st.button("Додати"):
    add_transaction(тип, категорія, сума)
    st.rerun()

# -------------------------
# АНАЛІТИКА
# -------------------------
st.subheader("📊 Розподіл витрат")

if not df.empty:
    витрати_df = df[df.type=="expense"].groupby("category")["amount"].sum()
    st.bar_chart(витрати_df)

# -------------------------
# ТОП КАТЕГОРІЇ
# -------------------------
st.subheader("🔥 Найбільші витрати")

if not df.empty:
    топ = df[df.type=="expense"].groupby("category")["amount"].sum().sort_values(ascending=False)
    st.write(топ.head(5))

# -------------------------
# БЮДЖЕТИ
# -------------------------
st.subheader("🎯 Бюджети")

colA,colB = st.columns(2)

with colA:
    б_кат = st.selectbox("Категорія бюджету", [
        "Їжа","Дім","Транспорт","Розваги","Здоров'я","Підписки","Інше"
    ])
    ліміт = st.number_input("Ліміт", min_value=0.0)

    if st.button("Зберегти бюджет"):
        set_budget(б_кат, ліміт)
        st.rerun()

with colB:
    st.dataframe(budgets)

# -------------------------
# СТАН БЮДЖЕТІВ
# -------------------------
st.subheader("⚠️ Використання бюджету")

for _,b in budgets.iterrows():
    витрачено = df[(df.category==b.category)&(df.type=="expense")]["amount"].sum()
    відсоток = (витрачено / b.limit_amount * 100) if b.limit_amount > 0 else 0

    if відсоток > 100:
        st.error(f"{b.category}: перевищено {витрачено}/{b.limit_amount} 😏")
    else:
        st.write(f"{b.category}: {витрачено}/{b.limit_amount} ({відсоток:.0f}%)")

# -------------------------
# ІСТОРІЯ
# -------------------------
st.subheader("🧾 Історія транзакцій")

if not df.empty:
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)