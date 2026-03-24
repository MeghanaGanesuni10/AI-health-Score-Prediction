"""
Flask Backend for AI-Powered Preventive Healthcare Score System.
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from gemini_ai import (
    calculate_health_score,
    get_chatbot_response,
    generate_monthly_report,
    get_doctor_recommendation
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
CORS(app, supports_credentials=True, origins=["*"])

DATABASE = os.path.join(os.path.dirname(__file__), "database.db")


@app.route("/")
def serve_index():
    return app.send_static_file("login.html")


@app.route("/<path:filename>")
def serve_static(filename):
    try:
        return app.send_static_file(filename)
    except Exception:
        return app.send_static_file("login.html")


# ─── Database ────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS health_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            bmi REAL,
            blood_pressure TEXT,
            sugar_level REAL,
            heart_rate REAL,
            sleep_hours REAL,
            exercise_minutes REAL,
            steps_per_day REAL,
            water_intake REAL,
            smoking TEXT,
            alcohol TEXT,
            score INTEGER,
            risk_level TEXT,
            recommendations TEXT,
            summary TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    """)
    conn.commit()
    conn.close()


# ─── Helpers ─────────────────────────────────────────────────────────

def hash_password(password):
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"


def verify_password(stored, password):
    try:
        salt, pwd_hash = stored.split(":")
        return hashlib.sha256((salt + password).encode()).hexdigest() == pwd_hash
    except Exception:
        return False


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Auth Routes ─────────────────────────────────────────────────────

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Email already registered"}), 409

    pwd_hash = hash_password(password)
    conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                 (name, email, pwd_hash))
    conn.commit()
    conn.close()
    return jsonify({"message": "Registration successful"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not verify_password(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    return jsonify({
        "message": "Login successful",
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
    })


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@app.route("/check-session", methods=["GET"])
def check_session():
    if "user_id" in session:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": session["user_id"],
                "name": session["user_name"],
                "email": session["user_email"]
            }
        })
    return jsonify({"authenticated": False}), 401


# ─── Health Data Routes ─────────────────────────────────────────────

@app.route("/submit-health-data", methods=["POST"])
@login_required
def submit_health_data():
    data = request.get_json()

    # Calculate BMI
    try:
        height_m = float(data.get("height", 0)) / 100
        weight = float(data.get("weight", 0))
        bmi = round(weight / (height_m ** 2), 1) if height_m > 0 else 0
    except (ValueError, ZeroDivisionError):
        bmi = 0

    data["bmi"] = bmi

    # Get AI health score
    ai_result = calculate_health_score(data)
    score = ai_result.get("score", 50)
    risk_level = ai_result.get("risk_level", "Moderate")
    recommendations = ai_result.get("recommendations", [])
    summary = ai_result.get("summary", "")

    # Get doctor recommendations
    doctor_recs = get_doctor_recommendation(score, risk_level, data)

    # Save to database
    conn = get_db()
    conn.execute("""
        INSERT INTO health_data
        (user_id, name, age, gender, height, weight, bmi, blood_pressure,
         sugar_level, heart_rate, sleep_hours, exercise_minutes, steps_per_day,
         water_intake, smoking, alcohol, score, risk_level, recommendations, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        data.get("name", ""),
        data.get("age"),
        data.get("gender", ""),
        data.get("height"),
        data.get("weight"),
        bmi,
        data.get("blood_pressure", ""),
        data.get("sugar_level"),
        data.get("heart_rate"),
        data.get("sleep_hours"),
        data.get("exercise_minutes"),
        data.get("steps_per_day"),
        data.get("water_intake"),
        data.get("smoking", "No"),
        data.get("alcohol", "No"),
        score,
        risk_level,
        str(recommendations),
        summary
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "score": score,
        "risk_level": risk_level,
        "bmi": bmi,
        "recommendations": recommendations,
        "summary": summary,
        "doctor_recommendations": doctor_recs
    })


@app.route("/get-score", methods=["GET"])
@login_required
def get_score():
    conn = get_db()
    # Latest entry
    latest = conn.execute(
        "SELECT * FROM health_data WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
        (session["user_id"],)
    ).fetchone()

    # Score history (last 30 entries)
    history = conn.execute(
        "SELECT score, risk_level, bmi, timestamp FROM health_data WHERE user_id = ? ORDER BY timestamp DESC LIMIT 30",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    if not latest:
        return jsonify({"error": "No health data found. Please submit your health data first."}), 404

    # Parse recommendations
    try:
        recs = eval(latest["recommendations"]) if latest["recommendations"] else []
    except Exception:
        recs = []

    doctor_recs = get_doctor_recommendation(
        latest["score"],
        latest["risk_level"],
        dict(latest)
    )

    return jsonify({
        "latest": {
            "score": latest["score"],
            "risk_level": latest["risk_level"],
            "bmi": latest["bmi"],
            "blood_pressure": latest["blood_pressure"],
            "sugar_level": latest["sugar_level"],
            "heart_rate": latest["heart_rate"],
            "sleep_hours": latest["sleep_hours"],
            "exercise_minutes": latest["exercise_minutes"],
            "steps_per_day": latest["steps_per_day"],
            "water_intake": latest["water_intake"],
            "smoking": latest["smoking"],
            "alcohol": latest["alcohol"],
            "recommendations": recs,
            "summary": latest["summary"],
            "timestamp": latest["timestamp"]
        },
        "history": [
            {
                "score": h["score"],
                "risk_level": h["risk_level"],
                "bmi": h["bmi"],
                "timestamp": h["timestamp"]
            }
            for h in reversed(list(history))
        ],
        "doctor_recommendations": doctor_recs
    })


@app.route("/get-report", methods=["GET"])
@login_required
def get_report():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn = get_db()
    entries = conn.execute(
        "SELECT * FROM health_data WHERE user_id = ? AND strftime('%Y-%m', timestamp) = ? ORDER BY timestamp",
        (session["user_id"], month)
    ).fetchall()
    conn.close()

    if not entries:
        return jsonify({"error": f"No health data found for {month}."}), 404

    data_list = [dict(e) for e in entries]

    # Parse recommendations for each entry
    for entry in data_list:
        try:
            entry["recommendations"] = eval(entry["recommendations"]) if entry["recommendations"] else []
        except Exception:
            entry["recommendations"] = []

    report = generate_monthly_report(data_list)
    report["entries"] = [
        {
            "score": e["score"],
            "risk_level": e["risk_level"],
            "bmi": e["bmi"],
            "blood_pressure": e["blood_pressure"],
            "sugar_level": e["sugar_level"],
            "heart_rate": e["heart_rate"],
            "sleep_hours": e["sleep_hours"],
            "exercise_minutes": e["exercise_minutes"],
            "steps_per_day": e["steps_per_day"],
            "water_intake": e["water_intake"],
            "timestamp": e["timestamp"]
        }
        for e in data_list
    ]
    report["month"] = month

    return jsonify(report)


@app.route("/chatbot", methods=["POST"])
@login_required
def chatbot():
    data = request.get_json()
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Message is required"}), 400

    response = get_chatbot_response(message, history)
    return jsonify({"response": response})


# ─── Start ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("[OK] Database initialized")
    print("[OK] Starting Healthcare Score API on http://localhost:5000")
    app.run(debug=True, port=5000)
from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='../frontend')

@app.route('/')
def home():
    return send_from_directory('../frontend', 'index.html')
