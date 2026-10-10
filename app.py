"""FastAPI browser UI for CareBridge. Run: uvicorn app:app --reload"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from carebridge.rag import answer
from carebridge.corpus import demo_documents

app = FastAPI(title="CareBridge", version="0.1.0",description="Citation-grounded vaccine information demo")
ROOT = Path(__file__).parent

class ChatInput(BaseModel):
    question: str = Field(min_length=1,max_length=2000)
    mode: str = "hybrid"
    history: list[dict] = Field(default_factory=list,max_length=4)

@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/healthz")
def healthz():
    return {"status":"ok","mode": "demo" if not os.getenv("CAREBRIDGE_CORPUS") else "custom_corpus","demo_chunks":len(demo_documents())}

@app.post("/api/chat")
def chat(payload: ChatInput):
    return answer(payload.question,payload.mode if payload.mode in {"bm25","dense","hybrid"} else "hybrid",
                  os.getenv("CAREBRIDGE_CORPUS",""),os.getenv("CAREBRIDGE_RERANK","off")=="cross-encoder",
                  payload.history)
