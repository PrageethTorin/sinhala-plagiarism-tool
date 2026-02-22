# backend/server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add the modules path so we can import your engine
sys.path.append(os.path.dirname(__file__))
from modules.ParaphraseDetection.plagiarism_engine import check_paraphrase, check_internet_plagiarism

app = Flask(__name__)

# IMPORTANT: This must allow the origin of your React app
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

print("--- 🔌 Server Starting ---")

# --- 1. ROUTE FOR TWO-TEXT COMPARISON ---
@app.route('/api/check-paraphrase', methods=['POST'])
def check():
    data = request.json
    source_text = data.get('sourceText', '')
    suspicious_text = data.get('suspiciousText', '')
    
    if not source_text or not suspicious_text:
        return jsonify({"error": "Both text fields are required"}), 400

    try:
        result = check_paraphrase(source_text, suspicious_text)
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- 2. ROUTE FOR INTERNET SEARCH (THIS WAS MISSING) ---
@app.route('/api/check-internet', methods=['POST'])
def check_internet():
    data = request.json
    student_text = data.get('studentText', '')
    
    if not student_text:
        return jsonify({"error": "Student text is required"}), 400

    print(f"📡 Received Internet Scan Request ({len(student_text)} chars)")

    try:
        # Calls the function in plagiarism_engine.py
        result = check_internet_plagiarism(student_text)
        print("✅ Internet Analysis Complete.")
        return jsonify(result)
    except Exception as e:
        print(f"❌ Internet Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Paraphrase Detection API is running on http://localhost:5000")
    app.run(debug=True, port=5000)