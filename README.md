# Traceify

[![CI](https://github.com/anmol0b/Traceify/actions/workflows/ci.yml/badge.svg)](https://github.com/anmol0b/Traceify/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> Public profile intelligence: load any public X (Twitter) profile and have a grounded AI conversation about the person, backed by semantic search over their tweets.

**Live demo:** [traceify.anmol0b.xyz](https://traceify.anmol0b.xyz) (the free-tier backend may take ~30s to wake up on the first request)

![Traceify profile page with streamed AI chat](docs/demo.png)

**Stack:** Next.js 16 · TypeScript · Tailwind CSS · FastAPI · Pydantic · Neon (serverless Postgres + pgvector) · psycopg · fastembed · Groq · Docker · GitHub Actions

---

## Features

- **Any public X profile**: enter `@handle`, `handle`, or paste an `x.com/…` URL
- **~100 recent original tweets** fetched with cursor pagination (retweets and replies filtered out)
- **Engagement insights**: top tweets by likes and by views, averages and medians, posting rate and most active times
- **Topic map**: tweets are clustered by meaning (k-means over their embeddings) and an LLM names each cluster, so "what do they tweet about?" is answered over every tweet, not a handful
- **Grounded chat with citations**: the model sees the profile, precomputed stats, topics and the tweets themselves (numbered, dated), and cites them as `[T4]`; the UI turns each citation into a link to the tweet
- **Retrieval for each question**: follow-ups are rewritten into standalone queries, embedded, and matched against the person's tweets (in memory, or pgvector) to point the model at the likeliest tweets
- **Streaming answers** token by token from Groq's gpt-oss-120b, with more reasoning effort for analytical questions
- **Evals, tracing and feedback**: an eval suite with an LLM judge, one structured trace log per answer, and thumbs up/down stored against the prompt version
- **Graceful degradation**: works without a database (in-memory cache) and without an LLM (rule-based answers)
- **24h profile cache** in Postgres, so repeat visits don't spend API quota
- **Typed error states** for invalid handles, missing and private accounts, and rate limits
- **Per-IP rate limiting** to protect the public demo's API quotas

## Architecture

```mermaid
flowchart LR
    U([User]) --> FE["Next.js frontend<br/>(Vercel)"]
    FE -- "GET /api/profiles/{handle}" --> API["FastAPI backend<br/>(Docker)"]
    FE -- "POST /api/chat (streamed)" --> API
    API --> X["RapidAPI twitter241<br/>profile + tweets"]
    API --> EMB["fastembed<br/>bge-small-en-v1.5 (384-d)"]
    API --> DB[("Neon Postgres<br/>profiles · tweets + pgvector")]
    API --> LLM["Groq<br/>gpt-oss-20b / gpt-oss-120b"]
```

**Profile request:** normalize the handle → return the cached profile if it's under 24h old → otherwise fetch the profile and paginated tweets → save the profile row → embed the tweets and upsert them. The profile is saved first because `tweets.handle` has a foreign key to `profiles.handle`.

Fetching also embeds the tweets once and reuses the vectors three ways: topic clustering, the database, and an in-memory search index. One call to the fast model then writes the summary, names the topics and suggests questions tailored to the account.

**Chat request:** load the profile server-side, rather than trusting profile data sent by the client → if it's a follow-up, rewrite it into a standalone query with the fast model → find the most similar tweets above a similarity floor → build the system prompt: rules, then a `<profile_data>` block with the profile, stats, topics, the numbered tweets and the retrieved IDs → append the last 6 exchanges and the question → stream gpt-oss-120b's answer as chunked plain text, with an `X-Request-Id` header the UI sends back with feedback.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness, and which integrations are configured |
| `GET` | `/api/profiles/{handle}` | Profile, insights, starter message, suggested questions. `handle` may be an x.com URL |
| `POST` | `/api/profiles/{handle}/refresh` | Clear the cache and refetch |
| `POST` | `/api/chat` | `{handle, question, history[]}` → `text/plain` stream, `X-Request-Id` header |
| `POST` | `/api/feedback` | `{request_id, handle, rating: "up"\|"down", question, answer}` → 204 |

Errors are returned as `{"code": "...", "message": "..."}`: `invalid_handle` (422), `private_account` (403), `not_found` (404), `rate_limited` / `upstream_rate_limited` (429), `upstream_error` (502), `not_configured` (503). Interactive docs are at `/docs`.

## Project structure

```
backend/
  app/
    main.py               FastAPI app, CORS, error handling, lifespan warm-up
    config.py             Typed settings (pydantic-settings, .env)
    schemas.py            Pydantic request/response models
    errors.py             Domain errors → HTTP status codes
    rate_limit.py         Sliding-window per-IP limiter
    api/                  health · profiles · chat routes
    services/
      x_client.py         RapidAPI client, timeline parsing, insights
      profile_service.py  Cache → fetch → persist orchestration
      repo.py             Postgres persistence (psycopg pool), TTL cache, vector search
      embeddings.py       fastembed wrapper
      chat.py             Prompt and context building, query rewriting, streaming, tracing, fallback
      retrieval.py        Semantic search: in-memory vectors first, pgvector otherwise
      analysis.py         Topic clustering and the ingest LLM pass (summary, topic labels, questions)
      llm.py              Groq client and JSON helpers
      tracing.py          One structured JSON log line per LLM event
      profiles.py         Handle normalization, summaries, suggested questions
  tests/                  pytest suite (HTTP mocked, no network)
  evals/                  Answer-quality evals: a fictional profile, test cases, runner with LLM judge
frontend/
  app/                    Landing page, /x/[handle] profile page
  components/             HandleSearch, ProfileCard, TweetInsights, ChatPanel, ProfileView
  lib/                    Typed API client (incl. stream reader), handle parsing
db/
  schema.sql              Tables, foreign key, HNSW vector index
```

## Running locally

### 1. Database (optional, but needed for a persistent cache and stored feedback)

Any Postgres with the pgvector extension works. The demo uses a free [Neon](https://neon.tech) project: copy its **pooled** connection string into `DATABASE_URL`, then apply the schema with `psql "$DATABASE_URL" -f db/schema.sql` (it's idempotent, so re-run it after upgrading to add new tables) (or paste [`db/schema.sql`](db/schema.sql) into Neon's SQL editor).

### 2. Backend

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env        # fill in your keys
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local  # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                 # http://localhost:3000
```

### Or with Docker

```bash
cp backend/.env.example backend/.env   # fill in your keys
docker compose up --build
```

## Configuration

| Variable | Required | Notes |
|---|---|---|
| `RAPIDAPI_KEY` | Yes | [RapidAPI](https://rapidapi.com): subscribe to **twitter241** (free tier) |
| `GROQ_API_KEY` | Recommended | [console.groq.com](https://console.groq.com). Without it, chat uses rule-based answers |
| `DATABASE_URL` | Recommended | Postgres + pgvector connection string. Without it, profiles and embeddings are kept in memory and feedback is only logged |
| `ALLOWED_ORIGINS` | Prod | Comma-separated frontend origins for CORS |
| `GROQ_MODEL_FAST`, `GROQ_MODEL_SMART` | No | Override the models if Groq retires them. Smart writes answers; fast rewrites queries and runs the ingest analysis |
| `CONTEXT_MAX_TWEET_CHARS` | No | Characters of tweet text per chat prompt, default `10000` (fits Groq's free tier). `0` sends every tweet |
| `RETRIEVAL_MIN_SIMILARITY`, `RETRIEVAL_LIMIT` | No | Similarity floor (default `0.5`) and number of retrieved tweets (default `8`) |
| `LLM_TEMPERATURE`, `LLM_MAX_COMPLETION_TOKENS` | No | Defaults `0.3` and `4096` (gpt-oss reasoning tokens count toward the limit) |
| `ANALYZE_ON_INGEST` | No | Default `true`. Set `false` to skip the summary/topics/questions LLM call when fetching |
| `CACHE_TTL_HOURS` | No | Default `24` |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend URL, inlined at build time |

## Testing

```bash
cd backend && ruff check . && pytest -q
cd frontend && npm run lint && npm test && npm run build
```

### Evals

`backend/evals` runs the real chat pipeline (query rewriting, retrieval, prompt, streaming) against a fictional profile whose facts are known. Each case checks for required facts, valid citations, refusals where the data has no answer, prompt injection planted in a tweet, and sensitive-trait questions. With `--judge`, gpt-oss-120b also grades each answer for groundedness.

```bash
cd backend
python -m evals.run --retrieval-only   # embeddings only, no LLM calls
python -m evals.run --judge            # needs GROQ_API_KEY
```

Results are written to `evals/results/` and every answer is tagged with `PROMPT_VERSION`, so you can compare runs before and after a prompt change. The **Evals** workflow runs the suite on demand from the Actions tab (it needs a `GROQ_API_KEY` repository secret). A full run with the judge uses about 100k tokens, half of Groq's free daily quota for gpt-oss-120b.

### Unit tests

The backend suite covers handle and URL parsing, timeline parsing, upstream error mapping, insights, prompt construction (including a regression test that the question is sent only once), streaming and fallback behavior, TTL caching, rate limiting, and the API routes (including a check that the profile is saved before its tweets). The frontend has Vitest tests for handle and URL parsing that use the same cases as the backend, so the two parsers stay in sync. CI runs both jobs on every push and pull request.

## Deployment

- **Backend:** deploy `backend/` as a Docker web service, for example on Render or Fly.io. The embedding model is baked into the image, and the runtime needs well under 512MB of RAM. Set the env vars above, and set `ALLOWED_ORIGINS` to your frontend URL.
- **Frontend:** import `frontend/` into Vercel and set `NEXT_PUBLIC_API_URL`.

## Design decisions

- **FastAPI + Next.js instead of Streamlit.** A typed REST API with streaming responses, a separately deployable frontend, and a real loading, error and empty state for every request.
- **Groq.** Very high tokens/sec, so streamed answers start almost instantly. Every answer comes from gpt-oss-120b; questions that ask for analysis ("analyze", "compare", "why"…) get `reasoning_effort: medium`, and lookups get `low`. The 20b model does the internal jobs: rewriting follow-up questions and the one-off analysis at fetch time.
- **Tweets in the prompt, retrieval as a pointer.** ~100 tweets fit comfortably in gpt-oss's context window, and questions like "what do they tweet about?" need all of them, so the tweets themselves go into the prompt. Retrieval then marks the likeliest ones. On Groq's free tier (8k tokens/minute) the tweet section is capped at about 2.5k tokens, filled with the retrieved, most-engaging and newest tweets; stats and topics are still computed over every tweet.
- **Citations instead of trust.** Answers cite tweets by number and the UI links each one, so readers can check claims, and evals can verify that citations exist.
- **Scraped text is data.** Bios and tweets sit inside a tagged block that the prompt calls untrusted, and angle brackets in them are neutralized so a tweet can't close the block. The eval profile includes a tweet that tries a prompt injection.
- **Evals before tuning.** Measuring changed two of the original plans: the BGE query instruction didn't improve ranking for bge-small-en-v1.5 (it's now an opt-in setting), and the similarity floor had to be 0.5, not 0.6, because real matches score lower than expected.
- **Postgres + pgvector in one database.** Structured cache and embeddings live together, with no separate vector store to run. An HNSW index on the embeddings makes per-handle similarity search a single SQL query.
- **Neon + plain SQL instead of a hosted BaaS client.** Serverless Postgres scales to zero when idle and wakes in under a second, so a free-tier demo never needs a manual restore. The backend talks to it with psycopg and a small connection pool that re-checks connections Neon has dropped.
- **fastembed (ONNX) instead of sentence-transformers.** The same 384-dimensional embeddings without PyTorch, which keeps the container small enough for free hosting tiers.
- **Server-side profile lookup in chat.** The client sends only the handle and history, so it can't inject fake "profile facts" into the prompt.
- **Fail soft.** Database, embedding and LLM failures are logged and degrade gracefully instead of breaking the page.

## Limitations

- Only ~100 of the most recent original tweets are analyzed. Replies aren't fetched, though they often say a lot about someone's views.
- On Groq's free tier, gpt-oss-120b allows 8k tokens a minute and 200k a day: roughly one or two questions a minute and a few dozen a day. The tweet budget keeps each prompt under the per-minute limit, but a busy demo needs a paid tier.
- The eval set is small and synthetic (one fictional profile, 15 cases). It catches regressions; it doesn't prove quality on real accounts.
- The rate limiter is in-memory and per-process. A multi-instance deployment would need Redis.
- Data comes from a third-party RapidAPI wrapper and is subject to its availability and quotas.

## License

[MIT](LICENSE)
