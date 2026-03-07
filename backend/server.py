# backend/server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import asyncio

# Add the modules path so we can import engines
sys.path.append(os.path.dirname(__file__))

# --- IMPORTS FROM YOUR ENGINE ---
from modules.ParaphraseDetection.plagiarism_engine import check_paraphrase, check_internet_plagiarism

app = Flask(__name__)

# Combine CORS settings: Allows React (Port 3000)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

print("--- 🔌 Server Starting ---")

# --- INITIALIZE WSA ANALYZER (From Friend's Code) ---
try:
    from modules.WSA.wsa_engine import WSAAnalyzer
    analyzer = WSAAnalyzer()
    print("✅ WSA Engine initialized successfully")
except Exception as e:
    print(f"⚠️ WSA Engine initialization failed: {e}")
    analyzer = None

# --- 1. HEALTH CHECK (From Friend's Code) ---
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "wsa_engine": "available" if analyzer else "unavailable",
        "paraphrase_engine": "available" 
    }), 200

# --- 2. ROUTE FOR TWO-TEXT COMPARISON (Your Code) ---
@app.route('/api/check-paraphrase', methods=['POST'])
def check():
    data = request.json
    source_text = data.get('sourceText', '')
    suspicious_text = data.get('suspiciousText', '')
    
    if not source_text or not suspicious_text:
        return jsonify({"error": "Both text fields are required"}), 400

    try:
        print(f"📥 Paraphrase Request: Source ({len(source_text)} chars) vs Suspicious ({len(suspicious_text)} chars)")
        result = check_paraphrase(source_text, suspicious_text)
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- 3. ROUTE FOR INTERNET SEARCH (Your Code) ---
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

# --- 4. WRITING STYLE ANALYSIS (From Friend's Code) ---
@app.route('/api/check-wsa', methods=['POST'])
def check_wsa():
    """Writing Style Analysis endpoint"""
    if not analyzer:
        return jsonify({"error": "WSA Engine not available"}), 503
    
    try:
        data = request.json
        input_text = data.get('text', '')
        
        if not input_text:
            return jsonify({"error": "Text field is required"}), 400
        
        print(f"📥 WSA Request: {len(input_text)} chars")
        
        # Run async analyzer in sync context
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(analyzer.check_text(input_text))
        loop.close()
        
        print("✅ WSA Analysis Complete")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Error in WSA: {e}")
        return jsonify({"error": str(e)}), 500

# --- SERVER STARTUP INFO ---
print("\n📡 Available Endpoints:")
print("   • POST /api/check-paraphrase - Compare two texts")
print("   • POST /api/check-internet   - Scan the web")
print("   • POST /api/check-wsa        - Writing Style Analysis")
print("   • GET  /api/health           - Server Status Check")
print("")

if __name__ == '__main__':
    print("🚀 Unified Backend API is running on http://localhost:5000")
    # Added threaded=True to handle multiple requests better
    app.run(debug=True, port=5000, threaded=True)