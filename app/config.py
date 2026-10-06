"""Configuration loaded from environment / .env."""

import os

from dotenv import load_dotenv

load_dotenv(override=True)

# Azure AI Foundry (chat model for grounded answers).
AZURE_AI_ENDPOINT = os.environ.get(
    "AZURE_AI_ENDPOINT", "https://aiml4good.services.ai.azure.com/openai/v1"
)
AZURE_AI_DEPLOYMENT = os.environ.get("AZURE_AI_DEPLOYMENT", "gpt-5.4")
AZURE_AI_KEY = os.environ.get("AZURE_AI_KEY") or os.environ.get("AZURE_SPEECH_KEY", "")

# Local embedding model (runs offline, no Azure deployment needed).
EMBED_MODEL = os.environ.get("KB_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Where the vector index and metadata are persisted.
DATA_DIR = os.environ.get("KB_DATA_DIR", "./kb_data")

CHUNK_SIZE = int(os.environ.get("KB_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("KB_CHUNK_OVERLAP", "150"))
TOP_K = int(os.environ.get("KB_TOP_K", "5"))

# Vector store backend: "numpy" (local file) or "dartdb" (dart-db-server).
VECTOR_BACKEND = os.environ.get("KB_VECTOR_BACKEND", "numpy").lower()
DARTDB_HOST = os.environ.get("KB_DARTDB_HOST", "127.0.0.1")
DARTDB_PORT = int(os.environ.get("KB_DARTDB_PORT", "4555"))
DARTDB_TABLE = os.environ.get("KB_DARTDB_TABLE", "chunks")
DARTDB_INDEX_KIND = os.environ.get("KB_DARTDB_INDEX_KIND", "hnsw")
