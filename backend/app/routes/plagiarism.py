from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from app.models.plagiarism.predictor import predict_plagiarism_from_text

router = APIRouter()

@router.post("/check")
async def check_plagiarism(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    # ❌ No input provided
    if not text and not file:
        return {"error": "No text or file provided"}

    # ✅ If text is pasted
    if text and text.strip():
        content = text.strip()

    # ✅ If file is uploaded
    elif file:
        try:
            content = (await file.read()).decode("utf-8")
        except Exception:
            return {"error": "Unable to read file"}

    # ✅ Run prediction
    result = predict_plagiarism_from_text(content)
    return result
