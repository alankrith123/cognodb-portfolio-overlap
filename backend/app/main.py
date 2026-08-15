import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import close_driver
from .queries import DatabaseUnavailable, fetch_exposure, fetch_funds


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    close_driver()


app = FastAPI(title="Portfolio Overlap", lifespan=lifespan)

_LOCAL_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
_EXTRA_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_LOCAL_ORIGINS + _EXTRA_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


class ExposureRequest(BaseModel):
    fund_names: list[str] = Field(min_length=2)


@app.get("/api/funds")
def get_funds():
    try:
        return {"funds": fetch_funds()}
    except DatabaseUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Can't reach the database right now.",
        )


@app.post("/api/exposure")
def post_exposure(body: ExposureRequest):
    try:
        return fetch_exposure(body.fund_names)
    except DatabaseUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Can't reach the database right now.",
        )
