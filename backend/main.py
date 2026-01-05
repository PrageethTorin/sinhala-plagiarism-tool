from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # NEW: Required for React connectivity
from pydantic import BaseModel
import sys
import os

# Link the WSA module correctly
base_dir = os.path.dirname(os.path.abspath(__file__))
wsa_path = os.path.join(base_dir, "modules", "WSA")
if wsa_path not in sys.path:
    sys.path.append(wsa_path)

from wsa_engine import WSAAnalyzer

# Initialize FastAPI and the Writing Style Analyzer
app = FastAPI()
analyzer = WSAAnalyzer()

# --- NEW: CORS MIDDLEWARE CONFIGURATION ---
# This allows your React app (on port 3000) to talk to this API (on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, OPTIONS, GET, etc.
    allow_headers=["*"],  # Allows all headers
)

class TextRequest(BaseModel):
    text: str

@app.post("/api/check-wsa")
async def check_style(request: TextRequest):
    try:
        # 1. Ensure the text is not empty
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Input text is empty")

        # 2. Await the results from the analyzer engine
        results = await analyzer.check_text(request.text)
        
        # 3. Extract the processed research data
        data = results.get('ratio_data', {})
        
        return {
            "style_change_ratio": data.get('style_change_ratio', 0),
            "matched_url": data.get('matched_url', "No source found"),
            "similarity_score": data.get('similarity_score', 0),
            "sentence_map": data.get('sentence_map', [])
        }
    except Exception as e:
        # Log the error on the server side for debugging
        print(f"📡 SERVER ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Port 8000 must match the URL used in your React 'fetch' call
    uvicorn.run(app, host="127.0.0.1", port=8000)