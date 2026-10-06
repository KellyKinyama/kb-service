"""Vector store backed by dart-db-server over its JSON line protocol.

Embeddings are computed locally (sentence-transformers); dart-db-server holds
the vectors and runs k-NN search via its built-in vector index. Exposes the
same surface as :class:`app.store.VectorStore` so the two are interchangeable.
"""

import json
import socket
import threading

from sentence_transformers import SentenceTransformer


def _sql_str(value: str) -> str:
    """Quotes a string literal for inline SQL (vectors are numeric, so safe)."""
    return "'" + value.replace("'", "''") + "'"


class DartDbVectorStore:
    """Talks to a running dart-db-server instance over TCP (JSON per line)."""

    def __init__(
        self,
        embed_model: str,
        host: str,
        port: int,
        table: str = "chunks",
        index_kind: str = "hnsw",
    ):
        self.model = SentenceTransformer(embed_model)
        self.dim = self.model.get_sentence_embedding_dimension()
        self._host = host
        self._port = port
        self._table = table
        self._index_kind = index_kind
        self._lock = threading.Lock()
        self._sock: socket.socket | None = None
        self._reader = None
        self._req_id = 0
        self._ensure_schema()

    # --- connection handling -------------------------------------------------

    def _connect(self) -> None:
        self._sock = socket.create_connection((self._host, self._port), timeout=30)
        self._reader = self._sock.makefile("r", encoding="utf-8", newline="\n")

    def _exec(self, sql: str) -> dict:
        """Sends one SQL request and returns the decoded response object."""
        with self._lock:
            for attempt in range(2):
                try:
                    if self._sock is None:
                        self._connect()
                    self._req_id += 1
                    payload = json.dumps({"id": self._req_id, "sql": sql}) + "\n"
                    self._sock.sendall(payload.encode("utf-8"))
                    line = self._reader.readline()
                    if not line:
                        raise ConnectionError("connection closed by server")
                    resp = json.loads(line)
                    if not resp.get("ok", False):
                        raise RuntimeError(f"dart-db error: {resp.get('error')}")
                    return resp
                except (OSError, ConnectionError) as exc:
                    self._close()
                    if attempt == 1:
                        raise RuntimeError(
                            f"dart-db-server unreachable at {self._host}:{self._port}: {exc}"
                        ) from exc
            raise RuntimeError("unreachable")

    def _close(self) -> None:
        try:
            if self._reader is not None:
                self._reader.close()
            if self._sock is not None:
                self._sock.close()
        except OSError:
            pass
        finally:
            self._sock = None
            self._reader = None

    # --- schema --------------------------------------------------------------

    def _ensure_schema(self) -> None:
        ddl = (
            f"CREATE TABLE IF NOT EXISTS {self._table} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "source TEXT NOT NULL, "
            "path TEXT, "
            "chunk_index INTEGER, "
            "chunk_text TEXT NOT NULL, "
            "embedding BLOB VECTOR("
            f"dim={self.dim}, kind={self._index_kind}, metric=cosine, "
            "m=16, ef_construction=64, filter_cols='source'"
            ")"
            ")"
        )
        self._exec(ddl)

    # --- interface (mirrors VectorStore) -------------------------------------

    @property
    def count(self) -> int:
        resp = self._exec(f"SELECT COUNT(*) FROM {self._table}")
        rows = resp.get("rows") or [[0]]
        return int(rows[0][0])

    def sources(self) -> list[str]:
        resp = self._exec(f"SELECT DISTINCT source FROM {self._table} ORDER BY source")
        return [row[0] for row in (resp.get("rows") or [])]

    def add(self, items: list[dict]) -> int:
        if not items:
            return 0
        texts = [item["text"] for item in items]
        embeddings = self.model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        )
        values = []
        for item, vec in zip(items, embeddings):
            vec_json = "[" + ",".join(f"{float(x):.6g}" for x in vec) + "]"
            values.append(
                "("
                f"{_sql_str(item['source'])}, "
                f"{_sql_str(item.get('path', ''))}, "
                f"{int(item.get('chunk_index', 0))}, "
                f"{_sql_str(item['text'])}, "
                f"VEC({_sql_str(vec_json)})"
                ")"
            )
        # Insert in batches to keep each SQL line a reasonable size.
        batch = 50
        for start in range(0, len(values), batch):
            chunk = values[start : start + batch]
            sql = (
                f"INSERT INTO {self._table} "
                "(source, path, chunk_index, chunk_text, embedding) VALUES "
                + ", ".join(chunk)
            )
            self._exec(sql)
        return len(items)

    def remove_source(self, source: str) -> None:
        self._exec(f"DELETE FROM {self._table} WHERE source = {_sql_str(source)}")

    def search(self, query: str, top_k: int) -> list[dict]:
        vec = self.model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0]
        vec_json = "[" + ",".join(f"{float(x):.6g}" for x in vec) + "]"
        sql = (
            "SELECT c.chunk_text, c.source, c.path, c.chunk_index, s.distance "
            f"FROM vec_search({_sql_str(self._table)}, 'embedding', "
            f"VEC({_sql_str(vec_json)}), {int(top_k)}) AS s "
            f"JOIN {self._table} c ON c.id = s.rowid "
            "ORDER BY s.distance"
        )
        resp = self._exec(sql)
        results = []
        for row in resp.get("rows") or []:
            text, source, path, chunk_index, distance = row
            results.append(
                {
                    "source": source,
                    "path": path,
                    "chunk_index": chunk_index,
                    "text": text,
                    "score": 1.0 - float(distance),  # cosine distance -> similarity
                }
            )
        return results
