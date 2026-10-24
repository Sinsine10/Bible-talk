from __future__ import annotations

import json

from biblerag.config import PEOPLE_PATH


def load_people() -> list[dict]:
    return json.loads(PEOPLE_PATH.read_text(encoding="utf-8"))


def person_chunks(people: list[dict] | None = None) -> list[dict]:
    people = people or load_people()
    chunks: list[dict] = []
    for person in people:
        aliases = ", ".join(person.get("aliases", []))
        events = " ".join(f"- {event}" for event in person.get("events", []))
        related = ", ".join(person.get("related", []))
        verses = ", ".join(person.get("verses", []))
        text = (
            f"Biblical person: {person['name']}. "
            f"Also known as: {aliases or person['name']}. "
            f"Testament: {person.get('testament', '')}. "
            f"Role: {person.get('role', '')}. "
            f"Summary: {person['summary']} "
            f"Key events: {events} "
            f"Related people: {related}. "
            f"Key passages: {verses}."
        )
        chunks.append(
            {
                "id": f"person:{person['id']}",
                "text": text,
                "metadata": {
                    "source": "person",
                    "translation": "",
                    "book": "",
                    "chapter": 0,
                    "verse_start": 0,
                    "verse_end": 0,
                    "ref": verses,
                    "testament": person.get("testament", ""),
                    "name": person["name"],
                },
            }
        )
    return chunks


def find_people(query: str, people: list[dict] | None = None) -> list[dict]:
    people = people or load_people()
    needle = query.strip().lower()
    hits = []
    for person in people:
        names = [person["name"], person["id"], *person.get("aliases", [])]
        if any(needle == name.lower() or needle in name.lower() for name in names):
            hits.append(person)
    return hits
