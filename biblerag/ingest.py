from __future__ import annotations

from biblerag.bible import verse_chunks
from biblerag.people import person_chunks
from biblerag.store import client, collection, settings


def ingest(batch_size: int = 200) -> dict:
    print("loading people and KJV verses...", flush=True)
    people = person_chunks()
    verses = verse_chunks()
    docs = people + verses
    print(f"embedding {len(docs)} chunks ({len(people)} people, {len(verses)} verses)", flush=True)

    store = collection()
    if store.count():
        client().delete_collection(settings.collection_name)
        store = collection()

    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        store.add(
            ids=[item["id"] for item in batch],
            documents=[item["text"] for item in batch],
            metadatas=[item["metadata"] for item in batch],
        )
        print(f"indexed {min(i + batch_size, len(docs))}/{len(docs)}", flush=True)
    stats = {"chunks": store.count(), "people": len(people), "verses": len(verses)}
    print(stats, flush=True)
    return stats


def main() -> None:
    stats = ingest()
    print(stats)


if __name__ == "__main__":
    main()
