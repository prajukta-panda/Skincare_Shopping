import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from openai import OpenAI
import stripe
from models import db, User, Product, Order
load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Mail
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME"),
)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# ---------------- AUTH API ----------------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    pw = bcrypt.generate_password_hash(data["password"]).decode()
    user = User(
        username=data["username"],
        email=data["email"],
        password=pw
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user and bcrypt.check_password_hash(user.password, data["password"]):
        login_user(user)
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"})

# ---------------- PRODUCTS API ----------------
@app.route("/api/products", methods=["GET"])
def get_products():
    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    pagination = query.paginate(page=page, per_page=5)
    return jsonify({
        "products": [
            {"id": p.id, "name": p.name, "price": p.price}
            for p in pagination.items
        ],
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })

# ---------------- AI API ----------------
@app.route("/api/ai/recommend", methods=["POST"])
def ai_recommend():
    data = request.json
    prompt = f"""
    Suggest skincare products for:
    Skin Type: {data['skin_type']}
    Concerns: {data['concerns']}
    Ingredients: {data['ingredients']}
    """
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )
    return jsonify({
        "suggestions": response.output_text
    })


# ---------------- PAYMENT API ----------------
@app.route("/api/checkout/<int:product_id>", methods=["POST"])
@login_required
def checkout(product_id):
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
        success_url="http://localhost:5000/api/success",
        cancel_url="http://localhost:5000/api/cancel",
    )
    return jsonify({"checkout_url": session.url})

@app.route("/api/success")
@login_required
def success():
    order = Order(user_id=current_user.id, status="Paid")
    db.session.add(order)
    db.session.commit()
    msg = Message(
        "Order Confirmed",
        recipients=[current_user.email],
        body="Your payment was successful."
    )
    mail.send(msg)
    return jsonify({"message": "Payment successful, email sent"})

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)