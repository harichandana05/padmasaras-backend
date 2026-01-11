from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, json

from translator import translate_text
from db import get_db_connection

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
VOCAB_FILE = os.path.join(BASE_DIR, "vocabulary.json")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return "Backend is running"

# ---------- LOGIN ----------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT id,name,role FROM users WHERE email=%s AND password=%s",
        (data["email"], data["password"])
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return jsonify(user)
    return jsonify({"message": "Invalid credentials"}), 401

# ---------- STUDENTS ----------
@app.route("/students")
def students():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id,name FROM users WHERE role='student'")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# ---------- UPLOAD PDF ----------
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    file = request.files.get("pdf")
    teacher_id = request.form.get("teacher_id")

    if not file or not teacher_id:
        return jsonify({"message": "Missing PDF or teacher ID"}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pdfs (filename, uploaded_by) VALUES (%s,%s)",
        (filename, teacher_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "PDF uploaded successfully"})

# ---------- LIST PDFs ----------
@app.route("/list_pdfs")
def list_pdfs():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id,filename FROM pdfs ORDER BY id DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# ---------- DELETE PDF ----------
@app.route("/delete_pdf/<int:pdf_id>", methods=["DELETE"])
def delete_pdf(pdf_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT filename FROM pdfs WHERE id=%s", (pdf_id,))
    pdf = cur.fetchone()

    if not pdf:
        cur.close()
        conn.close()
        return jsonify({"message": "PDF not found"}), 404

    path = os.path.join(UPLOAD_FOLDER, pdf["filename"])
    if os.path.exists(path):
        os.remove(path)

    cur.execute("DELETE FROM assignments WHERE pdf_id=%s", (pdf_id,))
    cur.execute("DELETE FROM pdfs WHERE id=%s", (pdf_id,))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"message": "PDF deleted successfully"})

# ---------- ASSIGN PDF ----------
@app.route("/assign_pdf", methods=["POST"])
def assign_pdf():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO assignments (student_id,pdf_id) VALUES (%s,%s)",
        (data["student_id"], data["pdf_id"])
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "PDF assigned successfully"})

# ---------- STUDENT PDFs ----------
@app.route("/student_pdfs/<int:sid>")
def student_pdfs(sid):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT p.filename
        FROM pdfs p
        JOIN assignments a ON a.pdf_id = p.id
        WHERE a.student_id = %s
    """,(sid,))

    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# ---------- STUDENT RESULTS ----------
@app.route("/student_results/<int:sid>")
def student_results(sid):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT p.filename,s.marks,s.feedback
        FROM submissions s
        JOIN pdfs p ON p.id=s.pdf_id
        WHERE s.student_id=%s
    """,(sid,))

    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# ---------- SUBMISSIONS ----------
@app.route("/submissions")
def submissions():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT s.id,u.name AS student_name,p.filename,s.marks,s.feedback
        FROM submissions s
        JOIN users u ON u.id=s.student_id
        JOIN pdfs p ON p.id=s.pdf_id
        ORDER BY s.id DESC
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# ---------- ADD MARKS ----------
@app.route("/add_marks", methods=["POST"])
def add_marks():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE submissions SET marks=%s,feedback=%s WHERE id=%s
    """,(data["marks"],data["feedback"],data["submission_id"]))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Marks saved"})

# ---------- ADD WORD ----------
@app.route("/add_word", methods=["POST"])
def add_word():
    data = request.get_json()

    if not os.path.exists(VOCAB_FILE):
        with open(VOCAB_FILE,"w",encoding="utf-8") as f:
            json.dump({},f)

    with open(VOCAB_FILE,encoding="utf-8") as f:
        vocab=json.load(f)

    vocab[data["english"].lower()] = {
        "telugu":data["telugu"],
        "hindi":data["hindi"]
    }

    with open(VOCAB_FILE,"w",encoding="utf-8") as f:
        json.dump(vocab,f,indent=2,ensure_ascii=False)

    return jsonify({"message":"Word added"})

# ---------- TRANSLATE ----------
@app.route("/translate", methods=["POST"])
def translate():
    data=request.get_json()
    return jsonify(translate_text(data["text"],data["language"]))

# ---------- SERVE PDF ----------
@app.route("/pdf/<filename>")
def serve_pdf(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
