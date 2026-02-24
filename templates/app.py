from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import qrcode
import os
import random
import string
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from onedrive_helper import read_excel_from_onedrive, write_excel_to_onedrive

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Your app's public URL (update after deploying to Render/Railway)
APP_URL = os.environ.get("APP_URL", "http://localhost:5000")

# ─── Sample MCQ Questions (Edit these!) ───────────────────────────────────────
QUESTIONS = [
    {
        "question": "What does HTML stand for?",
        "options": ["Hyper Text Markup Language", "High Tech Machine Learning", "Home Tool Markup Language", "Hyperlink Text Mode Language"],
        "answer": "Hyper Text Markup Language"
    },
    {
        "question": "Which language is used for styling web pages?",
        "options": ["Java", "Python", "CSS", "C++"],
        "answer": "CSS"
    },
    {
        "question": "What does CSS stand for?",
        "options": ["Computer Style Sheets", "Cascading Style Sheets", "Creative Style System", "Colorful Style Sheets"],
        "answer": "Cascading Style Sheets"
    },
    {
        "question": "Which of the following is a Python web framework?",
        "options": ["Django", "Laravel", "Rails", "Express"],
        "answer": "Django"
    },
    {
        "question": "What does QR stand for in QR Code?",
        "options": ["Quick Response", "Quality Resolution", "Queue Request", "Quick Read"],
        "answer": "Quick Response"
    },
]

PASS_SCORE = 60  # Minimum % to pass

# ─── Helper: Generate Password ─────────────────────────────────────────────────
def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

# ─── Helper: Generate Certificate PDF ─────────────────────────────────────────
def generate_certificate(username, score, cert_id):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Background
    c.setFillColor(colors.HexColor("#f0f4ff"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Border
    c.setStrokeColor(colors.HexColor("#2c3e95"))
    c.setLineWidth(8)
    c.rect(20, 20, width - 40, height - 40, fill=0, stroke=1)
    c.setLineWidth(2)
    c.rect(30, 30, width - 60, height - 60, fill=0, stroke=1)

    # Title
    c.setFillColor(colors.HexColor("#2c3e95"))
    c.setFont("Helvetica-Bold", 42)
    c.drawCentredString(width / 2, height - 110, "CERTIFICATE OF COMPLETION")

    # Divider
    c.setStrokeColor(colors.HexColor("#f39c12"))
    c.setLineWidth(3)
    c.line(80, height - 130, width - 80, height - 130)

    # Body
    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 20)
    c.drawCentredString(width / 2, height - 175, "This is to certify that")

    c.setFillColor(colors.HexColor("#2c3e95"))
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, height - 225, username.upper())

    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 20)
    c.drawCentredString(width / 2, height - 270, "has successfully completed the examination")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#27ae60"))
    c.drawCentredString(width / 2, height - 315, f"with a score of {score}%")

    # Date and ID
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#777777"))
    c.drawCentredString(width / 2, height - 370, f"Date: {datetime.now().strftime('%B %d, %Y')}   |   Certificate ID: {cert_id}")

    c.save()
    buffer.seek(0)
    return buffer

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        if not username:
            return render_template("register.html", error="Please enter a username.")

        df = read_excel_from_onedrive("Users")

        if username in df["username"].str.lower().values:
            return render_template("register.html", error="Username already exists. Please login instead.", show_login=True)

        password = generate_password()
        new_row = pd.DataFrame([{
            "username": username,
            "password": password,
            "registered_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        write_excel_to_onedrive(df, "Users")

        return render_template("register.html", success=True, username=username, password=password)

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()

        df = read_excel_from_onedrive("Users")
        user = df[(df["username"].str.lower() == username) & (df["password"] == password)]

        if user.empty:
            return render_template("login.html", error="Invalid username or password.")

        # Check if already passed
        results_df = read_excel_from_onedrive("ExamResults")
        passed = results_df[(results_df["username"].str.lower() == username) & (results_df["passed"] == True)]
        if not passed.empty:
            session["username"] = username
            return redirect(url_for("certificate"))

        session["username"] = username
        return redirect(url_for("exam"))

    return render_template("login.html")

@app.route("/exam", methods=["GET", "POST"])
def exam():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        score = 0
        for i, q in enumerate(QUESTIONS):
            ans = request.form.get(f"q{i}")
            if ans == q["answer"]:
                score += 1

        percent = round((score / len(QUESTIONS)) * 100)
        passed = percent >= PASS_SCORE
        username = session["username"]

        # Save result
        results_df = read_excel_from_onedrive("ExamResults")
        cert_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        new_row = pd.DataFrame([{
            "username": username,
            "score": percent,
            "passed": passed,
            "cert_id": cert_id if passed else "",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        results_df = pd.concat([results_df, new_row], ignore_index=True)
        write_excel_to_onedrive(results_df, "ExamResults")

        if passed:
            session["cert_id"] = cert_id
            session["score"] = percent
            return redirect(url_for("certificate"))
        else:
            return render_template("result.html", passed=False, score=percent, pass_score=PASS_SCORE)

    return render_template("exam.html", questions=QUESTIONS)

@app.route("/certificate")
def certificate():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    results_df = read_excel_from_onedrive("ExamResults")
    user_result = results_df[(results_df["username"].str.lower() == username) & (results_df["passed"] == True)]

    if user_result.empty:
        return redirect(url_for("exam"))

    cert_id = user_result.iloc[-1]["cert_id"]
    score = user_result.iloc[-1]["score"]
    session["cert_id"] = cert_id
    session["score"] = score

    return render_template("certificate.html", username=username, score=score, cert_id=cert_id)

@app.route("/download_certificate")
def download_certificate():
    if "username" not in session or "cert_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    score = session.get("score", 0)
    cert_id = session["cert_id"]

    buffer = generate_certificate(username, score, cert_id)
    return send_file(buffer, as_attachment=True, download_name=f"certificate_{username}.pdf", mimetype="application/pdf")

@app.route("/generate_qr")
def generate_qr():
    img = qrcode.make(APP_URL)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name="exam_qr_code.png")

if __name__ == "__main__":
    app.run(debug=True)
