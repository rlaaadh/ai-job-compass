from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import company, comparison

app = FastAPI(
    title="이직각",
    description="국민연금 데이터 기반 기업 건강도 & 이직 추천도 API",
    version="0.1.0",
)

# CORS — MVP: 모든 origin 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(company.router)
app.include_router(comparison.router)


@app.get("/")
async def root():
    return {"message": "이직각 API", "docs": "/docs"}
