from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import razorpay  # NEW: Razorpay client

app = Flask(__name__)

# ----------------------------
# CONFIG
# ----------------------------
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///adivasi_store.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Gmail SMTP (use app password)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "theadivasistore@gmail.com"
app.config["MAIL_PASSWORD"] = "copn lept eaxr oqql"  # <-- change this

# Admin email constant
ADMIN_EMAIL = "theadivasistore@gmail.com"

# Razorpay (fill with your real keys)
app.config["RAZORPAY_KEY_ID"] = "rzp_live_Rpr7NCGKEWF1zH"
app.config["RAZORPAY_KEY_SECRET"] = "pfVOqcaOxlya6baESuZwxbzs"

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Razorpay client
razorpay_client = razorpay.Client(auth=(
    app.config["RAZORPAY_KEY_ID"],
    app.config["RAZORPAY_KEY_SECRET"]
))

# --------------------------------------------------------------------
# PRODUCT CATALOG (used ONLY for product_detail pages & optional fallback)
# You DO NOT need to touch this to add new products to cart.
# New products can be defined purely in index.html / shop.html and sent
# to /cart/add via query params (name, price, image, etc.).
# --------------------------------------------------------------------
PRODUCT_CATALOG = {
    # --- WOMEN ---
    "gamusa-border-cotton-saree": {
        "id": "gamusa-border-cotton-saree",
        "name": "Gamusa Border Cotton Saree",
        "price": 2490,
        "category": "Handloom Saree",
        "image": "https://images.pexels.com/photos/3738080/pexels-photo-3738080.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/3738082/pexels-photo-3738082.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Red", "Black"],
        "sizes": ["Free Size"],
        "description": "Soft handloom cotton saree with traditional gamusa border, perfect for everyday wear and gatherings."
    },
    "tribal-motif-wool-stole": {
        "id": "tribal-motif-wool-stole",
        "name": "Tribal Motif Wool Stole",
        "price": 1890,
        "category": "Stole",
        "image": "https://images.pexels.com/photos/6311661/pexels-photo-6311661.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/6311656/pexels-photo-6311656.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Rust", "Charcoal"],
        "sizes": ["Free Size"],
        "description": "Warm wool stole with subtle tribal motifs and a soft handfeel."
    },
    "evening-wrap-red-selvedge": {
        "id": "evening-wrap-red-selvedge",
        "name": "Evening Wrap with Red Selvedge",
        "price": 2190,
        "category": "Shawl",
        "image": "https://images.pexels.com/photos/3738081/pexels-photo-3738081.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/3738083/pexels-photo-3738083.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Ivory", "Deep Red"],
        "sizes": ["Free Size"],
        "description": "Lightweight evening shawl with a bold red selvedge detail."
    },
    "festive-mekhela-chador-set": {
        "id": "festive-mekhela-chador-set",
        "name": "Festive Mekhela Chador Set",
        "price": 3290,
        "category": "Set",
        "image": "https://images.pexels.com/photos/7691083/pexels-photo-7691083.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/7691052/pexels-photo-7691052.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Maroon", "Gold"],
        "sizes": ["Free Size"],
        "description": "Handwoven festive mekhela chador set inspired by traditional motifs."
    },

    # --- MEN ---
    "handloom-border-shirt": {
        "id": "handloom-border-shirt",
        "name": "Handloom Cotton Shirt with Border",
        "price": 1790,
        "category": "Shirt",
        "image": "https://images.pexels.com/photos/7691146/pexels-photo-7691146.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/7691043/pexels-photo-7691043.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Indigo", "Off-white"],
        "sizes": ["S", "M", "L", "XL"],
        "description": "Relaxed-fit cotton shirt with subtle handloom border on cuffs and placket."
    },
    "bordered-chest-panel-tee": {
        "id": "bordered-chest-panel-tee",
        "name": "Bordered Chest Panel Tee",
        "price": 990,
        "category": "T-shirt",
        "image": "https://images.pexels.com/photos/7691052/pexels-photo-7691052.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/7691057/pexels-photo-7691057.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Charcoal", "White"],
        "sizes": ["S", "M", "L", "XL"],
        "description": "Everyday tee with a woven chest panel inspired by Adivasi patterns."
    },
    "layered-jacket-tribal-trim": {
        "id": "layered-jacket-tribal-trim",
        "name": "Layered Jacket with Tribal Trim",
        "price": 2490,
        "category": "Jacket",
        "image": "https://images.pexels.com/photos/3738080/pexels-photo-3738080.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/3738081/pexels-photo-3738081.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Earth Brown", "Forest Green"],
        "sizes": ["S", "M", "L"],
        "description": "Layered jacket with subtle woven trims along collar and front."
    },

    # --- KIDS ---
    "mini-handwoven-jacket": {
        "id": "mini-handwoven-jacket",
        "name": "Mini Handwoven Jacket",
        "price": 1590,
        "category": "Kids · Jacket",
        "image": "https://images.pexels.com/photos/3662879/pexels-photo-3662879.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/3662822/pexels-photo-3662822.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Bright Red", "Mustard"],
        "sizes": ["2-3Y", "4-5Y", "6-7Y"],
        "description": "Soft kids’ jacket with bright handwoven panels."
    },
    "kids-festive-kurta-set": {
        "id": "kids-festive-kurta-set",
        "name": "Kids Festive Kurta Set",
        "price": 1290,
        "category": "Kids · Kurta Set",
        "image": "https://images.pexels.com/photos/3661391/pexels-photo-3661391.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/3661392/pexels-photo-3661392.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Marigold", "Green"],
        "sizes": ["2-3Y", "4-5Y", "6-7Y"],
        "description": "Festive kurta set with bright woven yoke and comfy fit."
    },

    # --- ORNAMENTS ---
    "multi-strand-bead-neckpiece": {
        "id": "multi-strand-bead-neckpiece",
        "name": "Multi-strand Bead Neckpiece",
        "price": 1490,
        "category": "Neckpiece",
        "image": "https://images.pexels.com/photos/1158438/pexels-photo-1158438.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/1158434/pexels-photo-1158434.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Classic Red", "Mixed Beads"],
        "sizes": ["Free Size"],
        "description": "Layered bead necklace inspired by traditional Adivasi jewellery."
    },
    "brass-hoop-earrings": {
        "id": "brass-hoop-earrings",
        "name": "Brass Hoop Earrings",
        "price": 790,
        "category": "Earrings",
        "image": "https://images.pexels.com/photos/1158436/pexels-photo-1158436.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/1158435/pexels-photo-1158435.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Antique Brass"],
        "sizes": ["Free Size"],
        "description": "Round brass hoops with a warm, antique finish."
    },

    # --- BAGS ---
    "gamusa-panel-sling-bag": {
        "id": "gamusa-panel-sling-bag",
        "name": "Gamusa Panel Sling Bag",
        "price": 1990,
        "category": "Sling Bag",
        "image": "https://images.pexels.com/photos/8148578/pexels-photo-8148578.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/8148577/pexels-photo-8148577.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Off-white & Red"],
        "sizes": ["One Size"],
        "description": "Everyday sling bag with a gamusa-inspired front panel."
    },
    "handloom-market-tote": {
        "id": "handloom-market-tote",
        "name": "Handloom Market Tote",
        "price": 1590,
        "category": "Tote",
        "image": "https://images.pexels.com/photos/6476584/pexels-photo-6476584.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/6476582/pexels-photo-6476582.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Natural", "Brick Red"],
        "sizes": ["One Size"],
        "description": "Sturdy tote with handloom panel – perfect for haat and city runs."
    },

    # --- ACCESSORIES ---
    "handloom-weave-belt": {
        "id": "handloom-weave-belt",
        "name": "Handloom Weave Belt",
        "price": 690,
        "category": "Belt",
        "image": "https://images.pexels.com/photos/7691083/pexels-photo-7691083.jpeg?auto=compress&cs=tinysrgb&w=800",
        "hover_image": "https://images.pexels.com/photos/7691048/pexels-photo-7691048.jpeg?auto=compress&cs=tinysrgb&w=800",
        "colors": ["Rust", "Black"],
        "sizes": ["S", "M", "L"],
        "description": "Slim belt with a handloom insert to lift any outfit."
    },
}

# ----------------------------
# MODELS
# ----------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150))
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    phone = db.Column(db.String(30))
    nearest_post_office = db.Column(db.String(150))
    pincode = db.Column(db.String(20))
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return str(self.id)

    @property
    def initials(self):
        if self.name:
            parts = self.name.strip().split()
            if len(parts) == 1:
                return parts[0][:2].upper()
            return (parts[0][0] + parts[-1][0]).upper()
        return (self.email[:2] if self.email else "GU").upper()


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    product_name = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_image = db.Column(db.String(500))
    product_size = db.Column(db.String(50))
    product_color = db.Column(db.String(50))  # NEW

    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Placed")  # Placed, Packed, Shipped, Delivered
    tracking_message = db.Column(db.String(255), default="Order received")

    # Razorpay
    razorpay_order_id = db.Column(db.String(100))
    payment_status = db.Column(db.String(50), default="Pending")  # Pending / Paid / Failed

    shipping_name = db.Column(db.String(150))
    shipping_email = db.Column(db.String(150))
    shipping_phone = db.Column(db.String(30))
    shipping_address = db.Column(db.String(255))
    shipping_post_office = db.Column(db.String(150))
    shipping_pincode = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)

    product_name = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_image = db.Column(db.String(500))
    product_size = db.Column(db.String(50))
    product_color = db.Column(db.String(50))  # NEW
    quantity = db.Column(db.Integer, default=1)


# ----------------------------
# LOGIN MANAGER
# ----------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ----------------------------
# CONTEXT PROCESSOR
# ----------------------------
@app.context_processor
def inject_cart_info():
    """
    Inject cart_count and cart_just_added into all templates.
    cart_just_added is a one-time flag used for cart icon animation.
    """
    cart_count = 0
    if current_user.is_authenticated and not getattr(current_user, "is_admin", False):
        cart_count = (
            db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity), 0))
            .filter_by(user_id=current_user.id)
            .scalar()
            or 0
        )

    # one-time flag – removed from session after first read
    cart_just_added = session.pop("cart_just_added", False)

    return dict(
        cart_count=int(cart_count),
        cart_just_added=bool(cart_just_added),
    )


# ----------------------------
# EMAIL HELPERS
# ----------------------------
def send_email(to_email, subject, body):
    """Simple SMTP email using Gmail app password."""
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = app.config["MAIL_USERNAME"]
        msg["To"] = to_email

        with smtplib.SMTP(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]) as server:
            server.starttls()
            server.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            server.send_message(msg)
    except Exception as e:
        print("Email error:", e)


def send_welcome_password_change_email(user: User):
    """Send email after signup telling user they can change password in profile."""
    subject = "Welcome to The Adivasi Store"
    body = f"""
Hi {user.name or user.email},

Your account at The Adivasi Store has been created with this email: {user.email}.

You can log in anytime and go to your Profile section to update your password and details.

Link: (add your deployed site URL here)

Warmly,
The Adivasi Store
"""
    send_email(user.email, subject, body)


def format_order_lines(order: Order):
    lines = []
    for item in order.items:
        line = f"- {item.product_name}"
        if item.product_size:
            line += f" | Size: {item.product_size}"
        if item.product_color:
            line += f" | Colour: {item.product_color}"
        line += f" | Qty: {item.quantity} | Rs. {int(item.product_price * item.quantity)}"
        lines.append(line)
    return "\n".join(lines)


def send_order_confirmation_email(order: Order):
    subject = f"Your order #{order.id} has been placed"
    body = f"""
Hi {order.shipping_name or order.shipping_email},

Thank you for shopping with The Adivasi Store. Your order #{order.id} has been placed.

Order summary:
{format_order_lines(order)}

Total amount: Rs. {int(order.total_amount)}

Shipping to:
{order.shipping_name or ""}
{order.shipping_address or ""}
{order.shipping_post_office or ""} – {order.shipping_pincode or ""}

Current status: {order.status} – {order.tracking_message}

We will share updates as your order is packed, shipped and delivered.

Warmly,
The Adivasi Store
"""
    if order.shipping_email:
        send_email(order.shipping_email, subject, body)


def send_new_order_admin_email(order: Order):
    subject = f"New order #{order.id} placed"
    body = f"""
Hello,

A new order has been placed on The Adivasi Store.

Order ID: {order.id}
Date: {order.created_at.strftime('%d %b %Y')}
Customer: {order.shipping_name or order.shipping_email}
Total: Rs. {int(order.total_amount)}

Items:
{format_order_lines(order)}

Shipping:
Name: {order.shipping_name or ""}
Email: {order.shipping_email or ""}
Phone: {order.shipping_phone or ""}
Address: {order.shipping_address or ""}
Post Office: {order.shipping_post_office or ""}
Pincode: {order.shipping_pincode or ""}

Current status: {order.status} – {order.tracking_message}

Regards,
The Adivasi Store system
"""
    send_email(ADMIN_EMAIL, subject, body)


# ----------------------------
# ADMIN DECORATOR & HELPER
# ----------------------------
def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access only.", "error")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def redirect_admin_if_needed():
    """
    If an admin is logged in, they should only see the admin side.
    Use this at the top of customer-facing routes.
    """
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin_dashboard"))
    return None


# ----------------------------
# BASIC PAGES
# ----------------------------
@app.route("/")
@app.route("/home")
def home():
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp
    return render_template("index.html")


@app.route("/about")
def about():
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp
    return render_template("about.html")


@app.route("/shop")
def shop():
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp
    return render_template("shop.html")


# Universal product detail endpoint (GET shows page, POST adds to cart)
@app.route("/product/<product_id>", methods=["GET", "POST"])
def product_detail(product_id):
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp

    product = PRODUCT_CATALOG.get(product_id)
    if not product:
        abort(404)

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Please log in to add items to your cart.", "info")
            return redirect(url_for("login"))

        if current_user.is_admin:
            return redirect(url_for("admin_dashboard"))

        selected_size = request.form.get("size") or ""
        selected_color = request.form.get("color") or ""

        existing = CartItem.query.filter_by(
            user_id=current_user.id,
            product_name=product["name"],
            product_size=selected_size,
            product_color=selected_color
        ).first()

        if existing:
            existing.quantity += 1
        else:
            item = CartItem(
                user_id=current_user.id,
                product_name=product["name"],
                product_price=product["price"],
                product_image=product["image"],
                product_size=selected_size,
                product_color=selected_color
            )
            db.session.add(item)

        db.session.commit()
        session["cart_just_added"] = True
        flash("Item added to cart.", "success")
        return redirect(url_for("cart"))

    return render_template("product_detail.html", product=product)


# ----------------------------
# AUTH
# ----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("login"))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=(email == ADMIN_EMAIL)
        )
        db.session.add(user)
        db.session.commit()

        send_welcome_password_change_email(user)

        login_user(user)
        flash("Account created. Welcome!", "success")

        if user.is_admin:
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("home"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password", "error")
            return redirect(url_for("login"))

        if user.email == ADMIN_EMAIL and not user.is_admin:
            user.is_admin = True
            db.session.commit()

        login_user(user)
        flash("Logged in successfully.", "success")

        if user.is_admin:
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ----------------------------
# PROFILE (CUSTOMER) + ADMIN PROFILE
# ----------------------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if current_user.is_admin:
        return redirect(url_for("admin_profile"))

    if request.method == "POST":
        current_user.name = request.form.get("name")
        current_user.phone = request.form.get("phone")
        current_user.nearest_post_office = request.form.get("nearest_post_office")
        current_user.pincode = request.form.get("pincode")
        current_user.address_line1 = request.form.get("address_line1")
        current_user.address_line2 = request.form.get("address_line2")

        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        if new_password:
            if new_password == confirm_password:
                current_user.password_hash = generate_password_hash(new_password)
                flash("Password updated.", "success")
            else:
                flash("Passwords do not match. Password not changed.", "error")

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html")


# SINGLE, CLEAN ADMIN PROFILE ROUTE
@app.route("/admin/profile", methods=["GET", "POST"])
@admin_required
def admin_profile():
    admin_user = current_user

    if request.method == "POST":
        admin_user.name = request.form.get("name")
        admin_user.phone = request.form.get("phone")
        admin_user.nearest_post_office = request.form.get("nearest_post_office")
        admin_user.pincode = request.form.get("pincode")
        admin_user.address_line1 = request.form.get("address_line1")
        admin_user.address_line2 = request.form.get("address_line2")

        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password:
            if new_password == confirm_password:
                admin_user.password_hash = generate_password_hash(new_password)
                flash("Admin password updated.", "success")
            else:
                flash("Passwords do not match.", "error")

        db.session.commit()
        flash("Admin profile updated successfully.", "success")
        return redirect(url_for("admin_profile"))

    return render_template("admin_profile.html", admin_user=admin_user)


# ----------------------------
# CART
# ----------------------------
@app.route("/cart")
@login_required
def cart():
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(i.product_price * i.quantity for i in items)
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add", methods=["GET", "POST"])
def add_to_cart():
    """
    Add item to cart.

    Supports:
    - POST form (product_id/name, price, image, size, color)
    - GET query (product_id/name, price, image, size, color)
    - Optional JSON (for future AJAX).

    IMPORTANT:
    - New products can send ALL details directly from index.html / shop.html.
    - PRODUCT_CATALOG is only used as a fallback if some fields are missing.
    """
    # Must be logged in
    if not current_user.is_authenticated:
        flash("Please log in to add items to your cart.", "info")
        return redirect(url_for("login"))

    # Admin should not be shopping; keep them on admin side
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    # ---------- read raw input ----------
    name = price = image = size = color = None
    product_id = None

    if request.method == "POST":
        if request.is_json:
            data = request.get_json() or {}
            product_id = data.get("product_id")
            name = data.get("name")
            price = data.get("price", "0")
            image = data.get("image", "")
            size = data.get("size", "")
            color = data.get("color", "")
        else:
            product_id = request.form.get("product_id")
            name = request.form.get("name")
            price = request.form.get("price", "0")
            image = request.form.get("image", "")
            size = request.form.get("size", "")
            color = request.form.get("color", "")
    else:  # GET
        product_id = (
            request.args.get("product_id")
            or request.args.get("id")
        )
        name = (
            request.args.get("name")
            or request.args.get("product_name")
            or request.args.get("product_id")
        )
        price = request.args.get("price", "0")
        image = request.args.get("image", "")
        size = request.args.get("size", "")
        color = request.args.get("color", "")

    # ---------- fill from PRODUCT_CATALOG if product_id is given ----------
    # This is ONLY a backup. If you pass name/price/image from frontend,
    # you NEVER need to touch the Python catalog.
    if product_id and (not name or not price or not image):
        catalog_item = PRODUCT_CATALOG.get(product_id)
        if catalog_item:
            name = catalog_item["name"]
            price = catalog_item["price"]
            image = catalog_item["image"]

    if not name:
        flash("No product information received.", "error")
        return redirect(request.referrer or url_for("shop"))

    # ---------- clean/parse price ----------
    if isinstance(price, str):
        price_clean = price.replace(",", "").strip()
    else:
        price_clean = price

    try:
        price_val = float(price_clean or 0)
    except Exception:
        price_val = 0.0

    # ---------- save / merge item ----------
    existing = CartItem.query.filter_by(
        user_id=current_user.id,
        product_name=name,
        product_size=size or "",
        product_color=color or ""
    ).first()

    if existing:
        existing.quantity += 1
    else:
        item = CartItem(
            user_id=current_user.id,
            product_name=name,
            product_price=price_val,
            product_image=image or None,
            product_size=size or "",
            product_color=color or ""
        )
        db.session.add(item)

    db.session.commit()

    # flag for animation on next page load
    session["cart_just_added"] = True

    # If AJAX/JSON, return JSON (optional, for future)
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        new_count = (
            db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity), 0))
            .filter_by(user_id=current_user.id)
            .scalar()
            or 0
        )
        return jsonify({"ok": True, "cart_count": int(new_count)})

    flash("Item added to cart.", "success")
    return redirect(request.referrer or url_for("cart"))


@app.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart_item(item_id):
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    qty = request.form.get("quantity", type=int)
    if qty is not None and qty > 0:
        item.quantity = qty
        db.session.commit()
        flash("Cart updated.", "success")
    else:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_cart_item(item_id):
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))


# ----------------------------
# CHECKOUT (COD + RAZORPAY)
# ----------------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("shop"))

    total = sum(i.product_price * i.quantity for i in items)  # ✅ compute once

    if request.method == "POST":
        payment_mode = request.form.get("payment_mode", "cod")

        shipping_name = request.form.get("name") or current_user.name
        shipping_email = request.form.get("email") or current_user.email
        shipping_phone = request.form.get("phone") or current_user.phone
        shipping_address = request.form.get("address")
        shipping_post_office = request.form.get("nearest_post_office")
        shipping_pincode = request.form.get("pincode")

        # ---------------- COD / MANUAL PAYMENT ----------------
        if payment_mode == "cod":
            order = Order(
                user_id=current_user.id,
                total_amount=total,
                status="Placed",
                payment_status="Pending",
                tracking_message="Order placed (Cash/manual). Preparing for dispatch.",
                shipping_name=shipping_name,
                shipping_email=shipping_email,
                shipping_phone=shipping_phone,
                shipping_address=shipping_address,
                shipping_post_office=shipping_post_office,
                shipping_pincode=shipping_pincode,
            )
            db.session.add(order)
            db.session.flush()

            for i in items:
                db.session.add(OrderItem(
                    order_id=order.id,
                    product_name=i.product_name,
                    product_price=i.product_price,
                    product_image=i.product_image,
                    product_size=i.product_size,
                    product_color=i.product_color,
                    quantity=i.quantity,
                ))

            for i in items:
                db.session.delete(i)

            db.session.commit()

            send_order_confirmation_email(order)
            send_new_order_admin_email(order)

            flash("Order placed successfully (Cash/manual).", "success")
            return redirect(url_for("my_orders"))

        # ---------------- ONLINE PAYMENT – RAZORPAY ----------------
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            status="Pending Payment",
            payment_status="Pending",
            tracking_message="Awaiting online payment confirmation.",
            shipping_name=shipping_name,
            shipping_email=shipping_email,
            shipping_phone=shipping_phone,
            shipping_address=shipping_address,
            shipping_post_office=shipping_post_office,
            shipping_pincode=shipping_pincode,
        )
        db.session.add(order)
        db.session.flush()

        for i in items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_name=i.product_name,
                product_price=i.product_price,
                product_image=i.product_image,
                product_size=i.product_size,
                product_color=i.product_color,
                quantity=i.quantity,
            ))

        try:
            rp_order = razorpay_client.order.create({
                "amount": int(total * 100),
                "currency": "INR",
                "payment_capture": 1,
                "notes": {
                    "local_order_id": str(order.id),
                    "customer_email": shipping_email or "",
                },
            })
            order.razorpay_order_id = rp_order["id"]
        except Exception as e:
            print("Razorpay order error:", e)
            db.session.rollback()
            flash("Could not start online payment. Please try again or choose Cash/manual.", "error")
            return redirect(url_for("checkout"))

        db.session.commit()

        return render_template(
            "checkout.html",
            items=items,
            user=current_user,
            total=total,  # ✅ IMPORTANT
            razorpay_order_id=order.razorpay_order_id,
            razorpay_amount_paise=int(total * 100),
            razorpay_key_id=app.config["RAZORPAY_KEY_ID"],
            order_id=order.id,
            shipping_name=shipping_name,
            shipping_email=shipping_email,
            shipping_phone=shipping_phone,
        )

    # ✅ GET
    return render_template("checkout.html", items=items, user=current_user, total=total)


# ----------------------------
# RAZORPAY PAYMENT VERIFY
# ----------------------------
@app.route("/payment/razorpay/verify", methods=["POST"])
@login_required
def razorpay_verify():
    """
    Called from frontend JS after successful Razorpay Checkout.
    Verifies signature, marks order as Paid, clears cart, sends emails.
    """
    data = request.get_json() or {}

    local_order_id = data.get("order_id")
    rp_payment_id = data.get("razorpay_payment_id")
    rp_order_id = data.get("razorpay_order_id")
    rp_signature = data.get("razorpay_signature")

    if not (local_order_id and rp_payment_id and rp_order_id and rp_signature):
        return jsonify({"ok": False, "error": "Missing payment fields"}), 400

    order = Order.query.get_or_404(local_order_id)

    # customer protection
    if order.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"ok": False, "error": "Not allowed"}), 403

    # already paid? just acknowledge
    if order.payment_status == "Paid":
        return jsonify({"ok": True, "already_paid": True})

    # verify signature
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": rp_order_id,
            "razorpay_payment_id": rp_payment_id,
            "razorpay_signature": rp_signature,
        })
    except razorpay.errors.SignatureVerificationError:
        order.payment_status = "Failed"
        order.status = "Payment Failed"
        order.tracking_message = "Payment failed. Please try again."
        db.session.commit()
        return jsonify({"ok": False, "error": "Signature verification failed"}), 400
    except Exception as e:
        print("Razorpay verify error:", e)
        return jsonify({"ok": False, "error": "Verification error"}), 400

    # mark order as paid
    order.payment_status = "Paid"
    order.status = "Placed"
    order.tracking_message = "Payment received. Order confirmed."
    db.session.commit()

    # clear cart now that payment succeeded
    CartItem.query.filter_by(user_id=order.user_id).delete()
    db.session.commit()

    # send emails (only now for online payment)
    send_order_confirmation_email(order)
    send_new_order_admin_email(order)

    return jsonify({"ok": True})


# ----------------------------
# MY ORDERS
# ----------------------------
@app.route("/my-orders")
@login_required
def my_orders():
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("my_orders.html", orders=orders)


# ----------------------------
# ADMIN PANEL
# ----------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    total_revenue = sum(o.total_amount for o in orders)
    live_orders = [o for o in orders if o.status not in ("Delivered", "Cancelled")]
    return render_template(
        "admin_dashboard.html",
        orders=orders,
        total_revenue=total_revenue,
        live_orders=live_orders,
        admin_user=current_user
    )


@app.route("/admin/order/<int:order_id>", methods=["GET", "POST"])
@admin_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    if request.method == "POST":
        status = request.form.get("status")
        tracking_message = request.form.get("tracking_message")

        if status:
            order.status = status
        if tracking_message:
            order.tracking_message = tracking_message

        db.session.commit()
        flash("Order updated.", "success")
        return redirect(url_for("admin_order_detail", order_id=order.id))

    return render_template("admin_order_detail.html", order=order)


# ----------------------------
# FORGOT / RESET PASSWORD
# ----------------------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("If this email is registered, a reset mail will be sent.", "info")
            return redirect(url_for("forgot_password"))

        subject = "Password reset request - The Adivasi Store"
        body = f"""
Hi {user.name or user.email},

We received a request to reset your password at The Adivasi Store.

For now, please log in with your existing password and change it from your Profile section.
(You can implement a secure reset link here later.)

Email: {user.email}

Warmly,
The Adivasi Store
"""
        send_email(user.email, subject, body)
        flash("If this email is registered, a reset mail has been sent.", "info")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
@login_required
def reset_password():
    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("reset_password"))
        current_user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash("Password updated.", "success")

        if current_user.is_admin:
            return redirect(url_for("admin_profile"))
        return redirect(url_for("profile"))

    return render_template("reset_password.html")


# ----------------------------
# INIT
# ----------------------------
def create_tables_and_admin():
    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(email=ADMIN_EMAIL).first()

        if not admin:
            admin = User(
                email=ADMIN_EMAIL,
                name="Store Admin",
                password_hash=generate_password_hash("Admin@123"),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created with email", ADMIN_EMAIL)


create_tables_and_admin()


if __name__ == "__main__":
    app.run(debug=True)
