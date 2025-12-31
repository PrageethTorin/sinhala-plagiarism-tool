from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from modules.WSA import WSAAnalyzer

# Initialize FastAPI app
app = FastAPI(title="Sinhala Plagiarism & Writing Style Analysis API")

# Initialize your custom research engine
# This will load your vectorizer.pkl and tfidf_matrix.pkl upon startup
wsa_tool = WSAAnalyzer()

class AnalysisRequest(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"message": "Sinhala Plagiarism Detection API is running"}

@app.post("/api/check-wsa")
async def check_wsa(request: AnalysisRequest):
    """
    Endpoint for Writing Style Analysis using Hybrid Scoring.
    Detects anomalies based on Sentence Length and Lexical Richness (TTR).
    """
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text input is empty. Please provide a paragraph.")

    try:
        # 1. Execute the Hybrid Analysis from the engine
        result = wsa_tool.check_text(request.text)
        
        # Extract the ratio_data dictionary calculated in wsa_engine.py
        r_info = result["ratio_data"]
        
        # 2. Return the full statistical breakdown for the research component
        return {
            "external_plagiarism": result["similarity_score"],
            "style_change_ratio": r_info["style_change_ratio"],
            "flagged_count": r_info["flagged_count"],
            "total_count": r_info["total_count"],
            "sentence_map": r_info["details"],  # This contains ID, Length, TTR, and Reason
            "verdict": "Suspicious" if r_info["style_change_ratio"] > 15 else "Clean"
        }

    except KeyError as ke:
        print(f"❌ Key Error in Main: {ke}")
        raise HTTPException(status_code=500, detail=f"Data mapping error: {str(ke)}")
    except Exception as e:
        print(f"❌ API Backend Crash: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# To run this: uvicorn main:app --reload