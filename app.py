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

PAGE = '<!doctype html>\n<html lang="en">\n<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="theme-color" content="#091a32">\n<title>ROCKYSMM PANEL</title>\n<style>\n*{box-sizing:border-box}\nbody{margin:0;background:#edf2fb;color:#10223f;font-family:Arial,sans-serif}\nheader{background:linear-gradient(120deg,#071a34,#0759a5);color:white;padding:24px 18px;box-shadow:0 5px 20px #0c234526}\nheader h1{font-size:23px;margin:0 0 7px}\nheader small{color:#c6dcfa}\nmain{max-width:720px;margin:20px auto;padding:0 15px 80px}\n.card{background:white;border:1px solid #dce5f1;border-radius:20px;padding:22px;margin:16px 0;box-shadow:0 5px 18px #11284b0c;overflow-wrap:anywhere}\n.card h2{font-size:22px;margin:0 0 14px;color:#102747}\n.card h3{font-size:27px;margin:10px 0;color:#0759a5}\n.hero{background:linear-gradient(130deg,#08264b,#0863b9);color:white;border:0}\n.hero h2,.hero h3{color:white}\n.eyebrow{font-size:12px;letter-spacing:2px;color:#c7e2ff;font-weight:bold}\ninput,select,button{display:block;width:100%;padding:14px;margin:11px 0;border-radius:11px;border:1px solid #d2deec;font-size:16px}\ninput,select{background:#f8faff;color:#10223f}\nbutton{border:0;background:linear-gradient(100deg,#0875df,#304fe0);color:white;font-weight:bold;cursor:pointer}\na{color:#075eb8;font-weight:600}\nsmall{color:#64748b;line-height:1.6}\n.card p{line-height:1.6}\n@media(min-width:600px){main{padding-top:12px}.card{padding:26px}}\n</style>\n</head>\n<body>\n<header><h1>👑 ROCKY BHAI</h1><small>WELCOME TO ROCKY BHAI</small></header>\n<main>{{ content|safe }}</main>\n</body>\n</html>'

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
    <div class="card hero"><p class="eyebrow">WELCOME BACK</p><h2>Namaste, {user['username']} 👋</h2>
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
