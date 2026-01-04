from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Link the WSA module
wsa_path = os.path.join(os.path.dirname(__file__), "modules", "WSA")
sys.path.append(wsa_path)

from wsa_engine import WSAAnalyzer
analyzer = WSAAnalyzer()
app = FastAPI()

class TextRequest(BaseModel):
    text: str

@app.post("/api/check-wsa")
async def check_style(request: TextRequest):
    try:
        # Await the async analyzer results
        results = await analyzer.check_text(request.text)
        return {
            "style_change_ratio": results['ratio_data']['style_change_ratio'],
            "matched_url": results['ratio_data'].get('matched_url'),
            "similarity_score": results['ratio_data'].get('similarity_score'),
            "sentence_map": results['ratio_data'].get('sentence_map')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)