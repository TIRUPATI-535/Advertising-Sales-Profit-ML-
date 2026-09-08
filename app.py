import os
import pickle
import requests
import psycopg

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash


# Load environment variables
load_dotenv()


app = Flask(__name__)

# Secret key
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")


# -------------------------------
# Load ML Model
# -------------------------------

with open("Advertising_model.pkl", "rb") as file:
    model = pickle.load(file)


# -------------------------------
# OpenRouter AI
# -------------------------------

# -------------------------------
# OpenRouter AI
# -------------------------------

def get_ai_analysis(tv, radio, newspaper, prediction):

    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        return "AI analysis is currently unavailable."

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Linear Regression coefficients
    tv_coefficient = 0.04472952
    radio_coefficient = 0.18919505
    newspaper_coefficient = 0.00276111

    prompt = f"""
You are an AI sales analysis assistant for an Advertising Sales Prediction system.

The system uses a Linear Regression machine learning model.

Advertising spending:
- TV: {tv}
- Radio: {radio}
- Newspaper: {newspaper}

Predicted sales:
- {prediction} units

Model coefficients:
- TV coefficient: {tv_coefficient}
- Radio coefficient: {radio_coefficient}
- Newspaper coefficient: {newspaper_coefficient}

Important:
Do NOT say that the channel with the highest spending is automatically the most influential.
Use the model coefficients to identify which advertising channel has the strongest relationship with predicted sales.

Give the response in this exact simple structure:

Prediction Summary:
Briefly explain the predicted sales.

Most Influential Channel:
Mention the channel with the strongest model coefficient and explain it simply.

Advertising Spend:
Mention which channel currently has the highest spending.

Recommendations:
Give exactly 2 short and practical recommendations based on the model and current spending.

Keep the complete response concise, professional, and easy to understand.
Do not use complicated mathematical terminology.
"""

    data = {
        "model": "openrouter/free",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code != 200:
            print("OpenRouter Error:", response.text)
            return "AI analysis could not be generated."

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except Exception as e:

        print("OpenRouter Error:", e)

        return "AI analysis could not be generated."
# -------------------------------
# Database Connection
# -------------------------------

def get_db():

    database_url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("POSTGRES_PRISMA_URL")
        or os.environ.get("POSTGRES_URL_NON_POOLING")
    )

    if not database_url:
        raise RuntimeError("No PostgreSQL connection found.")

    db = psycopg.connect(database_url)

    with db.cursor() as cursor:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                tv REAL,
                radio REAL,
                newspaper REAL,
                predicted_sales REAL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)

    db.commit()

    return db


# -------------------------------
# Home Page
# -------------------------------

@app.route("/")
def home():

    return redirect(url_for("signup"))


# -------------------------------
# Dashboard
# -------------------------------

@app.route("/dashboard", methods=["GET", "POST"])
def index():

    if "user_id" not in session:
        return redirect(url_for("login"))

    prediction = None
    ai_analysis = None

    if request.method == "POST":

        tv = float(request.form["tv"])
        radio = float(request.form["radio"])
        newspaper = float(request.form["newspaper"])

        # Model expects:
        # TV, Radio, Newspaper
        result = model.predict([[tv, radio, newspaper]])

        prediction = round(float(result[0]), 2)

        # Get AI analysis
        ai_analysis = get_ai_analysis(
            tv,
            radio,
            newspaper,
            prediction
        )

        # Save prediction
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO predictions
            (user_id, tv, radio, newspaper, predicted_sales)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                tv,
                radio,
                newspaper,
                prediction
            )
        )

        conn.commit()

        cur.close()
        conn.close()

    return render_template(
        "index.html",
        prediction=prediction,
        ai_analysis=ai_analysis
    )


# -------------------------------
# Login
# -------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, full_name, password_hash FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect(url_for("index"))

        flash("Invalid email or password")

    return render_template("login.html")


# -------------------------------
# Signup
# -------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        try:

            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO users
                (full_name, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (
                    name,
                    email,
                    password_hash
                )
            )

            conn.commit()

            cur.close()
            conn.close()

            flash("Account created successfully!")

            return redirect(url_for("login"))

        except Exception as e:

            print(e)

            flash("Email already registered.")

    return render_template("signup.html")


# -------------------------------
# Logout
# -------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# -------------------------------
# Run App
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True)