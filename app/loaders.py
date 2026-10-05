"""Document loaders for the knowledge base."""

import os

SUPPORTED = {".txt", ".md", ".pdf", ".docx"}


def load_file(path: str) -> str:
    """Extracts plain text from a supported document."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        with open(path, encoding="utf-8", errors="ignore") as handle:
            return handle.read()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if ext == ".docx":
        from docx import Document as DocxDocument

        document = DocxDocument(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    raise ValueError(f"Unsupported file type: {ext}")


def iter_files(root: str):
    """Yields paths of supported files under [root] (recursively)."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if os.path.splitext(name)[1].lower() in SUPPORTED:
                yield os.path.join(dirpath, name)
