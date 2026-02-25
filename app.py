from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import qrcode
import os, random, string, io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from onedrive_helper import read_excel_from_onedrive, write_excel_to_onedrive

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")
APP_URL = os.environ.get("APP_URL", "http://localhost:5000")

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

PASS_SCORE = 60

def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_certificate(username, score, cert_id):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    c.setFillColor(colors.HexColor("#f0f4ff"))
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#2c3e95"))
    c.setLineWidth(8)
    c.rect(20, 20, width-40, height-40, fill=0, stroke=1)
    c.setFillColor(colors.HexColor("#2c3e95"))
    c.setFont("Helvetica-Bold", 42)
    c.drawCentredString(width/2, height-110, "CERTIFICATE OF COMPLETION")
    c.setStrokeColor(colors.HexColor("#f39c12"))
    c.setLineWidth(3)
    c.line(80, height-130, width-80, height-130)
    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 20)
    c.drawCentredString(width/2, height-175, "This is to certify that")
    c.setFillColor(colors.HexColor("#2c3e95"))
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width/2, height-225, username.upper())
    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 20)
    c.drawCentredString(width/2, height-270, "has successfully completed the examination")
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#27ae60"))
    c.drawCentredString(width/2, height-315, f"with a score of {score}%")
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#777777"))
    c.drawCentredString(width/2, height-370, f"Date: {datetime.now().strftime('%B %d, %Y')}   |   Certificate ID: {cert_id}")
    c.save()
    buffer.seek(0)
    return buffer

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
        if len(df) > 0 and username in df["username"].str.lower().values:
            return render_template("register.html", error="Username already exists. Please login.", show_login=True)
        password = generate_password()
        new_row = pd.DataFrame([{"username": username, "password": password, "registered_date": datetime.now().strftime("%Y-%m-%d %H:%M")}])
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
        results_df = read_excel_from_onedrive("ExamResults")
        if len(results_df) > 0:
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
        score = sum(1 for i, q in enumerate(QUESTIONS) if request.form.get(f"q{i}") == q["answer"])
        percent = round((score / len(QUESTIONS)) * 100)
        passed = percent >= PASS_SCORE
        username = session["username"]
        cert_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        results_df = read_excel_from_onedrive("ExamResults")
        new_row = pd.DataFrame([{"username": username, "score": percent, "passed": passed, "cert_id": cert_id if passed else "", "date": datetime.now().strftime("%Y-%m-%d %H:%M")}])
        results_df = pd.concat([results_df, new_row], ignore_index=True)
        write_excel_to_onedrive(results_df, "ExamResults")
        if passed:
            session["cert_id"] = cert_id
            session["score"] = percent
            return redirect(url_for("certificate"))
        return render_template("result.html", passed=False, score=percent, pass_score=PASS_SCORE)
    return render_template("exam.html", questions=QUESTIONS, total=len(QUESTIONS))

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
    if "username" not in session:
        return redirect(url_for("login"))
    buffer = generate_certificate(session["username"], session.get("score", 0), session.get("cert_id", ""))
    return send_file(buffer, as_attachment=True, download_name=f"certificate_{session['username']}.pdf", mimetype="application/pdf")

@app.route("/generate_qr")
def generate_qr():
    img = qrcode.make(APP_URL)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype="image/png", download_name="exam_qr_code.png")

if __name__ == "__main__":
    app.run(debug=True)
