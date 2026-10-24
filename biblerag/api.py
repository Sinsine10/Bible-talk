from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from biblerag import __version__
from biblerag.config import ROOT, settings
from biblerag.people import load_people
from biblerag.rag import ask, person_card, retrieve
from biblerag.store import collection

app = FastAPI(
    title="Bible People RAG",
    version=__version__,
    description=(
        "Ask about biblical people and their stories. "
        "Answers are grounded in a people index plus the King James Bible (public domain)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, examples=["Who was Barnabas and what did he do with Paul?"])
    top_k: int = Field(default=8, ge=3, le=20)


class Passage(BaseModel):
    text: str
    source: str
    name: str = ""
    ref: str = ""
    book: str = ""
    testament: str = ""
    distance: float | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    mode: str
    passages: list[Passage]


def require_key(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = settings.biblerag_api_key
    if not expected:
        return
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


Auth = Annotated[None, Depends(require_key)]


@app.get("/")
def root() -> FileResponse:
    return FileResponse(ROOT / "biblerag" / "static" / "index.html")


@app.get("/health")
def health() -> dict:
    try:
        count = collection().count()
    except Exception:
        count = 0
    return {
        "ok": True,
        "version": __version__,
        "indexed_chunks": count,
        "people": len(load_people()),
        "generation": bool(settings.openai_api_key or settings.openai_base_url),
    }


@app.post("/v1/ask", response_model=AskResponse)
def ask_endpoint(body: AskRequest, _: Auth) -> dict:
    try:
        return ask(body.question, top_k=body.top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/v1/search", response_model=list[Passage])
def search_endpoint(
    _: Auth,
    q: str = Query(min_length=2),
    top_k: int = Query(default=8, ge=3, le=20),
) -> list[dict]:
    try:
        return retrieve(q, top_k=top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/v1/people")
def list_people(_: Auth, q: str | None = None) -> list[dict]:
    people = load_people()
    if q:
        needle = q.lower()
        people = [
            p
            for p in people
            if needle in p["name"].lower()
            or needle in p["id"]
            or any(needle in alias.lower() for alias in p.get("aliases", []))
        ]
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "aliases": p.get("aliases", []),
            "testament": p.get("testament"),
            "role": p.get("role"),
        }
        for p in people
    ]


@app.get("/v1/people/{name}")
def get_person(name: str, _: Auth) -> dict:
    card = person_card(name)
    if not card:
        raise HTTPException(status_code=404, detail=f"No indexed person matching '{name}'")
    return card
