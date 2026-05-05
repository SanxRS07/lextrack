from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "lextrack_secret"

# OpenAI client
client = OpenAI()

# Initialize database
def init_db():
    with sqlite3.connect('database.db', timeout=10) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                case_number TEXT,
                court_name TEXT,
                status TEXT,
                next_hearing TEXT
            )
        ''')

init_db()

# 🔥 HYBRID AI FUNCTION
def get_legal_response(query):
    try:
        # Try real AI first
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful legal assistant. Explain legal concepts in simple words for Indian users."
                },
                {"role": "user", "content": query}
            ],
            max_tokens=150
        )

        return response.choices[0].message.content

    except:
        # 🔁 FALLBACK (works even without API)
        query = query.lower()

        if any(word in query for word in ["bail", "release", "jail"]):
            return "Bail is the temporary release of an accused person while the case is still in court."

        elif any(word in query for word in ["fir", "complaint", "report"]):
            return "An FIR (First Information Report) is filed when police receive information about a serious offence."

        elif any(word in query for word in ["court", "hearing", "trial"]):
            return "A court hearing is a legal proceeding where both sides present their arguments before a judge."

        elif any(word in query for word in ["status", "case progress"]):
            return "Case status shows the current stage of your legal case."

        elif any(word in query for word in ["lawyer", "advocate"]):
            return "A lawyer (advocate) represents you in court and provides legal advice."

        else:
            return "AI service unavailable right now. Try asking about bail, FIR, court hearing, or legal process."

# Home
@app.route('/')
def home():
    return render_template("index.html")

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            with sqlite3.connect('database.db', timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password)
                )
                conn.commit()
        except:
            return "User already exists"

        return redirect(url_for('login'))

    return render_template("signup.html")

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('database.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )
            user = cursor.fetchone()

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Credentials"

    return render_template("login.html")

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template("dashboard.html", username=session['username'])
    return redirect(url_for('login'))

# Add Case
@app.route('/add_case', methods=['GET', 'POST'])
def add_case():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = session['username']
        case_number = request.form['case_number']
        court_name = request.form['court_name']
        status = request.form['status']
        next_hearing = request.form['next_hearing']

        with sqlite3.connect('database.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cases (username, case_number, court_name, status, next_hearing)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, case_number, court_name, status, next_hearing))
            conn.commit()

        return redirect(url_for('dashboard'))

    return render_template("add_case.html")

# View Cases
@app.route('/view_cases')
def view_cases():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    with sqlite3.connect('database.db', timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE username=?", (username,))
        cases = cursor.fetchall()

    return render_template("view_cases.html", cases=cases)

# AI Chat
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    response = None

    if request.method == 'POST':
        query = request.form['query']
        response = get_legal_response(query)

    return render_template("chat.html", response=response)

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# Run
if __name__ == '__main__':
    app.run(debug=True)