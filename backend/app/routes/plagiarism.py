from flask import Blueprint, request, jsonify
from app.models.plagiarism.predictor import predict_plagiarism_from_text

plagiarism_bp = Blueprint("plagiarism", __name__)

@plagiarism_bp.route("/check", methods=["POST"])
def check_plagiarism():
    # ✅ FILE VALIDATION
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # ✅ READ FILE CONTENT
    try:
        text = file.read().decode("utf-8")
    except Exception:
        return jsonify({"error": "Unable to read file"}), 400

    # ✅ RUN MODEL
    result = predict_plagiarism_from_text(text)

    return jsonify(result), 200
