"""FastAPI knowledge-base service: ingest documents, search, and ask."""

import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import chunking, config, loaders, rag
from .store import VectorStore

app = FastAPI(title="ZESCO Knowledge Base")

# Allow the React dev server (and other browser clients) to call the API.
_origins = os.environ.get("KB_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = VectorStore(config.DATA_DIR, config.EMBED_MODEL)


class IngestPath(BaseModel):
    path: str


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None


def _ingest_file(path: str, source: str) -> int:
    text = loaders.load_file(path)
    chunks = chunking.chunk_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    items = [
        {"source": source, "path": path, "chunk_index": i, "text": chunk}
        for i, chunk in enumerate(chunks)
    ]
    store.remove_source(source)  # replace any previous version cleanly
    return store.add(items)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "documents": store.count,
        "sources": store.sources(),
        "embed_model": config.EMBED_MODEL,
    }


@app.post("/ingest/path")
def ingest_path(body: IngestPath):
    """Ingests a single file or every supported file under a folder."""
    if not os.path.exists(body.path):
        raise HTTPException(404, "Path not found")

    files = (
        [body.path]
        if os.path.isfile(body.path)
        else list(loaders.iter_files(body.path))
    )
    ingested = 0
    for file_path in files:
        try:
            ingested += _ingest_file(file_path, os.path.basename(file_path))
        except ValueError:
            continue
    return {"ingested_chunks": ingested, "documents": store.count}


@app.post("/ingest/upload")
async def ingest_upload(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        ingested = _ingest_file(tmp_path, file.filename)
    except ValueError:
        raise HTTPException(400, "Unsupported file type")
    finally:
        os.unlink(tmp_path)
    return {"ingested_chunks": ingested, "documents": store.count}


@app.post("/search")
def search(body: AskRequest):
    results = store.search(body.question, body.top_k or config.TOP_K)
    return {
        "results": [
            {"source": r["source"], "score": r["score"], "text": r["text"][:500]}
            for r in results
        ]
    }


@app.post("/ask")
def ask(body: AskRequest):
    passages = store.search(body.question, body.top_k or config.TOP_K)
    if not passages:
        return {"answer": "The knowledge base is empty. Ingest documents first.", "sources": []}
    return {
        "answer": rag.answer(body.question, passages),
        "sources": sorted({p["source"] for p in passages}),
        "passages": [{"source": p["source"], "score": p["score"]} for p in passages],
    }
