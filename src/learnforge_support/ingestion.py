from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from .models import DocumentChunk

ENTRY_HEADING = re.compile(
    r"^#\s+(?P<document_id>(?:FAQ|POLICY|TICKET)-\d+)\s+[\u2014-]\s+(?P<title>.+?)\s*$",
    re.MULTILINE,
)
DATE_PATTERNS = (
    re.compile(r"(?:Last reviewed|Last updated|Updated|Reviewed|Effective)\s*:\s*(?P<date>[^.\n]+)", re.I),
)
STALE_TERMS = re.compile(
    r"\b(?:older|outdated|archived|previous|obsolete|retired|removed|no longer)\b",
    re.I,
)
SUPPORTED_SOURCES = {"faqs.md", "policies.md", "tickets.md"}


def _document_type(document_id: str) -> str:
    return document_id.split("-", maxsplit=1)[0].lower()


def _stable_chunk_id(source: str, document_id: str, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{document_id.lower()}_{digest}"


def _metadata_date(text: str, pattern_index: int) -> str | None:
    if pattern_index >= len(DATE_PATTERNS):
        return None
    match = DATE_PATTERNS[pattern_index].search(text)
    return match.group("date").strip() if match else None


def parse_markdown(path: Path) -> list[DocumentChunk]:
    """Parse one corpus Markdown file into one searchable record per KB entry."""
    if path.name not in SUPPORTED_SOURCES:
        return []

    content = path.read_text(encoding="utf-8")
    headings = list(ENTRY_HEADING.finditer(content))
    chunks: list[DocumentChunk] = []

    for index, heading in enumerate(headings):
        body_start = heading.end()
        body_end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        body = content[body_start:body_end].strip(" -\n\r")
        if not body:
            continue

        document_id = heading.group("document_id")
        title = heading.group("title").strip()
        document_type = _document_type(document_id)
        last_updated = _metadata_date(body, 0)
        effective_date = _metadata_date(body, 0) if document_type == "policy" else None
        chunks.append(
            DocumentChunk(
                chunk_id=_stable_chunk_id(path.name, document_id, body),
                text=f"{title}\n\n{body}",
                source=path.name,
                document_type=document_type,
                document_id=document_id,
                title=title,
                chunk_index=0,
                last_updated=last_updated,
                effective_date=effective_date,
                contains_stale_reference=bool(STALE_TERMS.search(body)),
            )
        )

    return chunks


def load_corpus(data_dir: Path) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for source_name in sorted(SUPPORTED_SOURCES):
        source_path = data_dir / source_name
        if source_path.exists():
            chunks.extend(parse_markdown(source_path))
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Index LearnForge knowledge-base documents.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--chroma-path", type=Path, default=Path(".chroma"))
    args = parser.parse_args()
    from .config import Settings
    from .retrieval import KnowledgeBase

    settings = Settings(chroma_path=args.chroma_path)
    indexed_count = KnowledgeBase(settings).rebuild(args.data_dir)
    print(f"Indexed {indexed_count} knowledge-base entries from {args.data_dir}")


if __name__ == "__main__":
    main()
