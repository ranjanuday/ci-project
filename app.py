from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
from werkzeug.utils import secure_filename
import bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re

app = Flask(__name__)
app.secret_key = "secret"

# --- Rate Limiter ---
limiter = Limiter(get_remote_address, app=app, default_limits=["5 per minute"])

# --- Upload Config ---
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "jpg", "jpeg", "png"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# --- Helpers ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

# --- DB ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Uday@123",
        database="student_db"
    )

# --- Routes ---
@app.route("/")
def home():
    return redirect("/login")

# --- Login ---
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            stored_hash = user["password"]
            if stored_hash and bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                session["username"] = user["username"]
                session["role"] = user["role"]
                return redirect("/dashboard")
        return "Invalid credentials"

    return render_template("login.html")

# --- Register ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        role = request.form["role"].strip()

        if not is_strong_password(password):
            return "Password must be strong (8+, A-Z, a-z, 0-9, special char)"

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed_pw, role)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/login")

    return render_template("register.html")

# --- Dashboard ---
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("dashboard.html",
                           username=session["username"],
                           role=session["role"],
                           students=students)

# --- Admin Panel (FIXED) ---
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if session.get("role") != "admin":
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # ✅ UPDATE FIRST
    if request.method == "POST":
        username = request.form["username"]
        role = request.form["role"]

        cursor.execute(
            "UPDATE users SET role=%s WHERE username=%s",
            (role, username)
        )
        conn.commit()

    # ✅ FETCH AFTER UPDATE
    cursor.execute("SELECT username, role FROM users")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin.html",
                           username=session.get("username"),
                           users=users)

# --- Upload ---
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]

        if file.filename == "":
            return "No file selected"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return f"File {filename} uploaded successfully!"
        else:
            return "File type not allowed"

    return '''
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
    '''

# --- Add Student ---
@app.route("/student/add", methods=["GET", "POST"])
def add_student():
    if session.get("role") != "admin":
        return "Access denied", 403

    if request.method == "POST":
        name = request.form["name"]
        grade = request.form["grade"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, grade) VALUES (%s, %s)", (name, grade))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/dashboard")

    return '''
        <form method="post">
            Name: <input type="text" name="name"><br>
            Grade: <input type="text" name="grade"><br>
            <input type="submit" value="Add Student">
        </form>
    '''

# --- API ---
@app.route("/api/students")
def api_students():
    if session.get("role") != "admin":
        return {"error": "Access denied"}, 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"students": students}

# --- Logout ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# --- Run ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)