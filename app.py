"""
app.py — Telco Operator Intelligence Platform
Flask backend with Firebase Auth verification + telecom analytics APIs.
"""

import os
import json
import functools
from flask import Flask, request, jsonify, render_template, redirect, url_for

import firebase_admin
from firebase_admin import credentials, auth as fb_auth

import data_utils
import db_utils

import data_utils
import db_utils

# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET", "telco-intel-secret-2026")

# Initialize Firebase Admin SDK
_SA_KEY = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
if os.path.exists(_SA_KEY):
    cred = credentials.Certificate(_SA_KEY)
    firebase_admin.initialize_app(cred)
    FIREBASE_ENABLED = True
    print("[Firebase] Admin SDK initialized from serviceAccountKey.json")
    
    # Init Firestore default admin if required
    db_utils.init_db()
else:
    # Demo mode — Firebase verification skipped (for local dev without key)
    FIREBASE_ENABLED = False
    print("[Firebase] serviceAccountKey.json not found — running in DEMO mode (no token verification)")

# Load datasets at startup
data_utils.load_datasets()
data_utils.load_ml_models()


# ─────────────────────────────────────────────
# Firebase Token Verification
# ─────────────────────────────────────────────

def verify_token():
    """Extract and verify Firebase ID token from Authorization header."""
    user = None
    if not FIREBASE_ENABLED:
        # Demo mode: return mock user
        user = {"uid": "demo-user", "email": "demo@telco.com"}
    else:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None, (jsonify({"error": "Unauthorized — missing token"}), 401)

        id_token = auth_header.split("Bearer ")[1].strip()
        try:
            user = fb_auth.verify_id_token(id_token)
        except Exception as e:
            return None, (jsonify({"error": f"Unauthorized — {str(e)}"}), 401)

    if user:
        # Sync user and update session persistence
        db_utils.sync_user(user["uid"], user["email"])
        db_utils.update_session(user["uid"], request.remote_addr)
        return user, None
    
    return None, (jsonify({"error": "Unauthorized"}), 401)


def firebase_required(f):
    """Decorator that enforces Firebase token verification on API routes."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user, err = verify_token()
        if err:
            return err
        request.firebase_user = user
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator that enforces Admin role."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user, err = verify_token()
        if err: return err
        
        role = db_utils.get_user_role(user["uid"])
        if role != "ADMIN":
            return jsonify({"error": "Forbidden — Admin access required"}), 403
            
        request.firebase_user = user
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Page Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ─────────────────────────────────────────────
# API: Firebase Config (for frontend)
# ─────────────────────────────────────────────

@app.route("/api/firebase-config")
def firebase_config():
    """Return Firebase client config."""
    return jsonify({
        "apiKey":            "AIzaSyC4y_pFnIUUvnBTvzUpiXP8qRzLMywFkR8",
        "authDomain":        "telecom-a3527.firebaseapp.com",
        "projectId":         "telecom-a3527",
        "storageBucket":     "telecom-a3527.firebasestorage.app",
        "messagingSenderId": "48619126415",
        "appId":             "1:48619126415:web:c68cf6b07411d5be957afa",
        "measurementId":     "G-S3JP9040EN"
    })


# ─────────────────────────────────────────────
# API: Overview
# ─────────────────────────────────────────────

@app.route("/api/overview")
@firebase_required
def api_overview():
    op_key = request.args.get("op", "")
    op_map = {"Airtel": "airtel", "BSNL": "bsnl", "Jio": "jio", "Vi": "vi"}
    op_key_lower = op_map.get(op_key)
    
    data = data_utils.compute_overview(op_key_lower)
    return jsonify(data)


# ─────────────────────────────────────────────
# API: Operators
# ─────────────────────────────────────────────

@app.route("/api/operators")
@firebase_required
def api_operators():
    data = data_utils.compute_operators()
    return jsonify(data)


# ─────────────────────────────────────────────
# API: Regions
# ─────────────────────────────────────────────

@app.route("/api/regions")
@firebase_required
def api_regions():
    limit = int(request.args.get("limit", 60))
    op_key = request.args.get("op", "")
    op_map = {"Airtel": "airtel", "BSNL": "bsnl", "Jio": "jio", "Vi": "vi"}
    op_key_lower = op_map.get(op_key)

    data = data_utils.compute_regions(limit=limit, operator_key=op_key_lower)
    return jsonify(data)


# ─────────────────────────────────────────────
# API: Customers
# ─────────────────────────────────────────────

@app.route("/api/customers")
@firebase_required
def api_customers():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    op_key = request.args.get("op", "")
    op_map = {"Airtel": "airtel", "BSNL": "bsnl", "Jio": "jio", "Vi": "vi"}
    op_key_lower = op_map.get(op_key)

    data = data_utils.get_customers(limit=limit, offset=offset, operator_key=op_key_lower)
    return jsonify(data)


# ─────────────────────────────────────────────
# API: Geography helpers
# ─────────────────────────────────────────────

@app.route("/api/geo/states")
@firebase_required
def api_states():
    return jsonify(data_utils.get_states())


@app.route("/api/geo/cities")
@firebase_required
def api_cities():
    state = request.args.get("state", "")
    return jsonify(data_utils.get_cities(state))


@app.route("/api/geo/areas")
@firebase_required
def api_areas():
    state = request.args.get("state", "")
    city  = request.args.get("city", "")
    return jsonify(data_utils.get_areas(state, city))


# ─────────────────────────────────────────────
# API: Churn Prediction
# ─────────────────────────────────────────────

@app.route("/api/predict_churn_latency", methods=["POST"])
@firebase_required
def api_predict_churn_latency():
    user = request.firebase_user
    usage = db_utils.get_usage(user["uid"])
    
    # Trial enforcement (Bypassed for ADMIN)
    role = db_utils.get_user_role(user["uid"])
    if role != "ADMIN" and usage["subscription_status"] == "FREE" and usage["churn_trials"] >= 4:
        return jsonify({"error": "trial_expired", "message": "You have reached the limit of 4 free churn predictions. Please upgrade to Pro."}), 403

    body = request.get_json(force=True) or {}
    operator        = body.get("operator", "")
    state           = body.get("state", "")
    network_type    = body.get("network_type", "")
    plan_type       = body.get("plan_type", "")
    signal_dbm      = float(body.get("signal_dbm", -85))
    months_active   = int(body.get("months_active", 12))
    issues_resolved = int(body.get("issues_resolved", 0))

    if not state:
        return jsonify({"error": "state is required"}), 400

    result = data_utils.predict_churn_latency(
        operator=operator,
        state=state,
        network_type=network_type,
        plan_type=plan_type,
        signal_dbm=signal_dbm,
        months_active=months_active,
        issues_resolved=issues_resolved
    )
    
    # Increment usage
    db_utils.increment_usage(user["uid"], "churn")
    
    return jsonify(result)


# ─────────────────────────────────────────────
# API: Demand Forecast
# ─────────────────────────────────────────────

@app.route("/api/forecast", methods=["POST"])
@firebase_required
def api_forecast():
    user = request.firebase_user
    usage = db_utils.get_usage(user["uid"])
    
    # Trial enforcement (Bypassed for ADMIN)
    role = db_utils.get_user_role(user["uid"])
    if role != "ADMIN" and usage["subscription_status"] == "FREE" and usage["forecast_trials"] >= 4:
        return jsonify({"error": "trial_expired", "message": "You have reached the limit of 4 free demand forecasts. Please upgrade to Pro."}), 403

    body = request.get_json(force=True) or {}
    operator = body.get("operator", "")
    state    = body.get("state", "")
    city     = body.get("city", "")
    area     = body.get("area", "")
    days     = int(body.get("days", 30))

    if days not in [30, 60, 90]:
        days = 30

    if not all([state, city, area]):
        return jsonify({"error": "state, city, and area are required"}), 400

    result = data_utils.generate_forecast(operator, state, city, area, days)
    
    # Increment usage
    db_utils.increment_usage(user["uid"], "forecast")
    
    return jsonify(result)


# ─────────────────────────────────────────────
# API: Admin
# ─────────────────────────────────────────────

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

@app.route("/api/admin/sessions")
@admin_required
def api_admin_sessions():
    return jsonify(db_utils.get_session_data())

@app.route("/api/admin/stats")
@admin_required
def api_admin_stats():
    return jsonify(db_utils.get_admin_stats())

@app.route("/api/admin/users")
@admin_required
def api_admin_users():
    return jsonify(db_utils.get_all_users())

@app.route("/api/user/usage")
@firebase_required
def api_user_usage():
    user = request.firebase_user
    usage = db_utils.get_usage(user["uid"])
    usage["role"] = db_utils.get_user_role(user["uid"])
    return jsonify(usage)


# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
