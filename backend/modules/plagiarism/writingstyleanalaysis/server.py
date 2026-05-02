# backend/server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add the modules path so we can import your engine
sys.path.append(os.path.dirname(__file__))
from modules.ParaphraseDetection.plagiarism_engine import check_paraphrase

app = Flask(__name__)
CORS(app)  # This allows React (Port 3000) to talk to Flask (Port 5000)

print("--- 🔌 Server Starting ---")

@app.route('/api/check-paraphrase', methods=['POST'])
def check():
    data = request.json
    
    # Get the two texts from the frontend
    source_text = data.get('sourceText', '')
    suspicious_text = data.get('suspiciousText', '')
    
    # Basic validation
    if not source_text or not suspicious_text:
        return jsonify({"error": "Both text fields are required"}), 400

    print(f"📥 Received Request: Comparing Source ({len(source_text)} chars) vs Suspicious ({len(suspicious_text)} chars)")

    # Run your Hybrid Engine
    try:
        result = check_paraphrase(source_text, suspicious_text)
        print("✅ Analysis Complete. Sending results...")
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    print("🚀 Paraphrase Detection API is running on http://localhost:5000")
    app.run(debug=True, port=5000) 