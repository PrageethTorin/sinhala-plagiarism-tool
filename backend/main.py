from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Link the WSA module correctly
base_dir = os.path.dirname(os.path.abspath(__file__))
wsa_path = os.path.join(base_dir, "modules", "WSA")
if wsa_path not in sys.path:
    sys.path.append(wsa_path)

from wsa_engine import WSAAnalyzer

app = FastAPI()
analyzer = WSAAnalyzer()

# CORS configuration to allow React communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.post("/api/check-wsa")
async def check_style(request: TextRequest):
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Input text is empty")

        # Results must be awaited to resolve the coroutine
        results = await analyzer.check_text(request.text)
        data = results.get('ratio_data', {})
        
        return {
            "style_change_ratio": data.get('style_change_ratio', 0),
            "matched_url": data.get('matched_url', "No source found"),
            "similarity_score": data.get('similarity_score', 0),
            "sentence_map": data.get('sentence_map', [])
        }
    except Exception as e:
        print(f"📡 SERVER ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)