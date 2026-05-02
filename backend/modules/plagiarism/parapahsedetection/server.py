# backend/server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add the modules path so we can import your engine
sys.path.append(os.path.dirname(__file__))

from modules.ParaphraseDetection.plagiarism_engine import (
    check_paraphrase,
    check_internet_plagiarism
)

app = Flask(__name__)

# Allow your React app (adjust if your frontend runs elsewhere)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

print("--- Server Starting ---")

# ✅ Root route so GET http://127.0.0.1:5000/ doesn't show 404
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "service": "Paraphrase Detection API",
        "routes": [
            "GET /health",
            "POST /api/check-paraphrase",
            "POST /api/check-internet"
        ]
    })

# ✅ Health route (useful for testing)
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

# --- 1) TWO-TEXT COMPARISON ---
@app.route("/api/check-paraphrase", methods=["POST"])
def check():
    data = request.get_json(silent=True) or {}

    source_text = data.get("sourceText", "")
    suspicious_text = data.get("suspiciousText", "")

    if not source_text or not suspicious_text:
        return jsonify({"error": "Both 'sourceText' and 'suspiciousText' are required"}), 400

    try:
        result = check_paraphrase(source_text, suspicious_text)
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error in /api/check-paraphrase: {e}")
        return jsonify({"error": str(e)}), 500

# --- 2) INTERNET SEARCH ---
@app.route("/api/check-internet", methods=["POST"])
def check_internet():
    data = request.get_json(silent=True) or {}

    student_text = data.get("studentText", "")

    if not student_text:
        return jsonify({"error": "Student text is required"}), 400

    print(f"[INTERNET] Received scan request ({len(student_text)} chars)")

    try:
        result = check_internet_plagiarism(student_text)
        print("[INTERNET] Analysis complete.")
        return jsonify(result), 200
    except Exception as e:
        print(f"[INTERNET] Error in /api/check-internet: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Paraphrase Detection API is running on http://127.0.0.1:5000")
    # ✅ disable reloader so model doesn't load twice
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)