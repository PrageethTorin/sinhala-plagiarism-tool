# backend/server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import asyncio

# Add the modules path so we can import your engine
sys.path.append(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)  # This allows React (Port 3000) to talk to Flask (Port 5000)

print("--- 🔌 Server Starting ---")

# Initialize WSA Analyzer
try:
    from modules.WSA.wsa_engine import WSAAnalyzer
    analyzer = WSAAnalyzer()
    print("✅ WSA Engine initialized successfully")
except Exception as e:
    print(f"⚠️ WSA Engine initialization failed: {e}")
    analyzer = None

# Optional: Try to import Paraphrase Detection
try:
    from modules.ParaphraseDetection.plagiarism_engine import check_paraphrase
    paraphrase_available = True
    print("✅ Paraphrase Detection Engine loaded")
except:
    paraphrase_available = False
    print("⚠️ Paraphrase Detection Engine not available (module not found)")

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "wsa_engine": "available" if analyzer else "unavailable",
        "paraphrase_engine": "available" if paraphrase_available else "unavailable"
    }), 200

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

@app.route('/api/check-paraphrase', methods=['POST'])
def check_paraphrase_route():
    """Paraphrase Detection endpoint"""
    if not paraphrase_available:
        return jsonify({"error": "Paraphrase Detection Engine not available"}), 503
    
    try:
        data = request.json
        source_text = data.get('sourceText', '')
        suspicious_text = data.get('suspiciousText', '')
        
        if not source_text or not suspicious_text:
            return jsonify({"error": "Both sourceText and suspiciousText are required"}), 400
        
        print(f"📥 Paraphrase Request: Source ({len(source_text)} chars) vs Suspicious ({len(suspicious_text)} chars)")
        
        result = check_paraphrase(source_text, suspicious_text)
        print("✅ Paraphrase Analysis Complete")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Error in Paraphrase: {e}")
        return jsonify({"error": str(e)}), 500

print("\n📡 Available Endpoints:")
print("   • POST /api/check-wsa      - Writing Style Analysis (ACTIVE)")
print("   • POST /api/check-paraphrase - Paraphrase Detection ({})")
print("   • GET /api/health          - Health Check")
print("")

if __name__ == '__main__':
    print("🚀 Backend API is running on http://localhost:5000")
    app.run(debug=True, port=5000, threaded=True) 