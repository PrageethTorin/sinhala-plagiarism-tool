# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import ONLY your component router
from modules.semantic_similarity.routes import router as similarity_router

app = FastAPI(title="University Project API")

# Attach your component under /semantic
app.include_router(similarity_router, prefix="/semantic")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"status": "ok"}
