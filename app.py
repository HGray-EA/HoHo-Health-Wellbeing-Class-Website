import os
import sqlite3
import stripe
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

DATABASE = "yoga.db"


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                date TEXT,
                price INTEGER
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER,
                email TEXT,
                FOREIGN KEY(class_id) REFERENCES classes(id)
            )
        """)
        conn.commit()


@app.route("/")
def index():
    with sqlite3.connect(DATABASE) as conn:
        classes = conn.execute("SELECT * FROM classes").fetchall()
    return render_template("index.html", classes=classes)


@app.route("/checkout/<int:class_id>", methods=["POST"])
def checkout(class_id):
    email = request.form["email"]

    with sqlite3.connect(DATABASE) as conn:
        yoga_class = conn.execute(
            "SELECT * FROM classes WHERE id = ?", (class_id,)
        ).fetchone()

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": yoga_class[1]},
                "unit_amount": yoga_class[3],
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=url_for("success", class_id=class_id, email=email, _external=True),
        cancel_url=url_for("index", _external=True),
    )

    return redirect(session.url)


@app.route("/success")
def success():
    class_id = request.args.get("class_id")
    email = request.args.get("email")

    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            "INSERT INTO bookings (class_id, email) VALUES (?, ?)",
            (class_id, email),
        )
        conn.commit()

    return render_template("success.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        title = request.form["title"]
        date = request.form["date"]
        price = int(float(request.form["price"]) * 100)

        with sqlite3.connect(DATABASE) as conn:
            conn.execute(
                "INSERT INTO classes (title, date, price) VALUES (?, ?, ?)",
                (title, date, price),
            )
            conn.commit()

        return redirect(url_for("admin"))

    return render_template("admin.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
