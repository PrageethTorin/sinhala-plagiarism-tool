from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import time

# Add the modules path so we can import your engine and shared modules
sys.path.append(os.path.dirname(__file__))

# Import the updated plagiarism detection function
from modules.ParaphraseDetection.plagiarism_engine import check_internet_plagiarism

app = Flask(__name__)
CORS(app)  # Allows your React frontend (port 3000) to communicate with this API

print("\n--- 🔌 Sinhala Plagiarism Detection Server Starting ---")

@app.route('/api/check-internet', methods=['POST'])
def check_internet():
    """
    API endpoint for full-paragraph internet paraphrase detection.
    Processes all sentences, submits tokens to discovery, and calculates Equation 7 scores.
    """
    start_time = time.time()
    data = request.json
    student_text = data.get('studentText', '')
    
    if not student_text:
        return jsonify({"error": "Student text is required"}), 400

    print(f"\n📥 [API] Received Request: {len(student_text)} characters.")
    print(f"📄 Text Preview: {student_text[:100]}...")

    try:
        # Step: Discovery -> Scrape -> Sentence-wise Paraphrase Detection
        # This now uses the Multi-Sentence Token Logic
        print("🔍 Starting Multi-Sentence Discovery Layer...")
        results = check_internet_plagiarism(student_text)
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        print(f"✅ Analysis Complete in {duration} seconds.")
        print(f"📤 Sending {len(results)} source reports to Frontend.")
        
        return jsonify(results)

    except Exception as e:
        print(f"❌ Critical Server Error: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    # Running on port 5000 as per your Paraphrase.js fetch configuration
    print("🚀 API is active at http://localhost:5000/api/check-internet")
    app.run(debug=True, port=5000, threaded=True)