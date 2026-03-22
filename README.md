# Traceify

Traceify is now a Streamlit-only app. It accepts a public LinkedIn URL or X handle, lets you optionally paste public notes/posts, and turns that context into a chat experience.

## What it does

- Runs as a single Streamlit app
- Accepts a public LinkedIn profile URL or X handle
- Supports optional manual public notes and post snippets
- Uses Groq when available for richer answers
- Includes a separate Streamlit page for RapidAPI-based X profile lookup
- Falls back to rule-based answers when no model or live enrichment is available

## Run locally

1. Activate your environment:

```bash
conda activate tracify
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in any values you have.

4. Start the app:

```bash
streamlit run app.py
```

5. Open [http://127.0.0.1:8501](http://127.0.0.1:8501).

## Environment variables

- `GROQ_API_KEY` for LLM answers
- `LINKEDIN_USERNAME` and `LINKEDIN_PASSWORD` for best-effort LinkedIn enrichment
- `RAPIDAPI_KEY` for the separate X profile lookup page

If those values are missing, the app still works in fallback mode.
