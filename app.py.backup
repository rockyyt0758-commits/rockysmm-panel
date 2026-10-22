import os
import sqlite3
import hashlib
from functools import wraps
from flask import Flask, request, redirect, session, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deployment")
DB = os.path.join(os.path.dirname(__file__), "panel.db")

SERVICES = {
    "Instagram campaign management": 50,
    "YouTube promotion campaign": 100,
    "Social media analytics report": 30
}

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

with connect() as db:
    db.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        balance REAL DEFAULT 0
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        service TEXT,
        quantity INTEGER,
        amount REAL,
        status TEXT DEFAULT 'Pending'
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        utr TEXT,
        status TEXT DEFAULT 'Pending'
    )""")

PAGE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ROCKYSMM PANEL</title>
<style>
body{margin:0;background:#0b1020;color:#fff;font-family:Arial}
header{background:#171f38;padding:20px;text-align:center}
main{max-width:700px;margin:25px auto;padding:18px}
.card{background:#171f38;border:1px solid #303b5c;border-radius:15px;padding:18px;margin:14px 0}
input,select,button{box-sizing:border-box;width:100%;padding:12px;margin:7px 0;border-radius:8px;border:1px solid #536080}
button{background:#7c4dff;color:white;font-weight:bold}
a{color:#b9a4ff}small{color:#c6cbe0}
</style>
</head>
<body>
<header><h1>👑 ROCKYSMM PANEL</h1><small>Social Media Service Dashboard</small></header>
<main>{{ content|safe }}</main>
</body></html>
"""

def page(content):
    return render_template_string(PAGE, content=content)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "uid" not in session:
            return redirect("/login")
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    if "uid" in session:
        return redirect("/dashboard")
    return page("""
    <div class="card"><h2>Welcome!</h2>
    <p>Manage your social media marketing orders.</p>
    <a href="/register">Create Account</a> |
    <a href="/login">Login</a></div>
    """)

@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        name = request.form.get("username", "").strip()
        pw = request.form.get("password", "")
        if len(name) < 3 or len(pw) < 8:
            msg = "Username: 3+ characters; password: 8+ characters."
        else:
            try:
                with connect() as db:
                    db.execute("INSERT INTO users(username,password) VALUES(?,?)",
                               (name, hashlib.sha256(pw.encode()).hexdigest()))
                return redirect("/login")
            except sqlite3.IntegrityError:
                msg = "Username already exists."
    return page(f"""<div class="card"><h2>Sign Up</h2><p>{msg}</p>
    <form method="post"><input name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password (8+ characters)" required>
    <button>Create Account</button></form><a href="/login">Login</a></div>""")

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        name = request.form.get("username", "")
        pw = hashlib.sha256(request.form.get("password", "").encode()).hexdigest()
        with connect() as db:
            user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                              (name, pw)).fetchone()
        if user:
            session.clear()
            session["uid"] = user["id"]
            return redirect("/dashboard")
        msg = "Login failed. Check your details."
    return page(f"""<div class="card"><h2>Login</h2><p>{msg}</p>
    <form method="post"><input name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button>Login</button></form><a href="/register">Create account</a></div>""")

@app.route("/dashboard")
@login_required
def dashboard():
    with connect() as db:
        user = db.execute("SELECT * FROM users WHERE id=?",
                          (session["uid"],)).fetchone()
        orders = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",
                            (session["uid"],)).fetchall()
        payments = db.execute("SELECT * FROM payments WHERE user_id=? ORDER BY id DESC",
                              (session["uid"],)).fetchall()

    services = "".join(
        f"<option value='{name}'>{name} — ₹{price} base price</option>"
        for name, price in SERVICES.items()
    )
    history = "".join(
        f"<p>Order #{o['id']} · {o['service']} · {o['quantity']} units · ₹{o['amount']} · {o['status']}</p>"
        for o in orders
    ) or "<p>No orders yet.</p>"
    payhistory = "".join(
        f"<p>Payment #{p['id']} · ₹{p['amount']} · {p['status']}</p>"
        for p in payments
    ) or "<p>No payment requests.</p>"

    return page(f"""
    <div class="card"><h2>Hello, {user['username']}</h2>
    <h3>Wallet: ₹{user['balance']:.2f}</h3><a href="/logout">Logout</a></div>
    <div class="card"><h2>New Order</h2>
    <form method="post" action="/order">
    <select name="service">{services}</select>
    <input type="number" name="quantity" min="1" max="10000" value="1" required>
    <button>Submit Demo Order</button></form>
    <small>Orders are recorded for admin review; no automatic social-media actions occur.</small></div>
    <div class="card"><h2>UPI Payment Request</h2>
    <p>Pay only to the verified UPI ID shown by the site owner.</p>
    <form method="post" action="/payment">
    <input type="number" step="1" min="1" name="amount" placeholder="Amount in ₹" required>
    <input name="utr" placeholder="UPI transaction reference (UTR)" required>
    <button>Request Payment Verification</button></form>
    <small>Keep your payment receipt. Balance is added only after admin verification.</small></div>
    <div class="card"><h2>My Orders</h2>{history}</div>
    <div class="card"><h2>My Payments</h2>{payhistory}</div>
    """)

@app.route("/order", methods=["POST"])
@login_required
def order():
    service = request.form.get("service", "")
    try:
        qty = int(request.form.get("quantity", "0"))
    except ValueError:
        return "Invalid quantity", 400
    if service not in SERVICES or not 1 <= qty <= 10000:
        return "Invalid order", 400
    amount = SERVICES[service] * qty
    with connect() as db:
        db.execute("INSERT INTO orders(user_id,service,quantity,amount) VALUES(?,?,?,?)",
                   (session["uid"], service, qty, amount))
    return redirect("/dashboard")

@app.route("/payment", methods=["POST"])
@login_required
def payment():
    try:
        amount = int(request.form.get("amount", "0"))
    except ValueError:
        return "Invalid amount", 400
    utr = request.form.get("utr", "").strip()
    if not 1 <= amount <= 100000 or not 6 <= len(utr) <= 80:
        return "Invalid payment request", 400
    with connect() as db:
        db.execute("INSERT INTO payments(user_id,amount,utr) VALUES(?,?,?)",
                   (session["uid"], amount, utr))
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin")
def admin():
    if not os.environ.get("ADMIN_KEY"):
        return "Admin key is not configured.", 503
    if request.args.get("key") != os.environ["ADMIN_KEY"]:
        return "Forbidden", 403
    with connect() as db:
        payments = db.execute("""
            SELECT payments.*, users.username FROM payments
            JOIN users ON users.id=payments.user_id
            ORDER BY payments.id DESC
        """).fetchall()
        orders = db.execute("""
            SELECT orders.*, users.username FROM orders
            JOIN users ON users.id=orders.user_id
            ORDER BY orders.id DESC
        """).fetchall()
    phtml = "".join(
        f"<p>Payment #{p['id']} · {p['username']} · ₹{p['amount']} · "
        f"UTR {p['utr']} · {p['status']} "
        f"<a href='/approve/{p['id']}?key={os.environ['ADMIN_KEY']}'>Approve</a></p>"
        for p in payments
    ) or "<p>No payments.</p>"
    ohtml = "".join(
        f"<p>Order #{o['id']} · {o['username']} · {o['service']} · "
        f"{o['quantity']} · ₹{o['amount']} · {o['status']}</p>"
        for o in orders
    ) or "<p>No orders.</p>"
    return page(f"<div class='card'><h2>Admin Payments</h2>{phtml}</div>"
                f"<div class='card'><h2>Orders</h2>{ohtml}</div>")

@app.route("/approve/<int:pid>")
def approve(pid):
    if not os.environ.get("ADMIN_KEY") or request.args.get("key") != os.environ["ADMIN_KEY"]:
        return "Forbidden", 403
    with connect() as db:
        p = db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
        if not p:
            return "Payment not found", 404
        if p["status"] == "Pending":
            db.execute("UPDATE payments SET status='Approved' WHERE id=?", (pid,))
            db.execute("UPDATE users SET balance=balance+? WHERE id=?",
                       (p["amount"], p["user_id"]))
    return "Approved. Check the dashboard."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
