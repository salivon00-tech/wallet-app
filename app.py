import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import calendar

st.set_page_config(page_title="Wallet Pro v3", layout="wide")

DB = "wallet_v3.db"
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

# -------------------------
# DB INIT
# -------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    type TEXT,
    category TEXT,
    amount REAL,
    date TEXT,
    weekday TEXT,
    recurring INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS budgets (
    user TEXT,
    category TEXT,
    limit_amount REAL,
    PRIMARY KEY (user, category)
)
""")

conn.commit()

# -------------------------
# HELPERS
# -------------------------
def add_user(u):
    c.execute("INSERT OR IGNORE INTO users VALUES (?)", (u,))
    conn.commit()

def add_tx(data):
    c.execute("""
    INSERT INTO transactions
    (user,type,category,amount,date,weekday,recurring)
    VALUES (?,?,?,?,?,?,?)
    """, data)
    conn.commit()

def get_df():
    return pd.read_sql("SELECT * FROM transactions", conn)

def get_budgets():
    return pd.read_sql("SELECT * FROM budgets", conn)

# -------------------------
# UI
# -------------------------
st.title("💰 Wallet Pro v3 — FINTECH EDITION")

# -------------------------
# LOGIN
# -------------------------
st.sidebar.header("🔐 Користувач")
user = st.sidebar.text_input("Ім'я", "Я")

add_user(user)

# -------------------------
# INPUT
# -------------------------
st.sidebar.header("➕ Транзакція")

t_type = st.sidebar.selectbox("Тип", ["Дохід","Витрата"])
category = st.sidebar.selectbox("Категорія", ["Їжа","Дім","Транспорт","Розваги","Здоров'я","Інше"])
amount = st.sidebar.number_input("Сума", min_value=0.0)
recurring = st.sidebar.checkbox("Повторювана")

date = st.sidebar.date_input("Дата", datetime.now())
weekday = calendar.day_name[date.weekday()]

if st.sidebar.button("Додати"):
    add_tx((user,t_type,category,amount,str(date),weekday,int(recurring)))
    st.success("Додано 😏")

# -------------------------
# DATA
# -------------------------
df = get_df()
budgets = get_budgets()

if df.empty:
    st.info("Нема даних")
    st.stop()

user_df = df[df.user == user]

# -------------------------
# KPIs
# -------------------------
income = user_df[user_df.type=="Дохід"].amount.sum()
expense = user_df[user_df.type=="Витрата"].amount.sum()
balance = income - expense

c1,c2,c3 = st.columns(3)
c1.metric("💰 Дохід", income)
c2.metric("💸 Витрати", expense)
c3.metric("📊 Баланс", balance)

if balance < 0:
    st.error("⚠️ Мінус бюджет!")

st.divider()

# -------------------------
# AI INSIGHT (простий rule-based)
# -------------------------
st.subheader("🧠 Інсайти")

avg_food = user_df[user_df.category=="Їжа"]["amount"].mean()

if avg_food > 500:
    st.warning("Ти витрачаєш забагато на їжу 😏")

if user_df[user_df.recurring==1].amount.sum() > 1000:
    st.info("Є великі повторювані платежі — перевір підписки")

# -------------------------
# WEEK ANALYTICS
# -------------------------
st.subheader("📅 Витрати по днях")

st.line_chart(user_df.groupby("weekday")["amount"].sum())

# -------------------------
# CATEGORY
# -------------------------
st.subheader("📊 Категорії")

st.bar_chart(user_df[user_df.type=="Витрата"].groupby("category")["amount"].sum())

# -------------------------
# CALENDAR VIEW (простий)
# -------------------------
st.subheader("📆 Останні дні")

st.dataframe(user_df.sort_values("date", ascending=False).head(20))

# -------------------------
# RECURRING
# -------------------------
st.subheader("🔁 Повторювані платежі")

st.dataframe(user_df[user_df.recurring==1])

# -------------------------
# BUDGET CONTROL
# -------------------------
st.subheader("🎯 Бюджети")

cat = st.selectbox("Категорія бюджету", ["Їжа","Дім","Транспорт","Розваги","Здоров'я","Інше"])
limit = st.number_input("Ліміт", min_value=0.0)

if st.button("Зберегти бюджет"):
    c.execute("""
    INSERT OR REPLACE INTO budgets VALUES (?,?,?)
    """, (user,cat,limit))
    conn.commit()

bud_df = budgets[budgets.user==user]
st.dataframe(bud_df)

# -------------------------
# ALERTS
# -------------------------
st.subheader("⚠️ Контроль бюджету")

for _, b in bud_df.iterrows():
    spent = user_df[user_df.category==b.category]["amount"].sum()
    if spent > b.limit_amount:
        st.error(f"{b.category}: перевищено {spent}/{b.limit_amount}")
    else:
        st.write(f"{b.category}: {spent}/{b.limit_amount}")

# -------------------------
# EXPORT
# -------------------------
st.download_button(
    "⬇️ Експорт CSV",
    user_df.to_csv(index=False),
    file_name="wallet_v3.csv"
)