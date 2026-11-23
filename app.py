import math
import os
import uuid
from datetime import date, datetime
from functools import wraps
import secrets
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_file, render_template, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

from controller import NexusIntegrationController

PROJECT_NAME = "NEXUS"
PROJECT_VERSION = "1.0.0"
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"
DATABASE_PATH = BASE_DIR / "nexus_users.db"
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
if not os.environ.get("NEXUS_SECRET_KEY") and not (BASE_DIR / ".nexus_secret_key").exists():
    generated_secret = secrets.token_hex(32)
    (BASE_DIR / ".nexus_secret_key").write_text(generated_secret, encoding="utf-8")

app.config.update(
    UPLOAD_FOLDER=str(UPLOAD_DIR),
    REPORT_FOLDER=str(REPORT_DIR),
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    SECRET_KEY=os.environ.get("NEXUS_SECRET_KEY") or (
        (BASE_DIR / ".nexus_secret_key").read_text(encoding="utf-8")
        if (BASE_DIR / ".nexus_secret_key").exists()
        else secrets.token_hex(32)
    ),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("NEXUS_HTTPS", "0") == "1",
)

# Reports are deliberately written to the same directory served by the
# report-download endpoint.
controller = NexusIntegrationController(report_directory=str(REPORT_DIR))


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_auth_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


init_auth_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return error_response("Authentication required. Please sign in.", 401)
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as connection:
        row = connection.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def make_json_safe(value):
    """Convert Pandas, NumPy, Plotly and date values into JSON-safe values."""
    if value is None or value is pd.NA:
        return None
    if isinstance(value, pd.DataFrame):
        clean = value.astype(object).where(pd.notna(value), None)
        return {"columns": [str(c) for c in clean.columns],
                "data": make_json_safe(clean.to_dict(orient="records"))}
    if isinstance(value, pd.Series):
        return make_json_safe(value.to_dict())
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return make_json_safe(value.tolist())
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_plotly_json"):
        return make_json_safe(value.to_plotly_json())
    if isinstance(value, (str, int, bool)):
        return value
    return str(value)


def success_response(message, data=None, status_code=200):
    return jsonify({
        "success": True,
        "message": message,
        "data": make_json_safe(data),
    }), status_code


def error_response(message, status_code=400):
    return jsonify({"success": False, "error": str(message)}), status_code


@app.get("/")
@login_required
def home():
    """Serve the authenticated NEXUS dashboard."""
    user = current_user()
    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template("index.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("home"))
    if request.method == "POST":
        from werkzeug.security import generate_password_hash
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or len(name) > 80 or "@" not in email or len(email) > 254:
            flash("Enter a valid name and email address.", "error")
        elif len(password) < 8:
            flash("Your password must contain at least 8 characters.", "error")
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            try:
                with get_db() as connection:
                    cursor = connection.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password))
                    )
                    session.clear()
                    session["user_id"] = cursor.lastrowid
                    session.permanent = True
                return redirect(url_for("home"))
            except sqlite3.IntegrityError:
                flash("An account with that email already exists. Sign in instead.", "error")
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("home"))
    if request.method == "POST":
        from werkzeug.security import check_password_hash
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as connection:
            user = connection.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = True
            return redirect(url_for("home"))
        flash("The email or password is incorrect.", "error")
    return render_template("auth.html", mode="login")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/account")
@login_required
def account_settings():
    return render_template("account.html", user=current_user())


@app.get("/api/health")
def health_check():
    return success_response("NEXUS backend is running.", {
        "application": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "status": "running",
    })


@app.get("/api/status")
@login_required
def pipeline_status():
    try:
        return success_response(
            "Pipeline status retrieved.",
            controller.get_pipeline_status(),
        )
    except Exception as error:
        app.logger.exception("Pipeline status failed")
        return error_response(error, 500)


@app.post("/api/upload")
@login_required
def upload_dataset():
    if "file" not in request.files:
        return error_response("No file was provided.")
    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return error_response("No filename was provided.")

    original_name = secure_filename(uploaded_file.filename)
    extension = Path(original_name).suffix.lower()
    if not original_name or extension not in ALLOWED_EXTENSIONS:
        return error_response("Unsupported file format. Upload CSV or Excel.")

    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    saved_path = UPLOAD_DIR / stored_name
    try:
        uploaded_file.save(saved_path)
        if saved_path.stat().st_size == 0:
            saved_path.unlink(missing_ok=True)
            return error_response("Uploaded file is empty.")
        loaded = controller.load_dataset(str(saved_path))
        return success_response("Dataset uploaded and loaded successfully.", {
            "filename": original_name,
            "stored_filename": stored_name,
            "file_size": saved_path.stat().st_size,
            "rows": int(loaded.shape[0]),
            "columns": int(loaded.shape[1]),
            "column_names": [str(c) for c in loaded.columns],
        }, 201)
    except Exception as error:
        saved_path.unlink(missing_ok=True)
        app.logger.exception("Dataset upload failed")
        return error_response(error, 400)


@app.post("/api/inspect")
@login_required
def inspect_dataset():
    try:
        return success_response(
            "Dataset inspection completed.",
            controller.inspect_dataset(),
        )
    except Exception as error:
        return error_response(error, 400)


@app.post("/api/clean")
@login_required
def clean_dataset():
    """Expected body: {"operations":[{"name":"remove_duplicates","parameters":{}}]}"""
    try:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error_response("A JSON object is required.")
        operations = payload.get("operations", [])
        if not isinstance(operations, list):
            return error_response("'operations' must be a list.")
        # Do not silently accept unknown keys or accidentally report a no-op
        # as a successful cleaning operation.
        if set(payload) - {"operations"}:
            return error_response("Unsupported cleaning request fields.")
        cleaned = controller.clean_dataset(operations=operations)
        return success_response("Dataset cleaning completed.", {
            "rows": int(cleaned.shape[0]),
            "columns": int(cleaned.shape[1]),
            "cleaning_history": controller.cleaner.get_cleaning_report(),
            "cleaned_data": cleaned,
        })
    except Exception as error:
        return error_response(error, 400)


@app.post("/api/analyze")
@login_required
def analyze_dataset():
    try:
        return success_response(
            "Data analysis completed.",
            controller.analyze_dataset(),
        )
    except Exception as error:
        return error_response(error, 400)


@app.post("/api/visualizations")
@login_required
def create_visualizations():
    try:
        charts = controller.create_visualizations()
        # Return Plotly figure JSON, not Python figure objects.
        return success_response("Visualizations generated.", charts)
    except Exception as error:
        return error_response(error, 400)


@app.post("/api/report")
@login_required
def generate_report():
    try:
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return error_response("A JSON object is required.")
        filename = payload.get("filename")
        if filename is not None and not isinstance(filename, str):
            return error_response("'filename' must be a string.")
        result = controller.generate_report(filename=filename)
        return success_response("Report generated successfully.", result, 201)
    except Exception as error:
        return error_response(error, 400)


@app.get("/api/reports/<filename>")
@login_required
def download_report(filename):
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        return error_response("Invalid report filename.", 400)
    report_path = (REPORT_DIR / safe_name).resolve()
    if report_path.parent != REPORT_DIR.resolve():
        return error_response("Invalid report path.", 400)
    if not report_path.is_file() or report_path.suffix.lower() != ".pdf":
        return error_response("Report not found.", 404)
    return send_file(
        report_path,
        as_attachment=True,
        download_name=safe_name,
        mimetype="application/pdf",
    )


@app.errorhandler(413)
def file_too_large(_error):
    return error_response("Upload exceeds the 50 MB limit.", 413)


@app.errorhandler(404)
def route_not_found(_error):
    return error_response("The requested API endpoint does not exist.", 404)


if __name__ == "__main__":
    # Development server only. Use a production WSGI server for deployment.
    app.run(host="127.0.0.1", port=5000, debug=False)
