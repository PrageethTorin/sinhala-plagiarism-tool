from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from modules.WSA import WSAAnalyzer

app = FastAPI()
wsa_tool = WSAAnalyzer()

class AnalysisRequest(BaseModel):
    text: str

@app.post("/api/check-wsa")
async def check_wsa(request: AnalysisRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Empty text input")
    try:
        # Get result from engine
        result = wsa_tool.check_text(request.text)
        r_data = result["ratio_data"]
        
        # Return dynamic values (No hardcoding)
        return {
            "external_plagiarism": result["similarity_score"],
            "style_change_ratio": r_data["style_change_ratio"],
            "flagged_count": r_data["flagged_count"],
            "total_count": r_data["total_count"],
            "sentence_data": r_data["details"],
            "verdict": "Suspicious" if r_data["style_change_ratio"] > 15 else "Clean"
        }
    except Exception as e:
        print(f"❌ Backend Crash: {e}")
        raise HTTPException(status_code=500, detail=str(e))