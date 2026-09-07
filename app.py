
import os
import pickle
import psycopg

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# Secret key
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")

# Database URL from Neon / Vercel
DATABASE_URL = os.environ.get("DATABASE_URL")


# -------------------------------
# Load ML Model
# -------------------------------

with open("Advertising_model.pkl", "rb") as file:
    model = pickle.load(file)


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
        raise RuntimeError(
            "No PostgreSQL connection found."
        )

    return psycopg.connect(database_url)


# -------------------------------
# Dashboard
# -------------------------------

@app.route("/", methods=["GET", "POST"])
def index():

    if "user_id" not in session:
        return redirect(url_for("login"))

    prediction = None

    if request.method == "POST":

        tv = float(request.form["tv"])
        radio = float(request.form["radio"])
        newspaper = float(request.form["newspaper"])

        # Model expects:
        # TV, Radio, Newspaper
        result = model.predict([[tv, radio, newspaper]])

        prediction = round(float(result[0]), 2)

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
        prediction=prediction
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

