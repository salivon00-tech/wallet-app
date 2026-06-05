import streamlit as st

st.title("💰 Wallet App")
st.write("Твій фінансовий застосунок запущено 😏")

income = st.number_input("Дохід", min_value=0)
expense = st.number_input("Витрати", min_value=0)

balance = income - expense

st.metric("Баланс", balance)