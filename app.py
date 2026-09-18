import os
from flask import Flask, render_template, jsonify, request
from flask_jwt_extended import JWTManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
try:
    from flask_cors import CORS
except ImportError:  # pragma: no cover
    CORS = None
from config import Config
from database import db, migrate
from security import register_security_headers
from routes.menu import menu_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.auth import auth_bp
from routes.chatbot import chatbot_bp
from routes.image import image_bp
from routes.voice import voice_bp
from routes.patients import patients_bp
from routes.doctors import doctors_bp
from routes.appointments import appointments_bp
from routes.records import records_bp
from routes.ai import ai_bp
from routes.notifications import notifications_bp
from routes.reports import reports_bp
from routes.analytics import analytics_bp
from routes.admin import admin_bp

mail = Mail()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

API_BLUEPRINTS = (
    menu_bp,
    cart_bp,
    orders_bp,
    auth_bp,
    chatbot_bp,
    image_bp,
    voice_bp,
    patients_bp,
    doctors_bp,
    appointments_bp,
    records_bp,
    ai_bp,
    notifications_bp,
    reports_bp,
    analytics_bp,
    admin_bp,
)


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    if CORS is not None:
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    register_security_headers(app)

    app.register_blueprint(menu_bp, url_prefix="/api/menu")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(image_bp, url_prefix="/api/image")
    app.register_blueprint(voice_bp, url_prefix="/api/voice")
    app.register_blueprint(patients_bp, url_prefix="/api/patients")
    app.register_blueprint(doctors_bp, url_prefix="/api/doctors")
    app.register_blueprint(appointments_bp, url_prefix="/api/appointments")
    app.register_blueprint(records_bp, url_prefix="/api/records")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    for blueprint in API_BLUEPRINTS:
        csrf.exempt(blueprint)

    with app.app_context():
        db.create_all()

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/chatbot")
    def chatbot():
        return render_template("chatbot.html")

    @app.route("/analytics")
    def analytics():
        return render_template("analytics.html")

    @app.route("/cart")
    def cart():
        return render_template("cart.html")

    @app.route("/menu")
    def menu():
        return render_template("menu.html")

    @app.route("/orders")
    def orders():
        return render_template("orders.html")

    @app.route("/ICST-System.html")
    def icst_system():
        return render_template("ICST-System.html")

    @app.route("/ICST-Student.html")
    def icst_student():
        return render_template("ICST-Student.html")

    @app.route("/ICST-Admin.html")
    def icst_admin():
        return render_template("ICST-Admin.html")

    @app.route("/ICST-Delivery.html")
    def icst_delivery():
        return render_template("ICST-Delivery.html")

    @app.route("/ICST-AI-Ordering.html")
    def icst_ai_ordering():
        return render_template("ICST-AI-Ordering.html")

    @app.route("/FoodieDash.html")
    def foodiedash():
        return render_template("FoodieDash.html")

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"message": "Resource not found."}), 404
        return render_template("index.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"message": "Internal server error."}), 500

    return app


application = create_app()
app = application


def _pick_port():
    preferred = int(os.getenv("PORT", 5000))
    for port in (preferred, 5001, 5002, 8080):
        yield port


if __name__ == "__main__":
    import socket
    import sys
    import threading
    import time
    import webbrowser

    def port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False

    started = False
    for port in _pick_port():
        if not port_available(port):
            print(f"Port {port} is already in use, trying another port...")
            continue

        try:
            if os.getenv("FLASK_OPEN_BROWSER", "1") != "0":

                def open_browser(target_port=port):
                    time.sleep(1.5)
                    webbrowser.open(f"http://127.0.0.1:{target_port}/")

                threading.Thread(target=open_browser, daemon=True).start()

            print(f"\nQuickBite is running at http://127.0.0.1:{port}/")
            print("Press Ctrl+C to stop.\n")
            started = True
            application.run(
                host="127.0.0.1",
                port=port,
                debug=Config.DEBUG,
                use_reloader=False,
            )
        except OSError as error:
            if getattr(error, "winerror", None) == 10048 or "address" in str(error).lower():
                print(f"Port {port} is already in use, trying another port...")
                continue
            raise

    if not started:
        print("Could not start the server. Close other apps using ports 5000-5002 and try again.")
        sys.exit(1)
