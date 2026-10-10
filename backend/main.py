"""
backend/main.py — FastAPI Application Entrypoint for ZipForge.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.compress import router as compress_router
from api.decompress import router as decompress_router
from api.image import router as image_router
from api.benchmark import router as benchmark_router
from api.inspect import router as inspect_router
from api.download import router as download_router
from algorithms.registry import get_registry

app = FastAPI(
    title="ZipForge API",
    description="Adaptive Multi-Engine File Compressor & Image Optimizer API",
    version="2.0.0",
)

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(compress_router)
app.include_router(decompress_router)
app.include_router(image_router)
app.include_router(benchmark_router)
app.include_router(inspect_router)
app.include_router(download_router)


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "app": "ZipForge",
        "version": "2.0.0",
        "engine": "FastAPI + Multi-Engine Compression",
    }


@app.get("/api/algorithms")
async def list_algorithms():
    registry = get_registry()
    algos = [
        {
            "id": "AUTO",
            "name": "Auto-Best",
            "tag": "AUTO",
            "description": "Evaluates all engines and selects maximum reduction.",
            "is_default": True,
        },
        {
            "id": "HUFFMAN",
            "name": "Huffman Coding",
            "tag": "HUF",
            "description": "Optimal binary prefix tree based on symbol frequencies.",
            "best_for": "Text files, source code, structured JSON/XML",
        },
        {
            "id": "LZW",
            "name": "Lempel-Ziv-Welch (LZW)",
            "tag": "LZW",
            "description": "Dynamic dictionary-based sliding phrase encoder (9–16 bits).",
            "best_for": "Repetitive patterns, log files, multi-word phrases",
        },
        {
            "id": "RLE",
            "name": "Run-Length Encoding (RLE)",
            "tag": "RLE",
            "description": "Escapes consecutive sequences of identical bytes.",
            "best_for": "Bitmap graphics, padded binary streams, sparse data",
        },
        {
            "id": "STORE",
            "name": "STORE (Uncompressed)",
            "tag": "STORE",
            "description": "Verbatim storage with SHA-256 cryptographic verification.",
            "best_for": "Already-compressed media (JPEG, MP4, existing ZIPs)",
        },
    ]
    return {"algorithms": algos}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
