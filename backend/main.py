from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

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
        # Await the async engine results
        results = await analyzer.check_text(request.text)
        return results['ratio_data']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)