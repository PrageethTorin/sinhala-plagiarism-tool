# backend/server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# 1. Setup paths BEFORE importing local modules
sys.path.append(os.path.dirname(__file__))

from modules.ParaphraseDetection.plagiarism_engine import check_paraphrase, check_internet_plagiarism
from modules.OCR.ocr_engine import extract_text_from_image

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

print("--- 🔌 Server Starting ---")

# --- ROUTE: TWO-TEXT COMPARISON ---
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
        return jsonify({"error": str(e)}), 500

# --- ROUTE: INTERNET SEARCH ---
@app.route('/api/check-internet', methods=['POST'])
def check_internet():
    data = request.json
    student_text = data.get('studentText', '')
    if not student_text:
        return jsonify({"error": "Student text is required"}), 400
    try:
        result = check_internet_plagiarism(student_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ROUTE: OCR EXTRACTION (MOVED UP) ---
@app.route('/api/ocr-extract', methods=['POST'])
def ocr_extract():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        file = request.files['image']
        image_bytes = file.read()
        
        text = extract_text_from_image(image_bytes)
        
        if not text:
            return jsonify({"error": "Could not read Sinhala text from this image."}), 400

        return jsonify({"extractedText": text})
    except Exception as e:
        print(f"❌ OCR Server Error: {e}")
        return jsonify({"error": "Internal Server Error: check Tesseract path"}), 500

# --- START SERVER (MUST BE AT THE VERY BOTTOM) ---
if __name__ == '__main__':
    print("🚀 Paraphrase Detection API is running on http://localhost:5000")
    app.run(debug=True, port=5000)