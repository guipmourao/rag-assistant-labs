# RAG Assistant Lab

A FastAPI backend for a Retrieval-Augmented Generation pipeline: upload a PDF, split it into
chunks, embed and index it in a vector store (Chroma), then ask questions or chat over the
indexed content with OpenAI answering from the retrieved context.

## Stack

- FastAPI + Pydantic (API, validation, settings)
- LangChain + LangChain-OpenAI (splitting, embeddings, retrieval, chat)
- Chroma (vector store, persisted to disk)
- slowapi (per-IP rate limiting)
- Docker / docker-compose

## Structure

```
backend/
  src/app/
    main.py              # app factory: middleware, exception handlers, router mounting
    core/
      config.py           # Settings (pydantic-settings, reads .env)
      security.py         # API key authentication dependency
      rate_limit.py        # per-IP rate limiter
      logging.py          # logging setup
      exceptions.py        # global exception handlers
    api/v1/
      api.py               # aggregates versioned routers
      endpoints/           # health, documents
    schemas/               # Pydantic request/response models
    services/              # PDF loading, splitting, embeddings, vector store, chat memory
  uploads/                  # uploaded PDFs (gitignored)
  storage/                  # Chroma persistence (gitignored)
  requirements.txt
  Dockerfile
```

## Endpoints

All routes under `/api/v1/documents/*` require an `X-API-Key` header matching `API_KEY` from
`.env`. `/api/v1/health` is open.

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/documents/upload` | Upload a PDF, returns page count and a preview |
| POST | `/api/v1/documents/upload-and-split` | Upload + split into chunks |
| POST | `/api/v1/documents/upload-and-index` | Upload + split + index into Chroma |
| POST | `/api/v1/documents/split-text` | Split raw text (no upload) |
| POST | `/api/v1/documents/search` | Similarity/MMR search over indexed chunks |
| POST | `/api/v1/documents/ask` | Ask a one-off question over indexed content |
| POST | `/api/v1/documents/chat` | Ask with conversation memory (`session_id`) |
| POST | `/api/v1/documents/chat/clear` | Clear a chat session's history |
| GET | `/api/v1/health` | Health check (no auth) |

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # set OPENAI_API_KEY and API_KEY
uvicorn app.main:app --reload --app-dir src --host 0.0.0.0 --port 8000
```

Interactive API docs: http://localhost:8000/docs

## Run with Docker

```bash
cp .env.example backend/.env   # set OPENAI_API_KEY and API_KEY
docker compose up --build
```

`docker-compose.override.yml` is loaded automatically and publishes port 8000 for local access.

## Try it

```bash
API_KEY=your-api-key-from-.env

curl http://localhost:8000/api/v1/health

curl -X POST http://localhost:8000/api/v1/documents/upload-and-index \
  -H "X-API-Key: $API_KEY" \
  -F "file=@/path/to/some.pdf"

curl -X POST http://localhost:8000/api/v1/documents/ask \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "k": 3}'
```

## Deploy behind a reverse proxy

`docker-compose.prod.yml` joins an existing external Docker network (e.g. the one your
reverse proxy uses) instead of publishing a port on the host:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

If the app is served under a path prefix (e.g. `https://example.com/labs/rag/`), set
`ROOT_PATH` in `.env` to that prefix so the generated docs and OpenAPI schema use the
right URLs, and configure the reverse proxy to strip the prefix before forwarding.

## Known limitations

- No automated test suite yet.
- Chat sessions and their history live in an in-memory dict (`app/services/chat_memory.py`);
  they reset on restart and aren't shared across multiple replicas.
