
import streamlit as st
from datetime import date

import sqlite3

# Connect to Database
conn = sqlite3.connect(
    "money_manager.db",
    timeout=30,
    check_same_thread=False
)
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
# Create Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

conn.commit()
conn.commit()

st.set_page_config(page_title="Smart Money Manager", page_icon="💰")
# =====================================
# PROFESSIONAL LOGIN & REGISTER PAGE
# =====================================

import hashlib

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        }
        .login-title {
            text-align: center;
            color: white;
            font-size: 38px;
            font-weight: bold;
        }
        .login-subtitle {
            text-align: center;
            color: #d6e4e8;
            font-size: 17px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="login-title">💰 Smart Money Manager</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitle">Manage your money. Build your future.</div>',
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    left, center, right = st.columns([1, 2, 1])

    with center:

        st.markdown("### Welcome Back 👋")
        st.write("Login or create your account to continue.")

        login_tab, register_tab = st.tabs(
            ["🔐 Login", "📝 Register"]
        )

        with login_tab:

            with st.form("login_form"):

                username = st.text_input("Username")
                password = st.text_input(
                    "Password",
                    type="password"
                )

                login_button = st.form_submit_button(
                    "Login",
                    use_container_width=True
                )

                if login_button:

                    password_hash = hashlib.sha256(
                        password.encode()
                    ).hexdigest()

                    cursor.execute(
                        "SELECT password FROM users WHERE username = ?",
                        (username.strip(),)
                    )

                    result = cursor.fetchone()

                    if result and result[0] == password_hash:

                        st.session_state.logged_in = True
                        st.session_state.current_user = username.strip()

                        st.success("Login Successful!")
                        st.rerun()

                    else:
                        st.error("Invalid username or password.")

        with register_tab:

            with st.form("register_form"):

                new_username = st.text_input("Create Username")

                new_password = st.text_input(
                    "Create Password",
                    type="password"
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password"
                )

                register_button = st.form_submit_button(
                    "Create Account",
                    use_container_width=True
                )

                if register_button:

                    if not new_username.strip() or not new_password:
                        st.warning("Please fill all fields.")

                    elif len(new_password) < 6:
                        st.warning("Password must be at least 6 characters.")

                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")

                    else:

                        password_hash = hashlib.sha256(
                            new_password.encode()
                        ).hexdigest()

                        try:
                            cursor.execute(
                                """
                                INSERT INTO users (username, password)
                                VALUES (?, ?)
                                """,
                                (new_username.strip(), password_hash)
                            )

                            conn.commit()

                            st.success("Account created successfully! Please login.")

                        except sqlite3.IntegrityError:
                            st.error("Username already exists.")

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

# ==========================================
# SMART MONEY ASSISTANT - DETAILED CHATBOT
# ==========================================

st.header("🤖 Smart Money Assistant")

st.write(
    "Ask any money-related question. "
    "Get detailed explanations, examples and practical suggestions."
)

def has_word(question, keywords):
    return any(word in question for word in keywords)

  
def get_money_answer(user_question):

    q = user_question.lower().strip()

    kannada = any(
        "\u0c80" <= char <= "\u0cff"
        for char in q
    )

    current_month = date.today().strftime("%Y-%m")

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE username = ?
        AND type = 'Expense'
        AND substr(date, 1, 7) = ?
    """, (st.session_state.current_user, current_month))

    monthly = float(cursor.fetchone()[0])

    income = float(total_income)
    expenses = float(total_expense)
    current_balance = float(balance)

    spending_ratio = (expenses / income * 100) if income > 0 else 0

    financial_summary = (
        f"Your total income is ₹{income:,.2f}, "
        f"total expenses are ₹{expenses:,.2f}, "
        f"and your balance is ₹{current_balance:,.2f}."
    )

    # Identify question category

    if has_word(q, ["reduce my monthly expenses",
                    "reduce monthly expenses",
                    "cut monthly expenses",
                    "lower monthly expenses",
                    "monthly spending"]):
        topic = "reduce_expense"

    elif has_word(q, ["manage my daily expenses",
                      "daily expenses",
                      "daily spending",
                      "track daily expenses"]):
        topic = "daily_expense"

    elif has_word(q, ["balance", "remaining", "left money",
                      "ಉಳಿದ ಹಣ", "ಬ್ಯಾಲೆನ್ಸ್"]):
        topic = "balance"

    elif has_word(q, ["income", "salary", "earning",
                      "ಆದಾಯ", "ಸಂಬಳ"]):
        topic = "income"

    elif has_word(q, ["save", "saving", "savings",
                      "ಉಳಿತಾಯ", "ಉಳಿಸು"]):
        topic = "saving"

    elif has_word(q, ["budget", "budgeting", "ಬಜೆಟ್"]):
        topic = "budget"

    elif has_word(q, ["invest", "investment", "investing",
                      "ಹೂಡಿಕೆ"]):
        topic = "investment"

    elif has_word(q, ["debt", "loan", "borrow", "interest",
                      "ಸಾಲ", "ಬಡ್ಡಿ"]):
        topic = "debt"

    elif has_word(q, ["emergency fund", "emergency savings",
                      "ತುರ್ತು ನಿಧಿ"]):
        topic = "emergency"

    elif has_word(q, ["expense", "expenses", "spending",
                      "spent", "spend", "ಖರ್ಚು", "ವೆಚ್ಚ"]):
        topic = "expense"

    elif has_word(q, ["financial status", "financial health",
                      "financial condition", "analyze"]):
        topic = "analysis"

    else:
        topic = "general"

    # English answers

    english_answers = {

        "balance": (
            f"{financial_summary}\n\n"
            "Keep some money aside for upcoming bills "
            "and emergencies."
        ),

        "reduce_expense": (
            "Here are 5 ways to reduce your monthly expenses:\n\n"
            "1. Create a monthly budget.\n"
            "2. Cancel unused subscriptions.\n"
            "3. Avoid unnecessary shopping.\n"
            "4. Compare prices before buying.\n"
            "5. Reduce eating out and cook at home.\n\n"
            "My suggestion: Try reducing your monthly expenses "
            "by 10% next month."
        ),

        "daily_expense": (
            "Here are 5 ways to manage your daily expenses:\n\n"
            "1. Set a daily spending limit.\n"
            "2. Record every purchase.\n"
            "3. Separate needs from wants.\n"
            "4. Check your expenses every evening.\n"
            "5. Follow your daily budget.\n\n"
            "My suggestion: Track every rupee you spend "
            "to understand your daily spending habits."
        ),

        "income": (
            f"Here is your income summary.\n\n{financial_summary}\n\n"
            "Record your salary and other income regularly."
        ),

        "expense": (
            f"Here is your expense summary.\n\n{financial_summary}\n"
            f"\nYour expenses this month are ₹{monthly:,.2f}.\n\n"
            "Review your spending and reduce unnecessary purchases."
        ),

        "saving": (
            "Start saving a small amount every month.\n\n"
            "For example, saving ₹1,000 monthly gives you "
            "₹12,000 in one year. Increase your savings gradually."
        ),

        "budget": (
            f"{financial_summary}\n\n"
            "Divide your income into rent, food, travel, bills "
            "and savings. Follow your budget every month."
        ),

        "investment": (
            "Before investing, understand the risks and charges. "
            "Build emergency savings first. Avoid schemes "
            "promising guaranteed high returns."
        ),

        "debt": (
            "List all your loans, interest rates and due dates. "
            "Pay instalments on time and avoid unnecessary new loans."
        ),

        "emergency": (
            "An emergency fund helps during unexpected situations. "
            "Gradually try to save enough for 3–6 months of essential expenses."
        ),

        "analysis": (
            f"Your financial analysis:\n\n{financial_summary}\n\n"
            f"Your expenses are {spending_ratio:.1f}% of your income.\n"
            f"This month's expenses are ₹{monthly:,.2f}.\n\n"
            "Review your spending and set a monthly savings goal."
        ),

        "general": (
            "I am your Smart Money Assistant!\n\n"
            "I can help with savings, expenses, budgeting, "
            "income, investments and financial planning.\n\n"
            "Please ask a specific money-related question."
        )
    }

    # Kannada answers

    kannada_answers = {

        "balance": (
            f"ನಿಮ್ಮ ಹಣದ ವಿವರ:\n\n{financial_summary}\n\n"
            "ಉಳಿದ ಹಣವನ್ನು ಸಂಪೂರ್ಣ ಖರ್ಚು ಮಾಡದೆ ಸ್ವಲ್ಪ ಉಳಿತಾಯ ಮಾಡಿ."
        ),

        "reduce_expense": (
            "ತಿಂಗಳ ಖರ್ಚು ಕಡಿಮೆ ಮಾಡಲು 5 ಸಲಹೆಗಳು:\n\n"
            "1. ತಿಂಗಳ ಬಜೆಟ್ ತಯಾರಿಸಿ.\n"
            "2. ಬೇಡದ subscriptions ರದ್ದು ಮಾಡಿ.\n"
            "3. ಅನಗತ್ಯ shopping ಕಡಿಮೆ ಮಾಡಿ.\n"
            "4. ಖರೀದಿಸುವ ಮೊದಲು ಬೆಲೆ ಹೋಲಿಕೆ ಮಾಡಿ.\n"
            "5. ಹೊರಗಿನ ಊಟದ ಖರ್ಚು ಕಡಿಮೆ ಮಾಡಿ.\n\n"
            "ಮುಂದಿನ ತಿಂಗಳು ಖರ್ಚನ್ನು 10% ಕಡಿಮೆ ಮಾಡುವ ಗುರಿ ಇಡಿ."
        ),

        "daily_expense": (
            "ದಿನನಿತ್ಯದ ಖರ್ಚು ನಿರ್ವಹಿಸಲು 5 ಸಲಹೆಗಳು:\n\n"
            "1. ಪ್ರತಿದಿನದ ಖರ್ಚಿಗೆ ಮಿತಿ ಇಡಿ.\n"
            "2. ಪ್ರತಿಯೊಂದು ಖರೀದಿಯನ್ನು ದಾಖಲಿಸಿ.\n"
            "3. ಅಗತ್ಯ ಮತ್ತು ಅನಗತ್ಯ ಖರ್ಚು ಬೇರ್ಪಡಿಸಿ.\n"
            "4. ಪ್ರತಿದಿನ ಸಂಜೆ ಖರ್ಚು ಪರಿಶೀಲಿಸಿ.\n"
            "5. ನಿಮ್ಮ ದಿನದ ಬಜೆಟ್ ಪಾಲಿಸಿ.\n\n"
            "ಪ್ರತಿ ರೂಪಾಯಿ ಎಲ್ಲಿ ಖರ್ಚಾಗುತ್ತಿದೆ ಎಂದು ಗಮನಿಸಿ."
        ),

        "income": (
            f"ನಿಮ್ಮ ಆದಾಯದ ವಿವರ:\n\n{financial_summary}\n\n"
            "ಪ್ರತಿ ತಿಂಗಳು ನಿಮ್ಮ ಆದಾಯವನ್ನು ದಾಖಲಿಸಿ."
        ),

        "expense": (
            f"ನಿಮ್ಮ ಖರ್ಚಿನ ವಿವರ:\n\n{financial_summary}\n"
            f"\nಈ ತಿಂಗಳ ಖರ್ಚು ₹{monthly:,.2f}.\n\n"
            "ಅನಗತ್ಯ ಖರ್ಚುಗಳನ್ನು ಕಡಿಮೆ ಮಾಡಿ."
        ),

        "saving": (
            "ಪ್ರತಿ ತಿಂಗಳು ಸ್ವಲ್ಪ ಹಣ ಉಳಿತಾಯ ಮಾಡಿ. "
            "ಉದಾಹರಣೆಗೆ ತಿಂಗಳಿಗೆ ₹1,000 ಉಳಿಸಿದರೆ "
            "ವರ್ಷಕ್ಕೆ ₹12,000 ಆಗುತ್ತದೆ."
        ),

        "budget": (
            f"{financial_summary}\n\n"
            "ನಿಮ್ಮ ಆದಾಯವನ್ನು ಮನೆ, ಆಹಾರ, ಪ್ರಯಾಣ, ಬಿಲ್ "
            "ಮತ್ತು ಉಳಿತಾಯಕ್ಕೆ ಹಂಚಿಕೊಳ್ಳಿ."
        ),

        "investment": (
            "ಹೂಡಿಕೆ ಮಾಡುವ ಮೊದಲು ಅಪಾಯ ಮತ್ತು ಲಾಭ ತಿಳಿದುಕೊಳ್ಳಿ. "
            "ಮೊದಲು ತುರ್ತು ನಿಧಿ ಸಂಗ್ರಹಿಸಿ."
        ),

        "debt": (
            "ನಿಮ್ಮ ಸಾಲ, ಬಡ್ಡಿ ಮತ್ತು ಕಂತಿನ ದಿನಾಂಕಗಳನ್ನು ದಾಖಲಿಸಿ. "
            "ಸಾಲದ ಕಂತುಗಳನ್ನು ಸಮಯಕ್ಕೆ ಪಾವತಿಸಿ."
        ),

        "emergency": (
            "ತುರ್ತು ನಿಧಿ ಅನಿರೀಕ್ಷಿತ ಖರ್ಚುಗಳಿಗೆ ಸಹಾಯ ಮಾಡುತ್ತದೆ. "
            "ನಿಧಾನವಾಗಿ 3–6 ತಿಂಗಳ ಅಗತ್ಯ ಖರ್ಚಿಗೆ ಸಾಕಾಗುವಷ್ಟು ಹಣ ಉಳಿಸಿ."
        ),

        "analysis": (
            f"ನಿಮ್ಮ ಹಣಕಾಸಿನ ವಿಶ್ಲೇಷಣೆ:\n\n{financial_summary}\n\n"
            f"ನಿಮ್ಮ ಆದಾಯದಲ್ಲಿ ಖರ್ಚಿನ ಪ್ರಮಾಣ {spending_ratio:.1f}%.\n"
            f"ಈ ತಿಂಗಳ ಖರ್ಚು ₹{monthly:,.2f}."
        ),

        "general": (
            "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ Smart Money Assistant.\n\n"
            "ಉಳಿತಾಯ, ಖರ್ಚು, ಬಜೆಟ್, ಆದಾಯ ಮತ್ತು ಹೂಡಿಕೆ "
            "ವಿಷಯಗಳಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ."
        )
    }

    if kannada:
        answer = kannada_answers.get(topic, kannada_answers["general"])
    else:
        answer = english_answers.get(topic, english_answers["general"])

    return answer


# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat Input
user_question = st.chat_input(
    "Ask any money-related question..."
)

if user_question:

    st.session_state.messages.append({
        "role": "user",
        "content": user_question
    })

    answer = get_money_answer(user_question)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.rerun()
import csv
import io
import csv
import io

st.header("📥 Download Your Money Report")

cursor.execute("""
    SELECT type, amount, description, date
    FROM transactions
    WHERE username = ?
    ORDER BY date DESC
""", (st.session_state.current_user,))

rows = cursor.fetchall()

if rows:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Type", "Amount", "Description", "Date"])
    writer.writerows(rows)

    csv_data = output.getvalue().encode("utf-8-sig")

    st.download_button(
        label="Download Report",
        data=csv_data,
        file_name="money_report.csv",
        mime="text/csv"
    )
else:
    st.info("Please add transactions before downloading the report.")