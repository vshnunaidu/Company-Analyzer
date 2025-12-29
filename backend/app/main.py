import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api import company, analysis, chat

load_dotenv()

app = FastAPI(
    title="Company Auditor API",
    description="AI-powered public company auditor using SEC filings",
    version="1.0.0"
)

# Configure CORS - allow frontend origins from environment or defaults
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
cors_origins = [origin.strip() for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(company.router, prefix="/api/company", tags=["company"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/")
async def root():
    return {"message": "Company Auditor API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
