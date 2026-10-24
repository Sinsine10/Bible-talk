from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import httpx

from biblerag.books import BOOKS, testament_for
from biblerag.config import BIBLE_PATH

BIBLE_URLS = [
    "https://cdn.jsdelivr.net/gh/thiagobodruk/bible@master/json/en_kjv.json",
    "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json",
]
WINDOW = 4
OVERLAP = 1


def download_bible(path: Path = BIBLE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 1000:
        return path
    errors: list[str] = []
    with httpx.Client(follow_redirects=True, timeout=180) as client:
        for url in BIBLE_URLS:
            try:
                response = client.get(url)
                response.raise_for_status()
                if len(response.content) < 1000:
                    raise ValueError("file too small")
                path.write_bytes(response.content)
                return path
            except Exception as exc:  # noqa: BLE001 — try the next mirror
                errors.append(f"{url}: {exc}")
    curl = shutil.which("curl")
    if curl:
        for url in BIBLE_URLS:
            try:
                subprocess.run(
                    [curl, "-L", "--retry", "5", "--max-time", "180", "-o", str(path), url],
                    check=True,
                )
                if path.exists() and path.stat().st_size > 1000:
                    return path
            except Exception as exc:  # noqa: BLE001
                errors.append(f"curl {url}: {exc}")
    raise RuntimeError("Could not download KJV JSON. Tried:\n" + "\n".join(errors))


def load_bible(path: Path = BIBLE_PATH) -> list[dict]:
    download_bible(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verse_chunks(bible: list[dict] | None = None) -> list[dict]:
    bible = bible or load_bible()
    chunks: list[dict] = []
    for book in bible:
        book_name = BOOKS.get(book["abbrev"], book.get("name") or book["abbrev"])
        testament = testament_for(book_name)
        for chapter_index, verses in enumerate(book["chapters"], start=1):
            n = len(verses)
            start = 0
            while start < n:
                end = min(start + WINDOW, n)
                texts = []
                for verse_index in range(start, end):
                    texts.append(f"{verse_index + 1} {verses[verse_index].strip()}")
                first_verse = start + 1
                last_verse = end
                ref = f"{book_name} {chapter_index}:{first_verse}"
                if last_verse != first_verse:
                    ref = f"{book_name} {chapter_index}:{first_verse}-{last_verse}"
                body = " ".join(texts)
                chunks.append(
                    {
                        "id": f"verse:{book_name}:{chapter_index}:{first_verse}-{last_verse}",
                        "text": f"{ref} (KJV). {body}",
                        "metadata": {
                            "source": "bible",
                            "translation": "KJV",
                            "book": book_name,
                            "chapter": chapter_index,
                            "verse_start": first_verse,
                            "verse_end": last_verse,
                            "ref": ref,
                            "testament": testament,
                            "name": "",
                        },
                    }
                )
                if end == n:
                    break
                start += WINDOW - OVERLAP
    return chunks
