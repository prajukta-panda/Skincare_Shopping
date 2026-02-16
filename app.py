import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from openai import OpenAI

import stripe

from models import db, User, Product, Order

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Email
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

# APIs
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- AUTH ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        pw = bcrypt.generate_password_hash(request.form["password"]).decode()
        user = User(
            username=request.form["username"],
            email=request.form["email"],
            password=pw
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("products"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- PRODUCTS ----------------
@app.route("/")
@login_required
def products():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    pagination = query.paginate(page=page, per_page=5)
    return render_template(
        "products.html",
        products=pagination.items,
        pagination=pagination,
        search=search
    )

# ---------------- AI ----------------
@app.route("/ai", methods=["GET", "POST"])
@login_required
def ai():
    suggestions = []
    if request.method == "POST":
        prompt = f"""
        Suggest skincare products for:
        Skin Type: {request.form['skin_type']}
        Concerns: {request.form['concerns']}
        Ingredients: {request.form['ingredients']}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        suggestions = response.choices[0].message.content.split("\n")

    return render_template("ai.html", suggestions=suggestions)

# ---------------- PAYMENT ----------------
@app.route("/buy/<int:product_id>")
@login_required
def buy(product_id):
    product = Product.query.get_or_404(product_id)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": product.name},
                "unit_amount": int(product.price * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=url_for("success", _external=True, product_id=product.id),
        cancel_url=url_for("products", _external=True),
    )

    return redirect(session.url)

@app.route("/success")
@login_required
def success():
    product_id = request.args.get("product_id")
    product = Product.query.get(product_id)

    order = Order(user_id=current_user.id, product_id=product.id, status="Paid")
    db.session.add(order)
    db.session.commit()

    msg = Message(
        "Order Confirmed",
        recipients=[current_user.email],
        body=f"Your order for {product.name} is confirmed."
    )
    mail.send(msg)

    return "Payment successful. Email sent."

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        db.session.add(Product(name="Retinol Night Cream", price=25))
        db.session.add(Product(name="Vitamin C Serum", price=20))
        db.session.add(Product(name="Niacinamide Moisturizer", price=18))
        db.session.add(Product(name="Salicylic Acid Face Wash", price=15))
        db.session.commit()
    app.run(debug=True)