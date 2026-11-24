
import streamlit as st
from datetime import date

import sqlite3

# Connect to Database
conn = sqlite3.connect("money_manager.db")
cursor = conn.cursor()

# Create Transactions Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    type TEXT,
    amount REAL,
    description TEXT,
    date TEXT
)
""")

conn.commit()

st.set_page_config(page_title="Smart Money Manager", page_icon="💰")

# Login and Registration System

import hashlib

if "users" not in st.session_state:
    st.session_state.users = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🔐 Smart Money Manager Login")

    login_tab, register_tab = st.tabs(
        ["Login", "Register"]
    )

    with register_tab:
        st.subheader("Create New Account")

        new_username = st.text_input(
            "Create Username",
            key="new_user"
        )

        new_password = st.text_input(
            "Create Password",
            type="password",
            key="new_pass"
        )

        if st.button("Register"):
            if new_username and new_password:
                if new_username in st.session_state.users:
                    st.error("Username already exists!")
                else:
                    password_hash = hashlib.sha256(
                        new_password.encode()
                    ).hexdigest()

                    st.session_state.users[new_username] = password_hash
                    st.success("Registration successful!")
            else:
                st.warning("Enter username and password.")

    with login_tab:
        st.subheader("Login to Your Account")

        username = st.text_input(
            "Username",
            key="login_user"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_pass"
        )

        if st.button("Login"):
            password_hash = hashlib.sha256(
                password.encode()
            ).hexdigest()

            if st.session_state.users.get(username) == password_hash:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.rerun()
            else:
                st.error("Invalid username or password!")

    st.stop()

# User Welcome and Logout

if st.session_state.logged_in:
    st.sidebar.success(
        f"Welcome, {st.session_state.current_user}!"
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

st.title("💰 Smart Money Manager")

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "messages" not in st.session_state:
    st.session_state.messages = []

# Add Transaction
st.header("➕ Add Transaction")

transaction_type = st.selectbox(
    "Select Transaction Type",
    ["Income", "Expense"]
)

amount = st.number_input(
    "Enter Amount (₹)",
    min_value=0.0,
    step=100.0
)

description = st.text_input("Description")
transaction_date = st.date_input("Transaction Date", date.today())

if st.button("Add Transaction"):
    if amount > 0:
        cursor.execute(
            """
            INSERT INTO transactions
            (username, type, amount, description, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                st.session_state.current_user,
                transaction_type,
                amount,
                description,
                str(transaction_date)
            )
        )

        conn.commit()

        st.success("Transaction Saved Successfully!")
    else:
        st.warning("Please enter an amount greater than 0.")


# Calculate Summary from Database

cursor.execute(
    """
    SELECT
        COALESCE(SUM(CASE WHEN type = 'Income'
        THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN type = 'Expense'
        THEN amount ELSE 0 END), 0)
    FROM transactions
    WHERE username = ?
    """,
    (st.session_state.current_user,)
)

total_income, total_expense = cursor.fetchone()

balance = total_income - total_expense

# Display Money Summary

st.header("💵 Money Summary")

st.write(f"Total Income: ₹{total_income:,.2f}")
st.write(f"Total Expense: ₹{total_expense:,.2f}")

st.success(f"Remaining Balance: ₹{balance:,.2f}")

# Transaction History
st.header("📊 Transaction History")

for t in st.session_state.transactions:
    st.write(
        t["Date"], "|", t["Type"],
        "| ₹", t["Amount"], "|", t["Description"]
    )

# Money Summary
st.header("💵 Money Summary")
st.write(f"Total Income: ₹{total_income:,.2f}")
st.write(f"Total Expense: ₹{total_expense:,.2f}")
st.success(f"Remaining Balance: ₹{balance:,.2f}")

# Monthly Expense Report
st.header("📅 Monthly Expense Report")

monthly_expenses = {}

for t in st.session_state.transactions:
    if t["Type"] == "Expense":
        month = t["Date"][:7]
        monthly_expenses[month] = (
            monthly_expenses.get(month, 0) + t["Amount"]
        )

if monthly_expenses:
    st.bar_chart(monthly_expenses)
else:
    st.info("No expense records available yet.")

# Chatbot
st.header("🤖 Money Assistant Chatbot")

st.write("Ask me about your money!")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_question = st.chat_input("Ask your money question...")

if user_question:
    st.session_state.messages.append({
        "role": "user",
        "content": user_question
    })

    question = user_question.lower()

    if "balance" in question:
        answer = f"Your current balance is ₹{balance:,.2f}."

    elif "income" in question:
        answer = f"Your total income is ₹{total_income:,.2f}."

    elif "expense" in question or "spend" in question:
        answer = f"Your total expense is ₹{total_expense:,.2f}."

    elif "saving" in question or "save" in question:
        answer = (
            "Saving Tip: Try to save at least 20% of your income. "
            "Avoid unnecessary expenses and track your spending."
        )

    elif "hello" in question or "hi" in question:
        answer = "Hello! Welcome to Smart Money Manager. How can I help you?"

    else:
        answer = (
            "I can help you with balance, income, expenses "
            "and saving tips. Please ask me about these topics."
        )

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.rerun()


# Download Transaction Report

import csv
import io

st.header("📥 Download Your Money Report")

if st.session_state.transactions:
    output = io.StringIO()

    fieldnames = [
        "Type",
        "Amount",
        "Description",
        "Date"
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(st.session_state.transactions)

    csv_data = output.getvalue().encode("utf-8-sig")

    st.download_button(
        label="Download Report",
        data=csv_data,
        file_name="money_report.csv",
        mime="text/csv"
    )
else:
    st.info("Please add transactions before downloading the report.")
