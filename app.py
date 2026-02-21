import os
import uuid
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, abort,request
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import razorpay  # Razorpay client
from product_catalogs import (
    ALL_PRODUCTS,
    SHOP_CATALOGS,
    ACCESSORY_CATEGORIES,
    WOMEN_PRODUCTS,
    MEN_PRODUCTS,
    KIDS_PRODUCTS,
    ORNAMENT_PRODUCTS
)


app = Flask(__name__)

# ----------------------------
# CONFIG
# ----------------------------
# ⚠️ SECURITY: put real values in environment variables in production
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///adivasi_store.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Gmail SMTP (use app password)
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "theadivasistore@gmail.com")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "ismd ozfs mnwg wkfk")  # set in env

# Admin email constant
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "theadivasistore@gmail.com")

# Razorpay (⚠️ set real keys via env; do NOT hardcode live keys)
app.config["RAZORPAY_KEY_ID"] = os.environ.get("RAZORPAY_KEY_ID", "rzp_live_Rpr7NCGKEWF1zH")
app.config["RAZORPAY_KEY_SECRET"] = os.environ.get("RAZORPAY_KEY_SECRET", "pfVOqcaOxlya6baESuZwxbzs")

# ----------------------------
# UPLOADS (Product Images)
# ----------------------------
# Store product images at: /static/uploads/products/
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "products")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8MB

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS





def save_product_image(file_storage):
    """
    Save upload to static/uploads/products/
    Return a public URL like: /static/uploads/products/<filename>
    """
    if not file_storage or not getattr(file_storage, "filename", ""):
        return ""

    filename = secure_filename(file_storage.filename)
    if not filename or not allowed_file(filename):
        return ""

    ext = filename.rsplit(".", 1)[1].lower()
    new_name = f"prod_{uuid.uuid4().hex}.{ext}"
    abs_path = os.path.join(app.config["UPLOAD_FOLDER"], new_name)
    file_storage.save(abs_path)

    return f"/static/uploads/products/{new_name}"


db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Razorpay client
razorpay_client = razorpay.Client(auth=(
    app.config["RAZORPAY_KEY_ID"],
    app.config["RAZORPAY_KEY_SECRET"]
))

# --------------------------------------------------------------------
# PRODUCT CATALOG (Legacy static catalog)
# NOTE: We'll gradually move to DB Products for admin-managed inventory.
# --------------------------------------------------------------------


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
    product_color = db.Column(db.String(50))
    product_db_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)

    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    


# ✅ NEW/UPDATED: Product model (Admin-managed products + stock + image upload)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)

    # Optional slug (safe even if you don't use it yet)
    slug = db.Column(db.String(260), unique=True, nullable=True)

    price = db.Column(db.Float, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)

    # Must match your mega-menu labels like "Saree", "Bandi", "Bags", etc.
    category = db.Column(db.String(120), nullable=False, index=True)

    description = db.Column(db.Text, default="")
    sizes = db.Column(db.String(200), default="")   # "S,M,L"
    colors = db.Column(db.String(200), default="")  # "Red,Black"

    image_url = db.Column(db.String(500), default="")  # "/static/uploads/products/xxx.jpg"

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Placed")
    tracking_message = db.Column(db.String(255), default="Order received")

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
    product_db_id = db.Column(db.Integer, nullable=True)

    product_name = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_image = db.Column(db.String(500))
    product_size = db.Column(db.String(50))
    product_color = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=1)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(30), default="New")  # New / Read / Replied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    cart_count = 0
    if current_user.is_authenticated and not getattr(current_user, "is_admin", False):
        cart_count = (
            db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity), 0))
            .filter_by(user_id=current_user.id)
            .scalar()
            or 0
        )

    cart_just_added = session.pop("cart_just_added", False)

    return dict(
        cart_count=int(cart_count),
        cart_just_added=bool(cart_just_added),
    )


# ----------------------------
# EMAIL HELPERS
# ----------------------------
def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = app.config["MAIL_USERNAME"]
        msg["To"] = to_email

        with smtplib.SMTP(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]) as server:
            if app.config["MAIL_USE_TLS"]:
                server.starttls()
            server.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            server.send_message(msg)
    except Exception as e:
        print("Email error:", e)


def send_welcome_password_change_email(user: User):
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
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin_dashboard"))
    return None


def _gen_slug_from_name(name: str) -> str:
    # lightweight slug (no extra deps)
    import re
    s = (name or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or uuid.uuid4().hex


def ensure_product_slug(p: Product):
    if p.slug:
        return
    base = _gen_slug_from_name(p.name)
    candidate = base
    i = 2
    while Product.query.filter(Product.slug == candidate, Product.id != p.id).first():
        candidate = f"{base}-{i}"
        i += 1
    p.slug = candidate


# ----------------------------
# ✅ HELPERS FOR PRODUCT VIEW (DB + CATALOG)
# ----------------------------
def _split_csv(text: str):
    """Convert 'S,M,L' => ['S','M','L'] safely."""
    if not text:
        return []
    return [x.strip() for x in text.split(",") if x.strip()]


def _product_to_template_dict(p: Product) -> dict:
    """
    Convert DB Product -> dict structure that your product_detail.html expects.
    Your template uses:
      product.image, product.hover_image, product.colors (list), product.sizes (list)
    """
    return {
        "id": str(p.slug or p.id),               # use slug in URL when available
        "name": p.name,
        "price": float(p.price or 0),
        "category": p.category,
        "image": p.image_url or "",
        "hover_image": "",                      # you can add a DB column later if needed
        "colors": _split_csv(p.colors),
        "sizes": _split_csv(p.sizes),
        "description": p.description or "",
        "_source": "db",
        "_db_id": p.id,
        "_slug": p.slug,
    }


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


# ----------------------------
# ✅ UPDATED SHOP — SINGLE SOURCE OF TRUTH (PRODUCT_CATALOG)
# ----------------------------
@app.route("/shop")
def shop():
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp

    # ✅ fetch admin-added products from DB (active only)
    db_products = (
        Product.query
        .filter_by(is_active=True)
        .order_by(Product.created_at.desc())
        .all()
    )

    return render_template(
        "shop.html",
        catalogs=SHOP_CATALOGS,
        accessory_categories=ACCESSORY_CATEGORIES,

        # ✅ NEW: send DB products to template
        db_products=db_products,
    )
# ----------------------------
# CONTACT PAGE (GET + POST)
# ----------------------------
@app.route("/contact", methods=["GET", "POST"])
def contact():
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not name or not email or not message:
            flash("Please fill Name, Email, and Message.", "error")
            return redirect(url_for("contact"))

        cm = ContactMessage(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            status="New"
        )
        db.session.add(cm)
        db.session.commit()

        flash("Message sent successfully. We’ll get back to you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


# ----------------------------
# ✅ PRODUCT DETAIL (DB + Legacy catalog) — FIXED WRONG PRODUCT OPENING
# ----------------------------

@app.route("/product/<product_id>", methods=["GET", "POST"])
def product_detail(product_id):
    redirect_resp = redirect_admin_if_needed()
    if redirect_resp:
        return redirect_resp

    product_for_template = None

    # ======================================================
    # 1) Try DB product by slug (priority)
    # ======================================================
    db_product = None
    if product_id:
        db_product = Product.query.filter_by(
            slug=product_id,
            is_active=True
        ).first()

    # ======================================================
    # 2) If numeric, try DB by ID
    # ======================================================
    if not db_product and str(product_id).isdigit():
        db_product = Product.query.filter_by(
            id=int(product_id),
            is_active=True
        ).first()

    # ======================================================
    # 3) Use DB product if found
    # ======================================================
    if db_product:
        product_for_template = _product_to_template_dict(db_product)

    # ======================================================
    # 4) Fallback to NEW product_catalogs.py (ALL_PRODUCTS)
    # ======================================================
    else:
        catalog_item = ALL_PRODUCTS.get(product_id)
        if not catalog_item:
            abort(404)

        # copy so we never mutate catalog
        product_for_template = dict(catalog_item)

        # ----------------------------------------------
        # normalize images for product_detail.html
        # ----------------------------------------------
        images = product_for_template.get("images") or {}

        product_for_template["image"] = images.get("primary", "")
        product_for_template["hover_image"] = images.get("hover", "")

        # ----------------------------------------------
        # normalize category label
        # ----------------------------------------------
        product_for_template["category"] = product_for_template.get(
            "category_label", ""
        )

    # ======================================================
    # 5) POST → Add to cart
    # ======================================================
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Please log in to add items to your cart.", "info")
            return redirect(url_for("login"))

        if current_user.is_admin:
            return redirect(url_for("admin_dashboard"))

        selected_size = request.form.get("size") or ""
        selected_color = request.form.get("color") or ""

        pname = product_for_template.get("name")
        pprice = product_for_template.get("price", 0)
        pimage = product_for_template.get("image", "")
        db_id = product_for_template.get("_db_id")  # will be int for DB products, None for catalog

        existing = CartItem.query.filter_by(
            user_id=current_user.id,
            product_name=pname,
            product_size=selected_size,
            product_color=selected_color,
            product_db_id=db_id
        ).first()

        if existing:
            existing.quantity += 1
        else:
            item = CartItem(
                user_id=current_user.id,
                product_db_id=db_id,
                product_name=pname,
                product_price=float(pprice or 0),
                product_image=pimage,
                product_size=selected_size,
                product_color=selected_color
            )
            db.session.add(item)

        db.session.commit()
        session["cart_just_added"] = True
        flash("Item added to cart.", "success")
        return redirect(url_for("cart"))

    # ======================================================
    # 6) Image override via query string (CRITICAL FEATURE)
    # ======================================================
    override_img = request.args.get("img") or request.args.get("image")
    override_hover = request.args.get("hover") or request.args.get("hover_image")

    if override_img or override_hover:
        product_for_template = dict(product_for_template)
        if override_img:
            product_for_template["image"] = override_img
        if override_hover:
            product_for_template["hover_image"] = override_hover

    # ======================================================
    # 7) Render
    # ======================================================
    return render_template(
        "product_detail.html",
        product=product_for_template
    )


#--------------passing products details from catalog file to index file------#


@app.route("/api/aps-products")
def api_aps_products():
    gender = (request.args.get("gender") or "women").strip().lower()

    catalog_map = {
        "women": WOMEN_PRODUCTS,
        "men": MEN_PRODUCTS,
        "kids": KIDS_PRODUCTS,
        "ornaments": ORNAMENT_PRODUCTS,
    }

    products = catalog_map.get(gender)
    if products is None:
        return jsonify({"ok": False, "items": [], "error": "Invalid gender"}), 400

    items = []
    for p in products:
        images = p.get("images") or {}

        # IMPORTANT: keep field mapping aligned to product_catalogs.py
        items.append({
            # product_catalogs.py fields (source of truth)
            "id": p.get("id"),
            "name": p.get("name", ""),
            "price": p.get("price", 0),
            "badge": p.get("badge", ""),
            "category_label": p.get("category_label", ""),
            "audience": p.get("audience", ""),
            "type": p.get("type", ""),
            "menu_category": p.get("menu_category", ""),

            # images normalized for frontend
            "images": {
                "primary": images.get("primary", ""),
                "hover": images.get("hover", images.get("primary", "")),
            }
        })

    return jsonify({"ok": True, "items": items})


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
    if not current_user.is_authenticated:
        flash("Please log in to add items to your cart.", "info")
        return redirect(url_for("login"))

    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

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
    else:
        product_id = request.args.get("product_id") or request.args.get("id")
        name = request.args.get("name") or request.args.get("product_name") or request.args.get("product_id")
        price = request.args.get("price", "0")
        image = request.args.get("image", "")
        size = request.args.get("size", "")
        color = request.args.get("color", "")

    # Legacy fallback from catalog if missing fields
    if product_id and (not name or not price or not image):
        catalog_item = PRODUCT_CATALOG.get(product_id)
        if catalog_item:
            name = catalog_item["name"]
            price = catalog_item["price"]
            image = catalog_item["image"]

    if not name:
        flash("No product information received.", "error")
        return redirect(request.referrer or url_for("shop"))

    if isinstance(price, str):
        price_clean = price.replace(",", "").strip()
    else:
        price_clean = price

    try:
        price_val = float(price_clean or 0)
    except Exception:
        price_val = 0.0

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
    session["cart_just_added"] = True

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

    total = sum(i.product_price * i.quantity for i in items)

    if request.method == "POST":
        payment_mode = request.form.get("payment_mode", "cod")

        shipping_name = (request.form.get("name") or "").strip() or (current_user.name or "")
        shipping_email = (request.form.get("email") or "").strip() or (current_user.email or "")
        shipping_phone = (request.form.get("phone") or "").strip() or (current_user.phone or "")
        shipping_address = (request.form.get("address") or "").strip() or (
            " ".join(filter(None, [current_user.address_line1, current_user.address_line2])).strip()
        )
        shipping_post_office = (request.form.get("nearest_post_office") or "").strip() or (current_user.nearest_post_office or "")
        shipping_pincode = (request.form.get("pincode") or "").strip() or (current_user.pincode or "")

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
            return redirect(url_for("order_success", order_id=order.id))

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
                    "customer_pincode": shipping_pincode or "",
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
            total=total,
            razorpay_order_id=order.razorpay_order_id,
            razorpay_amount_paise=int(total * 100),
            razorpay_key_id=app.config["RAZORPAY_KEY_ID"],
            order_id=order.id,
            shipping_name=shipping_name,
            shipping_email=shipping_email,
            shipping_phone=shipping_phone,
        )

    return render_template("checkout.html", items=items, user=current_user, total=total)


# ----------------------------
# RAZORPAY PAYMENT VERIFY
# ----------------------------
@app.route("/payment/razorpay/verify", methods=["POST"])
@login_required
def razorpay_verify():
    data = request.get_json() or {}

    local_order_id = data.get("order_id")
    rp_payment_id = data.get("razorpay_payment_id")
    rp_order_id = data.get("razorpay_order_id")
    rp_signature = data.get("razorpay_signature")

    if not (local_order_id and rp_payment_id and rp_order_id and rp_signature):
        return jsonify({"ok": False, "error": "Missing payment fields"}), 400

    order = Order.query.get_or_404(local_order_id)

    if order.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"ok": False, "error": "Not allowed"}), 403

    if order.payment_status == "Paid":
        return jsonify({"ok": True, "already_paid": True, "order_id": order.id})

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

    order.payment_status = "Paid"
    order.status = "Placed"
    order.tracking_message = "Payment received. Order confirmed."
    db.session.commit()

    CartItem.query.filter_by(user_id=order.user_id).delete()
    db.session.commit()

    send_order_confirmation_email(order)
    send_new_order_admin_email(order)

    return jsonify({"ok": True, "order_id": order.id})


# ----------------------------
# ORDER SUCCESS PAGE
# ----------------------------
@app.route("/order-success/<int:order_id>")
@login_required
def order_success(order_id):
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        abort(403)

    if order.status in ("Pending Payment", "Payment Failed"):
        flash("This order is not confirmed yet.", "info")
        return redirect(url_for("checkout"))

    return render_template("order_success.html", order=order)


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

    contact_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    new_contact_count = ContactMessage.query.filter_by(status="New").count()

    # ✅ NEW: Products for admin dashboard tab
    products = Product.query.order_by(Product.created_at.desc()).all()

    return render_template(
        "admin_dashboard.html",
        orders=orders,
        total_revenue=total_revenue,
        live_orders=live_orders,
        admin_user=current_user,
        contact_messages=contact_messages,
        new_contact_count=new_contact_count,

        # NEW
        products=products,
        categories=ACCESSORY_CATEGORIES,
    )


@app.route("/admin/contact/<int:msg_id>/mark-read", methods=["POST"])
@admin_required
def admin_mark_contact_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.status = "Read"
    db.session.commit()
    flash("Message marked as Read.", "success")
    return redirect(url_for("admin_dashboard"))


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
# ADMIN PRODUCTS (CRUD)
# These are the routes your updated admin_dashboard.html will call.
# ----------------------------
@app.route("/admin/products/create", methods=["POST"])
@admin_required
def admin_create_product():
    name = (request.form.get("name") or "").strip()
    category = (request.form.get("category") or "").strip()
    price = request.form.get("price", type=float) or 0
    stock = request.form.get("stock", type=int) or 0
    sizes = (request.form.get("sizes") or "").strip()
    colors = (request.form.get("colors") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not name or not category:
        flash("Name and Category are required.", "error")
        return redirect(url_for("admin_dashboard"))

    if category not in ACCESSORY_CATEGORIES:
        flash("Invalid category selected.", "error")
        return redirect(url_for("admin_dashboard"))

    image_file = request.files.get("image")
    image_url = save_product_image(image_file)
    if not image_url:
        flash("Please upload a valid image (png/jpg/jpeg/webp).", "error")
        return redirect(url_for("admin_dashboard"))

    p = Product(
        name=name,
        category=category,
        price=float(price or 0),
        stock=int(stock or 0),
        sizes=sizes,
        colors=colors,
        description=description,
        image_url=image_url,
        is_active=True,
    )
    db.session.add(p)
    db.session.flush()

    # Optional slug
    ensure_product_slug(p)

    db.session.commit()
    flash("Product added successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/products/<int:product_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_product(product_id):
    p = Product.query.get_or_404(product_id)
    p.is_active = not p.is_active
    db.session.commit()
    flash("Product status updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_delete_product(product_id):
    p = Product.query.get_or_404(product_id)

    # optional: delete file from disk
    try:
        if p.image_url and p.image_url.startswith("/static/uploads/products/"):
            fname = p.image_url.split("/")[-1]
            fpath = os.path.join(app.config["UPLOAD_FOLDER"], fname)
            if os.path.exists(fpath):
                os.remove(fpath)
    except Exception as e:
        print("Image delete error:", e)

    db.session.delete(p)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):
    p = Product.query.get_or_404(product_id)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        category = (request.form.get("category") or "").strip()
        price = request.form.get("price", type=float) or 0
        stock = request.form.get("stock", type=int) or 0
        sizes = (request.form.get("sizes") or "").strip()
        colors = (request.form.get("colors") or "").strip()
        description = (request.form.get("description") or "").strip()

        if not name or not category:
            flash("Name and Category are required.", "error")
            return redirect(url_for("admin_edit_product", product_id=p.id))

        if category not in ACCESSORY_CATEGORIES:
            flash("Invalid category selected.", "error")
            return redirect(url_for("admin_edit_product", product_id=p.id))

        p.name = name
        p.category = category
        p.price = float(price or 0)
        p.stock = int(stock or 0)
        p.sizes = sizes
        p.colors = colors
        p.description = description

        # new image optional
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            new_url = save_product_image(image_file)
            if not new_url:
                flash("Invalid image. Allowed: png/jpg/jpeg/webp", "error")
                return redirect(url_for("admin_edit_product", product_id=p.id))
            p.image_url = new_url

        ensure_product_slug(p)

        db.session.commit()
        flash("Product updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_product_edit.html",
        p=p,
        categories=ACCESSORY_CATEGORIES
    )


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
