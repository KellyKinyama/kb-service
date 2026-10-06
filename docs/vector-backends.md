# Vector Store Backends

The knowledge base can store and search embeddings through two interchangeable
backends, selected at runtime by `KB_VECTOR_BACKEND`. Both expose the same
interface (`add`, `remove_source`, `search`, `count`, `sources`), so ingestion
and query code — and the HTTP API — are identical regardless of backend.

Embeddings are **always computed locally** with the sentence-transformers model
(`all-MiniLM-L6-v2`, 384-dim). The backend only decides where vectors are stored
and how k-NN search runs.

| Backend  | Storage                         | Index      | External process | Best for                       |
| -------- | ------------------------------- | ---------- | ---------------- | ------------------------------ |
| `numpy`  | `vectors.npy` + `meta.json`     | flat cosine| none             | Default; up to ~100k chunks    |
| `dartdb` | dart-db-server (`VECTOR` column)| HNSW/IVF…  | dart-db-server   | Larger corpora, hybrid search  |

## numpy (default)

A single-node numpy cosine index persisted to disk under `KB_DATA_DIR`
(`./kb_data`). Zero external dependencies — the service is fully self-contained.
Exact (100% recall) search by brute-force cosine. Ideal for the current corpus
size.

Nothing to run; it is the default (`KB_VECTOR_BACKEND=numpy`).

## dartdb (dart-db-server)

Stores vectors in [dart-db-server](https://github.com/KellyKinyama/dart-db-server),
a pure-Dart SQL database with a built-in vector engine. The Python service talks
to it over its TCP JSON-line protocol and keeps the vectors in a SQL `VECTOR`
column with an approximate-nearest-neighbour index.

### Why use it

- **HNSW index** — sub-linear k-NN that scales to ~1M vectors per node.
- **Payload-filter pruning** — `filter_cols='source'` lets the engine intersect
  candidate rows by metadata *before* scanning vectors (fast per-source or
  per-tenant queries).
- **Hybrid search** — `vec_hybrid_search` fuses vector distance with BM25
  keyword rank (Reciprocal Rank Fusion), which usually beats either signal
  alone for RAG. Not yet wired into the service, but available.
- **Range search, batch search, k-NN joins** — additional retrieval modes if
  needed later.
- **Operational control** — PRAGMAs to verify, rebuild, warm, and inspect the
  index.

### Running the server

```powershell
cd C:\projects\ai_projects\dart-db-server
dart pub get
dart run bin/dart_db_server.dart --port 4555 --file kb_vectors.json
```

The `--file` argument is the JSON persistence file; vectors survive restarts.

### Pointing the service at it

In `kb-service/.env`:

```ini
KB_VECTOR_BACKEND=dartdb
KB_DARTDB_HOST=127.0.0.1
KB_DARTDB_PORT=4555
KB_DARTDB_TABLE=chunks
KB_DARTDB_INDEX_KIND=hnsw
```

Then ingest as usual (`ingest_cli.py` or the Ingest tab). The service creates
the table automatically:

```sql
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  path TEXT,
  chunk_index INTEGER,
  chunk_text TEXT NOT NULL,
  embedding BLOB VECTOR(
    dim=384, kind=hnsw, metric=cosine,
    m=16, ef_construction=64, filter_cols='source'
  )
);
```

### How the integration works

`app/dartdb_store.py` holds a persistent TCP socket (with a lock for
thread-safety and one automatic reconnect) and sends `{"id", "sql"}` JSON lines.

- **Insert** — chunks are embedded locally, then written with
  `INSERT … VALUES (…, VEC('[f,f,…]'))`. The protocol has no bound parameters,
  so numeric vectors are inlined and text is single-quote-escaped. Rows are
  batched (50 per statement).
- **Search** — the query vector is embedded, then:

  ```sql
  SELECT c.chunk_text, c.source, c.path, c.chunk_index, s.distance
  FROM vec_search('chunks', 'embedding', VEC('[…]'), 5) AS s
  JOIN chunks c ON c.id = s.rowid
  ORDER BY s.distance;
  ```

  Cosine distance is converted to a similarity score (`1 - distance`) so results
  match the numpy backend's scale.
- **Replace / delete** — `remove_source(source)` runs
  `DELETE FROM chunks WHERE source = …`; the index stays incrementally
  consistent (HNSW tombstones auto-rebuild past a 30% ratio).

### Operations (run via a dart-db client)

```sql
PRAGMA vector_index_stats('chunks.embedding');   -- kind, n, live, tombstones, bytes
PRAGMA vector_verify('chunks.embedding');        -- consistency vs rows
PRAGMA vector_analyze('chunks.embedding');       -- top-k recall via random probes
PRAGMA vector_index_rebuild('chunks.embedding'); -- clean rebuild
```

### Choosing an index kind

- `flat` — exact, 100% recall, no build cost (< ~100k rows).
- `hnsw` — default; best recall/latency for ~100k–1M rows.
- `ivfpq` — for > 1M rows, combine with `filter_cols` to prune first.

Set via `KB_DARTDB_INDEX_KIND`.

## Switching backends

The two backends do not share storage. After switching `KB_VECTOR_BACKEND`,
re-ingest your documents so the new backend is populated. Verify the active
backend at any time:

```
GET /health  →  { …, "vector_backend": "dartdb" }
```
