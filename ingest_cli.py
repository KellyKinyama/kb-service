"""CLI to ingest a file or folder into the knowledge base index.

Usage:
    python ingest_cli.py <file-or-folder>
"""

import os
import sys

from app import chunking, config, loaders
from app.store_factory import make_store


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python ingest_cli.py <file-or-folder>")
        sys.exit(2)

    target = sys.argv[1]
    if not os.path.exists(target):
        sys.exit(f"Path not found: {target}")

    store = make_store()
    files = [target] if os.path.isfile(target) else list(loaders.iter_files(target))

    total = 0
    for file_path in files:
        try:
            text = loaders.load_file(file_path)
        except ValueError:
            continue
        chunks = chunking.chunk_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        source = os.path.basename(file_path)
        items = [
            {"source": source, "path": file_path, "chunk_index": i, "text": chunk}
            for i, chunk in enumerate(chunks)
        ]
        store.remove_source(source)
        count = store.add(items)
        total += count
        print(f"ingested {count} chunks from {file_path}")

    print(f"done. total chunks={total}, documents={store.count}")


if __name__ == "__main__":
    main()
