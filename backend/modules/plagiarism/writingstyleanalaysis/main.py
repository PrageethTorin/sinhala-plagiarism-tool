from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

from backend.modules.plagiarism.writingstyleanalaysis.modules.web_scraper import (

    get_internet_resources,
    scrape_many,
)

base_dir = os.path.dirname(os.path.abspath(__file__))
wsa_path = os.path.join(base_dir, "modules", "WSA")
if wsa_path not in sys.path:
    sys.path.append(wsa_path)

from wsa_engine import WSAAnalyzer

app = FastAPI()
analyzer = WSAAnalyzer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StyleCompareRequest(BaseModel):
    sourceText: str
    studentText: str


@app.post("/api/check-wsa")
async def check_style(request: StyleCompareRequest):
    try:
        source_text = request.sourceText.strip()
        student_text = request.studentText.strip()

        if not source_text or not student_text:
            raise HTTPException(
                status_code=400,
                detail="Both sourceText and studentText are required"
            )

        results = await analyzer.compare_texts(source_text, student_text)
        data = results.get("ratio_data", {})

        urls = get_internet_resources(student_text, num_results=3)
        scraped = await scrape_many(urls)

        web_sources = []
        for item in scraped:
            if item.get("text_len", 0) > 80:
                web_sources.append({
                    "url": item["url"],
                    "text_len": item["text_len"],
                    "preview": item["text"][:200] if item.get("text") else ""
                })

        matched_url = data.get("matched_url", "No source found")
        if (not matched_url or matched_url == "No source found") and web_sources:
            matched_url = web_sources[0]["url"]

        return {
            "style_change_ratio": data.get("style_change_ratio", 0),
            "matched_url": matched_url,
            "similarity_score": data.get("similarity_score", 0),
            "sentence_map": data.get("sentence_map", []),
            "web_sources": web_sources,
            "ratio_data": data,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"SERVER ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
