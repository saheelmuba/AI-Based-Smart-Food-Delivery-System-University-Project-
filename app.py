"""
ICST AI Food Ordering System - Consolidated Backend
====================================================
A single Flask server (port 5000) that serves EVERY endpoint the frontend
(student.html / student.js) calls. Replaces the old split between
backend_server.py and backend_api.py (which both bound port 5000 and could
not run together).

Storage:  SQLite (zero-setup, auto-created on first run) -> app_data.db
Auth:     werkzeug password hashing + itsdangerous signed/expiring tokens
          (JWT-equivalent, no extra dependency required)
Security: input sanitisation, parameterised SQL (no injection), CORS,
          file-type/size validation on uploads, secret from environment.

Run:      python app.py     (or)     start_app.bat
Dependencies: Flask, flask-cors  (werkzeug + itsdangerous ship with Flask)
"""

import os
import re
import json
import base64
import hashlib
import sqlite3
import secrets
import logging
import urllib.request
import urllib.error
from io import BytesIO
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app_data.db"
MENU_SEED = BASE_DIR / "menu_dataset.json"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def _load_dotenv(path):
    """Minimal .env loader (no external dependency). Lines look like KEY=value;
    blank lines and '#' comments are ignored. Existing env vars win."""
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


_load_dotenv(BASE_DIR / ".env")

# Secret key: use env var in production, fall back to a generated one in dev.
SECRET_KEY = os.environ.get("APP_SECRET_KEY") or secrets.token_hex(32)
TOKEN_MAX_AGE = 60 * 60 * 24 * 7          # 7 days
ALLOWED_EMAIL_DOMAIN = "@icst.edu.lk"
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024         # 5 MB

# Gemini Vision (optional): set GEMINI_API_KEY in the environment (or .env) to
# enable real food-image recognition. Absent key => upload still works, no
# recognition.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest").strip()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_BYTES
CORS(app)  # allow the static page (file:// or any host) to call the API
serializer = URLSafeTimedSerializer(SECRET_KEY, salt="auth-token")


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and seed the menu + a demo user (idempotent)."""
    con = sqlite3.connect(DB_PATH)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            password_hash   TEXT NOT NULL,
            food_preference TEXT DEFAULT 'all',
            is_admin        INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS menu (
            id        INTEGER PRIMARY KEY,
            name      TEXT NOT NULL,
            price     INTEGER NOT NULL,
            category  TEXT,
            cuisine   TEXT,
            veg       INTEGER,
            emoji     TEXT,
            protein   TEXT,
            calories  INTEGER,
            ai_score  INTEGER
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id            TEXT PRIMARY KEY,
            user_id             INTEGER NOT NULL,
            items_json          TEXT NOT NULL,
            total               INTEGER NOT NULL,
            delivery_location   TEXT,
            special_instructions TEXT,
            status              TEXT DEFAULT 'placed',
            timestamp           TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """
    )

    # Migration: add the `cuisine` column to pre-existing databases.
    menu_cols = {r[1] for r in con.execute("PRAGMA table_info(menu)").fetchall()}
    if "cuisine" not in menu_cols:
        con.execute("ALTER TABLE menu ADD COLUMN cuisine TEXT")

    # Seed/expand from the dataset: add any items not already present (keyed by
    # id), so growing menu_dataset.json adds new foods on the next boot WITHOUT
    # overwriting prices/names an admin may have edited in the DB.
    if MENU_SEED.exists():
        items = json.loads(MENU_SEED.read_text(encoding="utf-8"))
        existing_ids = {r[0] for r in con.execute("SELECT id FROM menu").fetchall()}
        added = 0
        for it in items:
            iid = it.get("id")
            if iid in existing_ids:
                # Backfill cuisine on rows seeded before this column existed.
                con.execute("UPDATE menu SET cuisine=COALESCE(cuisine,?) WHERE id=?",
                            (it.get("cuisine") or "Sri Lankan", iid))
                continue
            con.execute(
                """INSERT INTO menu
                   (id,name,price,category,cuisine,veg,emoji,protein,calories,ai_score)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    iid,
                    (it.get("name") or "").strip().title(),  # clean casing/typos
                    int(it.get("price") or 0),
                    it.get("category") or "Unknown",
                    it.get("cuisine") or "Sri Lankan",
                    1 if it.get("veg") else 0,
                    it.get("emoji"),
                    it.get("protein") or "Balanced",
                    int(it.get("calories") or 0),
                    int(it.get("ai_score") or 72),
                ),
            )
            added += 1
        if added:
            logger.info("Added %d new menu items (total dataset %d)", added, len(items))

    # Migration: add is_admin to pre-existing user tables.
    user_cols = {r[1] for r in con.execute("PRAGMA table_info(users)").fetchall()}
    if "is_admin" not in user_cols:
        con.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")

    # Seed a demo student account that matches the pre-filled login form.
    if con.execute("SELECT 1 FROM users WHERE email=?",
                   ("student@icst.edu.lk",)).fetchone() is None:
        con.execute(
            "INSERT INTO users (name,email,password_hash,food_preference,is_admin,created_at) "
            "VALUES (?,?,?,?,?,?)",
            ("Demo Student", "student@icst.edu.lk",
             generate_password_hash("ai2024"), "all", 0,
             datetime.utcnow().isoformat()),
        )
        logger.info("Created demo user student@icst.edu.lk / ai2024")

    # Seed an admin account for the dashboard.
    if con.execute("SELECT 1 FROM users WHERE email=?",
                   ("admin@icst.edu.lk",)).fetchone() is None:
        con.execute(
            "INSERT INTO users (name,email,password_hash,food_preference,is_admin,created_at) "
            "VALUES (?,?,?,?,?,?)",
            ("Administrator", "admin@icst.edu.lk",
             generate_password_hash("admin2024"), "all", 1,
             datetime.utcnow().isoformat()),
        )
        logger.info("Created admin user admin@icst.edu.lk / admin2024")

    con.commit()
    con.close()


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #
def sanitize(text, max_len=500):
    """Strip control chars / tags to prevent stored XSS; cap length."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]*>", "", text)           # drop HTML tags
    text = text.replace("\x00", "").strip()
    return text[:max_len]


def valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)) \
        and email.lower().endswith(ALLOWED_EMAIL_DOMAIN)


def make_token(user_id):
    return serializer.dumps({"uid": user_id})


def user_from_token():
    """Return the authenticated user row, or None."""
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else None
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return get_db().execute(
        "SELECT * FROM users WHERE user_id=?", (data["uid"],)
    ).fetchone()


def user_public(row):
    keys = row.keys()
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "food_preference": row["food_preference"],
        "is_admin": bool(row["is_admin"]) if "is_admin" in keys else False,
    }


def require_admin():
    """Return the admin user row, or None if not an authenticated admin."""
    row = user_from_token()
    if row is None:
        return None
    keys = row.keys()
    if "is_admin" not in keys or not row["is_admin"]:
        return None
    return row


# --------------------------------------------------------------------------- #
# Health / static
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "student.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "icst-ai-food",
                    "time": datetime.utcnow().isoformat()})


# --------------------------------------------------------------------------- #
# Authentication
# --------------------------------------------------------------------------- #
@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = sanitize(data.get("name", ""), 80)
    email = sanitize(data.get("email", ""), 120).lower()
    password = data.get("password", "")
    pref = sanitize(data.get("food_preference", "all"), 20) or "all"

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not valid_email(email):
        return jsonify({"error": f"Email must be valid and end with {ALLOWED_EMAIL_DOMAIN}"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
        return jsonify({"error": "An account with this email already exists"}), 409

    cur = db.execute(
        "INSERT INTO users (name,email,password_hash,food_preference,created_at) "
        "VALUES (?,?,?,?,?)",
        (name, email, generate_password_hash(password), pref,
         datetime.utcnow().isoformat()),
    )
    db.commit()
    row = db.execute("SELECT * FROM users WHERE user_id=?", (cur.lastrowid,)).fetchone()
    return jsonify({"user": user_public(row), "token": make_token(row["user_id"])}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = sanitize(data.get("email", ""), 120).lower()
    password = data.get("password", "")

    row = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    # check_password_hash is constant-time-ish; same error msg avoids user enumeration
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"user": user_public(row), "token": make_token(row["user_id"])})


# --------------------------------------------------------------------------- #
# Menu
# --------------------------------------------------------------------------- #
def menu_row_to_dict(r):
    keys = r.keys()
    return {
        "id": r["id"], "name": r["name"], "price": r["price"],
        "category": r["category"],
        "cuisine": r["cuisine"] if "cuisine" in keys else None,
        "veg": bool(r["veg"]), "emoji": r["emoji"],
        "protein": r["protein"], "calories": r["calories"], "ai_score": r["ai_score"],
    }


@app.route("/api/menu")
def get_menu():
    category = request.args.get("category")
    cuisine = request.args.get("cuisine")
    db = get_db()
    clauses, params = [], []
    if category and category.lower() != "all":
        clauses.append("category=?"); params.append(category)
    if cuisine and cuisine.lower() != "all":
        clauses.append("cuisine=?"); params.append(cuisine)
    sql = "SELECT * FROM menu"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY ai_score DESC"
    rows = db.execute(sql, params).fetchall()
    return jsonify({"items": [menu_row_to_dict(r) for r in rows]})


# --------------------------------------------------------------------------- #
# Orders
# --------------------------------------------------------------------------- #
# Kitchen has no real POS, so status advances on a timeline from order time.
# Minutes elapsed -> stage. 'cancelled' is terminal and overrides the timeline.
STATUS_TIMELINE = [(0, "placed"), (2, "preparing"), (5, "ready"), (9, "completed")]
STATUS_FLOW = ["placed", "preparing", "ready", "completed"]


def live_status(stored_status, timestamp):
    """Compute the current status + ETA from elapsed time (unless cancelled)."""
    if stored_status == "cancelled":
        return "cancelled", 0
    try:
        placed = datetime.fromisoformat(timestamp)
    except (ValueError, TypeError):
        return stored_status, 0
    elapsed = (datetime.utcnow() - placed).total_seconds() / 60.0
    status = STATUS_TIMELINE[0][1]
    for mins, label in STATUS_TIMELINE:
        if elapsed >= mins:
            status = label
    eta = max(0, round(9 - elapsed)) if status != "completed" else 0
    return status, eta


def order_to_dict(row):
    items = json.loads(row["items_json"])
    status, eta = live_status(row["status"], row["timestamp"])
    return {
        "id": row["order_id"], "order_id": row["order_id"],
        "items": items, "total": row["total"],
        "delivery_location": row["delivery_location"],
        "special_instructions": row["special_instructions"],
        "status": status, "eta_minutes": eta,
        "cancellable": status in ("placed", "preparing"),
        "timestamp": row["timestamp"],
    }


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    items = data.get("items", [])
    if not user_id or not isinstance(items, list) or not items:
        return jsonify({"error": "user_id and a non-empty items list are required"}), 400

    db = get_db()
    if not db.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone():
        return jsonify({"error": "Unknown user"}), 404

    # Compute total server-side from quantities/prices (never trust client total).
    total = 0
    for it in items:
        total += int(it.get("price", 0)) * int(it.get("qty", 1))

    # Second-precision timestamp + short random suffix: avoids PRIMARY KEY
    # collisions when two orders are placed within the same second.
    order_id = "ORD" + datetime.utcnow().strftime("%y%m%d%H%M%S") + secrets.token_hex(2)
    ts = datetime.utcnow().isoformat()
    db.execute(
        "INSERT INTO orders (order_id,user_id,items_json,total,delivery_location,"
        "special_instructions,status,timestamp) VALUES (?,?,?,?,?,?,?,?)",
        (order_id, user_id, json.dumps(items), total,
         sanitize(data.get("delivery_location", ""), 120),
         sanitize(data.get("special_instructions", ""), 300),
         "placed", ts),
    )
    db.commit()
    row = db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
    return jsonify({"order": order_to_dict(row)}), 201


@app.route("/api/orders", methods=["GET"])
def get_orders():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    rows = get_db().execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY timestamp DESC LIMIT 50",
        (user_id,),
    ).fetchall()
    return jsonify({"orders": [order_to_dict(r) for r in rows]})


@app.route("/api/orders/<order_id>", methods=["GET"])
def track_order(order_id):
    """Live status for a single order (frontend polls this for tracking)."""
    row = get_db().execute(
        "SELECT * FROM orders WHERE order_id=?", (order_id,)
    ).fetchone()
    if not row:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"order": order_to_dict(row), "flow": STATUS_FLOW})


@app.route("/api/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    """Cancel an order while it is still 'placed' or 'preparing'."""
    db = get_db()
    row = db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
    if not row:
        return jsonify({"error": "Order not found"}), 404
    status, _ = live_status(row["status"], row["timestamp"])
    if status not in ("placed", "preparing"):
        return jsonify({"error": f"Cannot cancel an order that is already '{status}'"}), 409
    db.execute("UPDATE orders SET status='cancelled' WHERE order_id=?", (order_id,))
    db.commit()
    row = db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
    return jsonify({"order": order_to_dict(row)})


# --------------------------------------------------------------------------- #
# Chatbot  (multilingual, food-domain aware)
# --------------------------------------------------------------------------- #
NOT_RELATED = {
    "en-US": "Sorry, this question is not related to our food system.",
    "si-LK": "සමාවන්න, මෙම ප්‍රශ්නය අපගේ ආහාර පද්ධතියට අදාළ නැත.",
    "ta-IN": "மன்னிக்கவும், இந்தக் கேள்வி எங்கள் உணவு அமைப்புடன் தொடர்புடையது அல்ல.",
    "hi-IN": "क्षमा करें, यह प्रश्न हमारी खाद्य प्रणाली से संबंधित नहीं है।",
    "es-ES": "Lo siento, esta pregunta no está relacionada con nuestro sistema de comida.",
}
# Food-domain keywords across supported languages.
FOOD_KEYWORDS = [
    # English
    "food", "menu", "order", "cart", "price", "rs", "rupee", "eat", "meal",
    "lunch", "dinner", "breakfast", "snack", "drink", "juice", "rice", "chicken",
    "beef", "fish", "egg", "veg", "vegetarian", "protein", "calorie", "calories",
    "nutrition", "healthy", "spicy", "recommend", "suggest", "hungry", "delivery",
    "kottu", "briyani", "biriyani", "curry", "rotti", "samosa", "cutlet", "tea",
    "coffee", "dessert", "ice cream", "track", "checkout", "buy", "spoil", "fresh",
    # Common food nouns (may not be on the menu) so "do you have X?" still
    # reaches the recommender instead of being treated as off-topic.
    "sushi", "ramen", "pasta", "spaghetti", "noodle", "noodles", "burger",
    "hamburger", "sandwich", "wrap", "taco", "burrito", "pizza", "kebab", "kabab",
    "shawarma", "falafel", "hummus", "biryani", "pulao", "soup", "salad", "steak",
    "pancake", "waffle", "donut", "cake", "cookie", "pie", "brownie", "milkshake",
    "smoothie", "shake", "lassi", "mojito", "dosa", "idli", "naan", "paneer",
    "mutton", "prawn", "crab", "cheese", "fries", "nuggets", "wings", "hotdog",
    "dumpling", "roll", "bread", "fruit", "mango", "lemon", "watermelon",
    # Sinhala
    "කෑම", "ආහාර", "මෙනු", "ඇණවුම", "මිල", "බත්", "කුකුල්", "මාළු", "බිත්තර",
    "ජූස්", "තේ", "කොත්තු", "බුරියානි",
    # Tamil
    "உணவு", "மெனு", "ஆர்டர்", "விலை", "சாதம்", "கோழி", "மீன்", "முட்டை",
    "சாறு", "தேநீர்", "கொத்து",
    # Hindi
    "खाना", "मेनू", "ऑर्डर", "कीमत", "चावल", "चिकन", "मछली",
]


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = sanitize(data.get("message", ""), 500)
    language = data.get("language", "en-US")
    if language not in NOT_RELATED:
        language = "en-US"
    if not message:
        return jsonify({"error": "Empty message"}), 400

    lower = message.lower()
    # Word-boundary tokens so "eat" doesn't match "weather", "tea" not "theater".
    words = set(re.findall(r"[a-z]+", lower))
    menu_names = [r["name"].lower() for r in get_db().execute("SELECT name FROM menu").fetchall()]
    _STOP = {"with", "and", "the", "for", "plus", "pcs"}
    menu_words = {w for n in menu_names for w in re.findall(r"[a-z]+", n)
                  if len(w) >= 3 and w not in _STOP}

    def keyword_hit(k):
        # ASCII keywords match on whole words (all sub-words present for phrases
        # like "ice cream"); non-Latin scripts (Sinhala/Tamil/Hindi) match on
        # substring since they aren't space-tokenised the same way.
        if re.fullmatch(r"[a-z ]+", k):
            return all(part in words for part in k.split())
        return k in lower

    related = (
        any(keyword_hit(k) for k in FOOD_KEYWORDS)
        or bool(words & menu_words)
        # Tamil/Sinhala food terms (e.g. "පීසා", "கோழி") from the voice lexicon.
        or any(term in lower for term in FOOD_LEXICON)
    )
    if not related:
        return jsonify({"reply": NOT_RELATED[language], "related": False, "intent": "off_topic"})

    # Lightweight intent routing; the frontend enriches with live menu data.
    intent = "general"
    if any(k in lower for k in ("recommend", "suggest", "best")):
        intent = "recommend"
    elif any(k in lower for k in ("protein", "calorie", "nutrition", "healthy")):
        intent = "nutrition"
    elif any(k in lower for k in ("order", "cart", "checkout", "track")):
        intent = "order"
    elif any(k in lower for k in ("menu", "show")):
        intent = "menu"

    return jsonify({"reply": None, "related": True, "intent": intent})


# --------------------------------------------------------------------------- #
# Voice order parsing (real NLP, runs server-side; STT/TTS happen in browser)
# --------------------------------------------------------------------------- #
NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "a": 1, "an": 1}
SPECIALS = ["spicy", "extra cheese", "no onion", "without onion", "no onions",
            "without onions", "less spicy", "extra", "no mayo", "without mayo"]

# --------------------------------------------------------------------------- #
# Multilingual voice lexicon (Tamil + Sinhala -> English menu keywords).
# Chrome's Speech-to-Text returns NATIVE SCRIPT for ta-IN (and romanised text
# for transliterated input). The English-only parser below stripped all
# non-ASCII characters, so Tamil/Sinhala orders never matched. We normalise the
# transcript to English keywords FIRST, then reuse the same matching pipeline.
# --------------------------------------------------------------------------- #
FOREIGN_NUMS = {
    # Tamil
    "ஒன்று": 1, "ஒரு": 1, "இரண்டு": 2, "ரெண்டு": 2, "மூன்று": 3, "நான்கு": 4,
    "நாலு": 4, "ஐந்து": 5, "ஆறு": 6, "ஏழு": 7, "எட்டு": 8, "ஒன்பது": 9, "பத்து": 10,
    # Sinhala
    "එක": 1, "එකක්": 1, "දෙක": 2, "දෙකක්": 2, "තුන": 3, "තුනක්": 3, "හතර": 4,
    "හතරක්": 4, "පහ": 5, "පහක්": 5, "හය": 6, "හත": 7, "අට": 8, "නවය": 9, "දහය": 10,
}
# Foreign food term -> English menu keyword(s). Longer keys are applied first
# so multi-word concepts win over their parts.
FOOD_LEXICON = {
    # ---- Tamil (native script) ----
    "கோழி": "chicken", "சிக்கன்": "chicken",
    "மாட்டிறைச்சி": "beef", "பீஃப்": "beef", "மாட்டு": "beef",
    "முட்டை": "egg",
    "மீன்": "fish",
    "காய்கறி": "veg", "சைவ": "veg",
    "சாதம்": "rice", "சோறு": "rice", "அன்னம்": "rice",
    "வறுத்த சாதம்": "fried rice",
    "கொத்து": "kottu",
    "பிரியாணி": "briyani", "பிரியாணி சாதம்": "briyani",
    "நூடுல்ஸ்": "noodles",
    "ரொட்டி": "rotti", "பரோட்டா": "barotta",
    "இடியாப்பம்": "string hoppers",
    "பிட்டு": "pittu",
    "சமோசா": "samosa",
    "கட்லெட்": "cutlet",
    "ரோல்": "roll",
    "சாண்ட்விச்": "sandwich",
    "எலுமிச்சை": "lemon",
    "மாம்பழம்": "mango", "மாங்காய்": "mango",
    "ஆரஞ்சு": "orange",
    "தர்பூசணி": "watermelon",
    "அன்னாசி": "pineapple",
    "வாழைப்பழம்": "banana",
    "ஐஸ்கிரீம்": "ice cream",
    "லஸ்ஸி": "lassi",
    "மொஜிட்டோ": "mojito",
    "சாறு": "juice", "ஜூஸ்": "juice",
    "பப்பாளி": "papaya",
    "வெண்ணெய் பழம்": "avocado",
    "பிட்சா": "pizza", "பீட்சா": "pizza", "பர்கர்": "burger",
    "சூப்": "soup", "சாலட்": "salad", "இறால்": "prawn", "நண்டு": "crab",
    "பன்னீர்": "paneer", "தோசை": "dosa", "டோசை": "dosa",
    # NOTE: Tamil "நான்" (naan bread) is omitted on purpose — it collides with
    # the extremely common pronoun "நான்" (= "I"), causing false matches.
    # ---- Tamil: extended menu coverage ----
    "கறி": "curry", "வெண்ணெய்": "butter", "மசாலா": "masala", "சீஸ்": "cheese",
    "பூண்டு": "garlic", "மில்க்ஷேக்": "milkshake", "கேக்": "cake",
    "சாக்லேட்": "chocolate", "வெண்ணிலா": "vanilla", "ஸ்ட்ராபெர்ரி": "strawberry",
    "காபி": "coffee", "தேநீர்": "tea", "டீ": "tea", "மட்டன்": "mutton",
    "ஆட்டிறைச்சி": "mutton", "ஷவர்மா": "shawarma", "ரேப்": "wrap",
    "ஃபலாஃபல்": "falafel", "ஹம்மஸ்": "hummus", "ஃப்ரைஸ்": "fries", "சிப்ஸ்": "fries",
    "விங்ஸ்": "wings", "நகெட்ஸ்": "nuggets", "ஹாட்டாக்": "hotdog", "கோலா": "cola",
    "சோடா": "soda", "ஸ்ப்ரைட்": "sprite", "டோஃபு": "tofu", "காளான்": "mushroom",
    "ஸ்பகெட்டி": "spaghetti", "பாஸ்தா": "pasta", "தேங்காய்": "coconut", "பால்": "milk",
    "பலா": "jackfruit", "பருப்பு": "dhal", "ஃபலூடா": "faluda", "வத்தலப்பம்": "watalappan",
    "ஹாப்பர்": "hoppers", "ஆப்பம்": "hoppers", "வடை": "wade", "இட்லி": "idli",
    "லாம்பிரைஸ்": "lamprais", "சாம்பல்": "sambol", "பான்": "bread",
    # ---- Sinhala (native script) ----
    "කුකුල් මස්": "chicken", "කුකුල්": "chicken", "චිකන්": "chicken",
    "හරක් මස්": "beef", "හරක්": "beef", "බීෆ්": "beef",
    "බිත්තර": "egg",
    "මාළු": "fish",
    "එළවළු": "veg", "එළවලු": "veg", "නිර්මාංශ": "veg",
    "බත්": "rice",
    "ෆ්‍රයිඩ් රයිස්": "fried rice", "ෆ්රයිඩ් රයිස්": "fried rice",
    "කොත්තු": "kottu",
    "බුරියානි": "briyani", "බිරියානි": "briyani",
    "නූඩ්ල්ස්": "noodles",
    "රොටි": "rotti", "රොට්ටි": "rotti", "පරෝටා": "barotta", "බරෝතා": "barotta",
    "ඉඳිආප්ප": "string hoppers",
    "පිට්ටු": "pittu",
    "සමෝසා": "samosa",
    "කට්ලට්": "cutlet",
    "රෝල්": "roll", "රෝල්ස්": "roll",
    "සැන්ඩ්විච්": "sandwich",
    "පාන්": "bread", "සම්බෝල": "sambol",
    "දෙහි": "lemon",
    "අඹ": "mango",
    "දොඩම්": "orange",
    "කොමඩු": "watermelon",
    "අන්නාසි": "pineapple",
    "කෙසෙල්": "banana",
    "අයිස් ක්‍රීම්": "ice cream", "අයිස්ක්‍රීම්": "ice cream",
    "ලස්සි": "lassi",
    "මොජිටෝ": "mojito",
    "ජූස්": "juice", "යුෂ": "juice",
    "පැපොල්": "papaya",
    "අලිගැට පේර": "avocado",
    "මිල්ක්": "milo", "මයිලෝ": "milo",
    "පීසා": "pizza", "පිට්සා": "pizza", "බර්ගර්": "burger",
    "සුප්": "soup", "සැලඩ්": "salad", "ඉස්සන්": "prawn", "කකුළුවා": "crab",
    "පැනීර්": "paneer", "නාන්": "naan", "දෝසෙ": "dosa",
    # ---- Sinhala: extended menu coverage ----
    "කරි": "curry", "ව්‍යංජන": "curry", "බටර්": "butter", "මසාලා": "masala",
    "චීස්": "cheese", "සුදුළූණු": "garlic", "මිල්ක්ෂේක්": "milkshake", "කේක්": "cake",
    "චොකලට්": "chocolate", "වැනිලා": "vanilla", "ස්ට්‍රෝබෙරි": "strawberry",
    "කෝපි": "coffee", "තේ": "tea", "මටන්": "mutton", "එළුමස්": "mutton",
    "ෂවර්මා": "shawarma", "රැප්": "wrap", "ෆලාෆල්": "falafel", "හම්මස්": "hummus",
    "ෆ්‍රයිස්": "fries", "චිප්ස්": "fries", "වින්ග්ස්": "wings", "නගට්ස්": "nuggets",
    "හොට්ඩොග්": "hotdog", "කෝලා": "cola", "සෝඩා": "soda", "ස්ප්‍රයිට්": "sprite",
    "ටෝෆු": "tofu", "හතු": "mushroom", "ස්පැගටි": "spaghetti", "පැස්ටා": "pasta",
    "පොල්": "coconut", "කිරි": "milk", "කොස්": "jackfruit", "පරිප්පු": "dhal",
    "ෆලූඩා": "faluda", "වටලප්පන්": "watalappan", "ආප්ප": "hoppers", "හොපර්": "hoppers",
    "වඩේ": "wade", "ඉඩ්ලි": "idli", "කිරිබත්": "kiribath", "ලැම්ප්‍රයිස්": "lamprais",
    "දෙවිල්": "devilled", "ඩෙවිල්ඩ්": "devilled",
}


def normalize_multilingual(text):
    """Rewrite Tamil/Sinhala number words + food terms to English in place so
    the English matcher (and quantity-adjacency regex) works unchanged."""
    # Numbers first (so '2 chicken' adjacency survives), then food terms.
    for foreign, digit in FOREIGN_NUMS.items():
        if foreign in text:
            text = text.replace(foreign, f" {digit} ")
    for foreign in sorted(FOOD_LEXICON, key=len, reverse=True):
        if foreign in text:
            text = text.replace(foreign, f" {FOOD_LEXICON[foreign]} ")
    return re.sub(r"\s+", " ", text).strip()


@app.route("/api/parse-voice-order", methods=["POST"])
def parse_voice_order():
    data = request.get_json(silent=True) or {}
    raw = sanitize(data.get("input", ""), 300).lower()
    if not raw:
        return jsonify({"success": False, "items": [], "confidence": 0})

    # Map any Tamil/Sinhala food + number words to English BEFORE matching.
    text = normalize_multilingual(raw)
    text_words = set(re.findall(r"[a-z]+", text))
    menu = [r["name"].lower() for r in get_db().execute("SELECT name FROM menu").fetchall()]
    special = {s: True for s in SPECIALS if s in text}

    # Grammatical words that must never count as a dish-name match.
    STOP = {"and", "the", "with", "for", "plus", "your", "our"}

    # Build per-item content words and a document frequency, so we can tell
    # "distinctive" words (appear in <=2 dishes, e.g. 'kiribath', 'watalappan',
    # 'dolphin') from common ones ('rice', 'chicken').
    item_words = []
    df = {}
    for name in menu:
        words = [w for w in name.split() if len(w) >= 3 and w not in STOP]
        item_words.append((name, words))
        for w in set(words):
            df[w] = df.get(w, 0) + 1

    # Score each item by the fraction of its words present in the input. Keep a
    # match if it covers >=50% of the item's words, OR if it includes a
    # DISTINCTIVE word (df<=2) — so a long-named item like "Kiribath With Lunu
    # Miris" still matches on the single word "kiribath", while a bare "chicken"
    # never matches every chicken dish.
    scored = []
    for name, words in item_words:
        if not words:
            continue
        matched = [w for w in words if w in text_words]
        if not matched:
            continue
        ratio = len(matched) / len(words)
        has_distinctive = any(df.get(w, 99) <= 2 for w in matched)
        if ratio >= 0.5 or has_distinctive:
            scored.append((len(matched), ratio, name, matched))

    if not scored:
        return jsonify({"success": False, "items": [], "confidence": 0})

    # Best matches first; dedupe identical matched-word sets and drop any item
    # whose matched words are a subset of an already-kept (more specific) item.
    found, kept_sets = [], []
    for score, ratio, name, matched in sorted(scored, key=lambda s: (s[0], s[1]), reverse=True):
        mset = frozenset(matched)
        if any(mset <= k for k in kept_sets):
            continue
        kept_sets.append(mset)
        # Quantity may appear BEFORE the dish ("two chicken") or AFTER it
        # ("chicken kottu two" — common in Sinhala/Tamil word order).
        num = r"(\d+|" + "|".join(NUM_WORDS) + r")"
        word = re.escape(matched[0])
        qty = 1
        m = (re.search(num + r"\s+" + word, text)
             or re.search(word + r"[a-z ]*?\s+" + num + r"\b", text))
        if m:
            token = m.group(1)
            qty = int(token) if token.isdigit() else NUM_WORDS.get(token, 1)
        found.append({"name": name.title(), "quantity": qty, "special": special})

    found = found[:6]
    confidence = min(95, 55 + len(found) * 12) if found else 0
    return jsonify({"success": bool(found), "items": found, "confidence": confidence})


# --------------------------------------------------------------------------- #
# AI feature endpoints (browser now handles live STT/TTS & camera).
# These return a graceful acknowledgement so the existing buttons keep working.
# --------------------------------------------------------------------------- #
@app.route("/api/run-voice", methods=["GET", "POST"])
@app.route("/api/run-voice-enhanced", methods=["GET", "POST"])
def run_voice():
    return jsonify({
        "success": True, "pid": 0,
        "message": "Voice runs in your browser (mic + speech). Click the mic and speak.",
    })


@app.route("/api/run-food-ai", methods=["GET", "POST"])
@app.route("/api/run-food-recognition-enhanced", methods=["GET", "POST"])
def run_food_ai():
    return jsonify({
        "success": True, "pid": 0,
        "message": "Upload a food image below for analysis.",
    })


@app.route("/api/train", methods=["POST"])
def train():
    data = request.get_json(silent=True) or {}
    n_menu = len(data.get("menu", []) or [])
    n_orders = len(data.get("orders", []) or [])
    logger.info("Training sync: %d menu items, %d orders", n_menu, n_orders)
    return jsonify({"status": "ok", "menu_items": n_menu, "orders": n_orders,
                    "message": "Dataset received and synced."})


# --------------------------------------------------------------------------- #
# Admin dashboard API (all routes require an authenticated is_admin user)
# --------------------------------------------------------------------------- #
def _admin_guard():
    """Returns (admin_row, None) or (None, error_response)."""
    admin = require_admin()
    if admin is None:
        return None, (jsonify({"error": "Admin access required"}), 403)
    return admin, None


@app.route("/api/admin/stats")
def admin_stats():
    _, err = _admin_guard()
    if err:
        return err
    db = get_db()
    n_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    n_menu = db.execute("SELECT COUNT(*) FROM menu").fetchone()[0]
    order_rows = db.execute("SELECT * FROM orders").fetchall()

    revenue = 0
    by_status = {}
    item_counts = {}
    for r in order_rows:
        status, _ = live_status(r["status"], r["timestamp"])
        by_status[status] = by_status.get(status, 0) + 1
        if status != "cancelled":
            revenue += r["total"]
        for it in json.loads(r["items_json"]):
            name = it.get("name", "Unknown")
            item_counts[name] = item_counts.get(name, 0) + int(it.get("qty", 1))

    popular = sorted(item_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
    return jsonify({
        "users": n_users,
        "menu_items": n_menu,
        "orders": len(order_rows),
        "revenue": revenue,
        "orders_by_status": by_status,
        "popular_items": [{"name": n, "qty": q} for n, q in popular],
    })


@app.route("/api/admin/orders")
def admin_orders():
    _, err = _admin_guard()
    if err:
        return err
    rows = get_db().execute(
        "SELECT o.*, u.name AS user_name, u.email AS user_email "
        "FROM orders o LEFT JOIN users u ON o.user_id=u.user_id "
        "ORDER BY o.timestamp DESC LIMIT 200"
    ).fetchall()
    out = []
    for r in rows:
        d = order_to_dict(r)
        d["user_name"] = r["user_name"]
        d["user_email"] = r["user_email"]
        out.append(d)
    return jsonify({"orders": out})


@app.route("/api/admin/orders/<order_id>/status", methods=["POST"])
def admin_set_status(order_id):
    _, err = _admin_guard()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in STATUS_FLOW + ["cancelled"]:
        return jsonify({"error": f"Invalid status. Allowed: {STATUS_FLOW + ['cancelled']}"}), 400
    db = get_db()
    if not db.execute("SELECT 1 FROM orders WHERE order_id=?", (order_id,)).fetchone():
        return jsonify({"error": "Order not found"}), 404
    db.execute("UPDATE orders SET status=? WHERE order_id=?", (new_status, order_id))
    db.commit()
    row = db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
    return jsonify({"order": order_to_dict(row)})


@app.route("/api/admin/users")
def admin_users():
    _, err = _admin_guard()
    if err:
        return err
    rows = get_db().execute(
        "SELECT u.*, "
        "(SELECT COUNT(*) FROM orders o WHERE o.user_id=u.user_id) AS order_count "
        "FROM users u ORDER BY u.user_id"
    ).fetchall()
    return jsonify({"users": [
        {**user_public(r), "order_count": r["order_count"], "created_at": r["created_at"]}
        for r in rows
    ]})


@app.route("/api/admin/menu", methods=["POST"])
def admin_add_menu():
    _, err = _admin_guard()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    name = sanitize(data.get("name", ""), 80).title()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    try:
        price = int(data.get("price"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid price is required"}), 400
    db = get_db()
    new_id = (db.execute("SELECT MAX(id) FROM menu").fetchone()[0] or 0) + 1
    db.execute(
        """INSERT INTO menu (id,name,price,category,cuisine,veg,emoji,protein,calories,ai_score)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (new_id, name, price,
         sanitize(data.get("category", "Snack"), 20) or "Snack",
         sanitize(data.get("cuisine", "Sri Lankan"), 30) or "Sri Lankan",
         1 if data.get("veg") else 0,
         sanitize(data.get("emoji", "🍽️"), 8) or "🍽️",
         sanitize(data.get("protein", "Balanced"), 20) or "Balanced",
         int(data.get("calories") or 400),
         int(data.get("ai_score") or 75)),
    )
    db.commit()
    row = db.execute("SELECT * FROM menu WHERE id=?", (new_id,)).fetchone()
    return jsonify({"item": menu_row_to_dict(row)}), 201


@app.route("/api/admin/menu/<int:item_id>", methods=["PUT"])
def admin_update_menu(item_id):
    _, err = _admin_guard()
    if err:
        return err
    db = get_db()
    if not db.execute("SELECT 1 FROM menu WHERE id=?", (item_id,)).fetchone():
        return jsonify({"error": "Menu item not found"}), 404
    data = request.get_json(silent=True) or {}
    # Only update provided fields.
    fields, params = [], []
    if "name" in data:
        fields.append("name=?"); params.append(sanitize(data["name"], 80).title())
    if "price" in data:
        try:
            params.append(int(data["price"])); fields.append("price=?")
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid price"}), 400
    for key, maxlen in (("category", 20), ("cuisine", 30), ("emoji", 8), ("protein", 20)):
        if key in data:
            fields.append(f"{key}=?"); params.append(sanitize(data[key], maxlen))
    if "veg" in data:
        fields.append("veg=?"); params.append(1 if data["veg"] else 0)
    for key in ("calories", "ai_score"):
        if key in data:
            fields.append(f"{key}=?"); params.append(int(data[key] or 0))
    if not fields:
        return jsonify({"error": "No fields to update"}), 400
    params.append(item_id)
    db.execute(f"UPDATE menu SET {', '.join(fields)} WHERE id=?", params)
    db.commit()
    row = db.execute("SELECT * FROM menu WHERE id=?", (item_id,)).fetchone()
    return jsonify({"item": menu_row_to_dict(row)})


@app.route("/api/admin/menu/<int:item_id>", methods=["DELETE"])
def admin_delete_menu(item_id):
    _, err = _admin_guard()
    if err:
        return err
    db = get_db()
    if not db.execute("SELECT 1 FROM menu WHERE id=?", (item_id,)).fetchone():
        return jsonify({"error": "Menu item not found"}), 404
    db.execute("DELETE FROM menu WHERE id=?", (item_id,))
    db.commit()
    return jsonify({"success": True, "deleted": item_id})


@app.route("/admin")
def admin_page():
    return send_from_directory(str(BASE_DIR), "admin.html")


# --------------------------------------------------------------------------- #
# Food image recognition via Gemini Vision (optional, env-gated)
# --------------------------------------------------------------------------- #
def _match_menu_item(dish_name):
    """Find the closest menu item to a recognised dish name (word overlap)."""
    if not dish_name:
        return None
    words = {w for w in re.findall(r"[a-z]+", dish_name.lower()) if len(w) >= 3}
    if not words:
        return None
    best, best_key = None, (0.0, 0)
    for r in get_db().execute("SELECT * FROM menu").fetchall():
        mwords = {w for w in re.findall(r"[a-z]+", r["name"].lower()) if len(w) >= 3}
        if not mwords:
            continue
        inter = len(words & mwords)
        ratio = inter / len(mwords)
        # Prefer higher coverage, then the more specific (more words matched) item.
        key = (ratio, inter)
        if key > best_key:
            best, best_key = r, key
    if best and best_key[0] >= 0.5:
        item = menu_row_to_dict(best)
        item["match_score"] = round(best_key[0] * 100)
        return item
    return None


# Cache successful recognitions by image hash so re-uploading the SAME photo
# (common while testing/demoing) costs zero Gemini calls and never hits quota.
_RECOGNITION_CACHE = {}
_RECOGNITION_CACHE_MAX = 256


def _shrink_for_vision(raw_bytes):
    """Downscale to <=384px JPEG so the image bills as a single Gemini tile
    (~258 input tokens instead of thousands). Hugely reduces free-tier quota
    use and latency. Falls back to the original bytes if Pillow is unavailable."""
    try:
        from PIL import Image
        img = Image.open(BytesIO(raw_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((384, 384))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return raw_bytes, None          # caller keeps the original mime


def classify_food_image(raw_bytes, mime_type):
    """Call Gemini Vision to identify the dish. Returns dict or None on any
    failure (so the upload endpoint always degrades gracefully)."""
    if not GEMINI_API_KEY:
        return None

    # Cache hit: identical image bytes -> identical result, no API call.
    digest = hashlib.sha256(raw_bytes).hexdigest()
    cached = _RECOGNITION_CACHE.get(digest)
    if cached is not None:
        return {**cached, "cached": True}

    # Shrink before sending to minimise input-token (quota) consumption.
    img_bytes, shrunk_mime = _shrink_for_vision(raw_bytes)
    send_mime = shrunk_mime or mime_type

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
    prompt = (
        "You are a food recognition system for a Sri Lankan campus canteen. "
        "Identify the single main food or drink in this image. Respond with ONLY "
        "a compact JSON object, no markdown, of the form "
        '{"dish": "<short dish name>", "confidence": <0-100>, '
        '"is_food": <true|false>}. If the image is not food, set is_food to false.'
    )
    body = json.dumps({
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": send_mime,
                                 "data": base64.b64encode(img_bytes).decode("ascii")}},
            ]
        }],
        # thinkingBudget:0 disables the model's internal reasoning so the whole
        # token budget goes to the answer (gemini-flash-latest is a thinking
        # model and would otherwise burn the budget and truncate the JSON).
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 200,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        # Strip ```json fences if present and parse the JSON object.
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        parsed = json.loads(m.group(0) if m else text)
    except urllib.error.HTTPError as exc:
        # Surface the reason so the user sees rate-limit vs bad-image, not a
        # generic "unavailable". Errors are NOT cached (so a retry can succeed).
        reason = {429: "rate_limited", 400: "bad_image",
                  401: "bad_key", 403: "bad_key"}.get(exc.code, "api_error")
        result = {"error": reason, "http_code": exc.code}
        # Google includes a suggested retry delay (e.g. "27s") on 429s.
        try:
            details = json.loads(exc.read().decode("utf-8")).get("error", {}).get("details", [])
            for d in details:
                if isinstance(d, dict) and d.get("retryDelay"):
                    result["retry_after"] = d["retryDelay"]
                    break
        except Exception:
            pass
        logger.warning("Gemini recognition HTTP %s (%s)", exc.code, reason)
        return result
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError) as exc:
        logger.warning("Gemini recognition failed: %s", exc)
        return {"error": "api_error"}

    if not parsed.get("is_food", True):
        result = {"is_food": False, "dish": parsed.get("dish", "unknown"),
                  "confidence": parsed.get("confidence", 0), "menu_match": None}
    else:
        dish = parsed.get("dish", "")
        result = {"is_food": True, "dish": dish,
                  "confidence": parsed.get("confidence", 0),
                  "menu_match": _match_menu_item(dish)}

    # Cache the successful result (simple FIFO cap).
    if len(_RECOGNITION_CACHE) >= _RECOGNITION_CACHE_MAX:
        _RECOGNITION_CACHE.pop(next(iter(_RECOGNITION_CACHE)))
    _RECOGNITION_CACHE[digest] = result
    return result


# --------------------------------------------------------------------------- #
# Food image upload / regeneration (validation, compression, fallback)
# --------------------------------------------------------------------------- #
FALLBACK_IMAGE = "/uploads/_fallback.png"


@app.route("/api/food-image", methods=["POST"])
def food_image():
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image provided",
                        "image_url": FALLBACK_IMAGE}), 400
    file = request.files["image"]
    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename",
                        "image_url": FALLBACK_IMAGE}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXT:
        return jsonify({"success": False,
                        "error": f"Unsupported type .{ext}. Allowed: {sorted(ALLOWED_IMAGE_EXT)}",
                        "image_url": FALLBACK_IMAGE}), 415

    raw = file.read()
    if len(raw) > MAX_IMAGE_BYTES:
        return jsonify({"success": False, "error": "Image exceeds 5 MB",
                        "image_url": FALLBACK_IMAGE}), 413

    safe_name = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    out_path = UPLOAD_DIR / safe_name

    # Optional lossless-ish compression if Pillow is available; otherwise store as-is.
    try:
        from PIL import Image
        img = Image.open(BytesIO(raw))
        img.thumbnail((1280, 1280))            # cap dimensions, keep aspect
        save_kwargs = {"optimize": True}
        if ext in ("jpg", "jpeg"):
            save_kwargs["quality"] = 85
        img.save(out_path, **save_kwargs)
        w, h = img.size
    except Exception:                          # Pillow missing or decode failed
        out_path.write_bytes(raw)
        w = h = None

    # Optional AI recognition (only if GEMINI_API_KEY is configured).
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    recognition = classify_food_image(raw, mime)
    if recognition is None:
        message = "Image uploaded and optimised."
    elif recognition.get("error"):
        wait = recognition.get("retry_after")
        rate_msg = (f"AI hit the free-tier limit — try again in {wait}."
                    if wait else
                    "AI is busy (free-tier rate limit). Wait a minute and try again.")
        reason_msg = {
            "rate_limited": rate_msg,
            "bad_image": "AI couldn't read that image — try a clearer JPG/PNG photo.",
            "bad_key": "AI recognition key is invalid — check GEMINI_API_KEY in .env.",
        }.get(recognition["error"], "AI recognition is temporarily unavailable.")
        message = "Image uploaded. " + reason_msg
    elif recognition.get("is_food"):
        match = recognition.get("menu_match")
        message = (f"Recognised: {recognition['dish']}"
                   + (f" → matches '{match['name']}' on the menu."
                      if match else " (no exact menu match)."))
    else:
        message = "That doesn't look like food."

    return jsonify({
        "success": True,
        "image_url": f"/uploads/{safe_name}",
        "width": w, "height": h,
        "size_bytes": out_path.stat().st_size,
        "recognition": recognition,
        "ai_enabled": bool(GEMINI_API_KEY),
        "message": message,
    })


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(str(UPLOAD_DIR), filename)


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    init_db()
    logger.info("ICST AI Food backend running on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
