"""Builds the configured vector store backend (numpy or dart-db-server)."""

from . import config


def make_store():
    if config.VECTOR_BACKEND == "dartdb":
        from .dartdb_store import DartDbVectorStore

        return DartDbVectorStore(
            config.EMBED_MODEL,
            config.DARTDB_HOST,
            config.DARTDB_PORT,
            config.DARTDB_TABLE,
            config.DARTDB_INDEX_KIND,
        )

    from .store import VectorStore

    return VectorStore(config.DATA_DIR, config.EMBED_MODEL)
