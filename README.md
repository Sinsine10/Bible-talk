# Bible People RAG

HTTP API that answers questions about **people in the Bible** using retrieval-augmented generation.

It indexes:

- A curated people file (`data/people.json`) with aliases, so “Cephas”, “Saul of Tarsus”, and the various Marys/Johns/Jameses can be told apart
- The public-domain **King James** text (downloaded on ingest)

Callers get a grounded answer plus the verses and person cards that were retrieved.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m biblerag ingest
python -m biblerag serve
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive API.

Ingest downloads the KJV JSON and builds a Chroma index under `data/index`. The first run also downloads a small ONNX MiniLM embedding model.

## Use the API

Ask about a person:

```powershell
curl -s http://127.0.0.1:8000/v1/ask -H "Content-Type: application/json" -d "{\"question\": \"Who was Barnabas and what did he do with Paul?\"}"
```

Search passages:

```powershell
curl -s "http://127.0.0.1:8000/v1/search?q=Peter%20denies%20Jesus"
```

List or fetch a person card:

```powershell
curl -s http://127.0.0.1:8000/v1/people
curl -s http://127.0.0.1:8000/v1/people/Barnabas
```

Without an LLM key, `POST /v1/ask` still works: `mode` is `extractive` and the answer is assembled from the best person profile plus supporting verses.

### Optional generated answers

Copy `.env.example` to `.env` and set an OpenAI-compatible key:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Or point at local Ollama:

```
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.1
```

### Optional shared secret

If you set `BIBLERAG_API_KEY`, every `/v1/*` route requires:

```
Authorization: Bearer <your-key>
```

`/health` stays public.

## Docker

```powershell
docker compose up --build
```

The image runs ingest on first start if `data/index` is empty.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Index size and whether generation is enabled |
| POST | `/v1/ask` | Question → answer + cited passages |
| GET | `/v1/search` | Semantic search only |
| GET | `/v1/people` | Indexed people (`?q=` filters) |
| GET | `/v1/people/{name}` | Profile + related verses |

Translation in the index is KJV (public domain). People summaries are a study aid; verses are the primary source.
