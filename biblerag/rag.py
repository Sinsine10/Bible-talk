from __future__ import annotations

from openai import OpenAI

from biblerag.config import settings
from biblerag.people import find_people, load_people
from biblerag.store import collection

SYSTEM_PROMPT = """You help people recall biblical figures and their stories.
Use only the provided context. Prefer the person profile for identity, then
support it with KJV verses. If names collide (several Johns, Marys, Jameses,
Josephs, Herods), disambiguate. Quote or paraphrase with book-chapter-verse
citations. If the context is not enough, say so. Do not invent episodes."""


def retrieve(question: str, top_k: int = 8) -> list[dict]:
    store = collection()
    if store.count() == 0:
        raise RuntimeError("Index is empty. Run: python -m biblerag.ingest")

    n_person = max(2, top_k // 3)
    n_verse = max(4, top_k - n_person)
    hits: list[dict] = []

    person_q = store.query(
        query_texts=[question],
        n_results=min(n_person, store.count()),
        where={"source": "person"},
    )
    verse_q = store.query(
        query_texts=[question],
        n_results=min(n_verse, store.count()),
        where={"source": "bible"},
    )
    hits.extend(_rows(person_q))
    hits.extend(_rows(verse_q))

    # Exact alias lookup so "Cephas" or "Saul of Tarsus" still resolve.
    for person in find_people(question):
        if not any(h.get("name") == person["name"] and h["source"] == "person" for h in hits):
            hits.insert(
                0,
                {
                    "text": person["summary"],
                    "source": "person",
                    "name": person["name"],
                    "ref": ", ".join(person.get("verses", [])),
                    "book": "",
                    "testament": person.get("testament", ""),
                    "distance": 0.0,
                },
            )
    return hits[: top_k + 2]


def _rows(result: dict) -> list[dict]:
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    dists = (result.get("distances") or [[]])[0]
    rows = []
    for text, meta, dist in zip(docs, metas, dists):
        rows.append(
            {
                "text": text,
                "source": meta.get("source", ""),
                "name": meta.get("name", ""),
                "ref": meta.get("ref", ""),
                "book": meta.get("book", ""),
                "testament": meta.get("testament", ""),
                "distance": dist,
            }
        )
    return rows


def generate(question: str, passages: list[dict]) -> str | None:
    if not settings.openai_api_key and not settings.openai_base_url:
        return None
    kwargs = {"api_key": settings.openai_api_key or "ollama"}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    client = OpenAI(**kwargs)
    context = "\n\n".join(
        f"[{p['source']}] {p.get('ref') or p.get('name')}\n{p['text']}" for p in passages
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nContext:\n{context}",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()


def ask(question: str, top_k: int = 8) -> dict:
    passages = retrieve(question, top_k=top_k)
    answer = generate(question, passages)
    if answer is None:
        answer = _extractive_answer(question, passages)
        mode = "extractive"
    else:
        mode = "generated"
    return {
        "question": question,
        "answer": answer,
        "mode": mode,
        "passages": passages,
    }


def _extractive_answer(question: str, passages: list[dict]) -> str:
    people = [p for p in passages if p["source"] == "person"]
    verses = [p for p in passages if p["source"] == "bible"]
    parts = []
    if people:
        parts.append(people[0]["text"])
    if verses:
        parts.append("Supporting passages:")
        for verse in verses[:5]:
            parts.append(f"- {verse['ref']}: {verse['text']}")
    if not parts:
        return "No matching Bible passages or people were found."
    return "\n".join(parts)


def person_card(name: str) -> dict | None:
    matches = find_people(name, load_people())
    if not matches:
        return None
    person = matches[0]
    related = retrieve(f"{person['name']} {person['summary'][:180]}", top_k=6)
    return {"person": person, "passages": [p for p in related if p["source"] == "bible"]}
