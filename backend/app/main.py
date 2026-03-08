from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.plagiarism import router as plagiarism_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plagiarism_router, prefix="/api/plagiarism")

@app.get("/")
def root():
    return {"status": "Backend running"}
