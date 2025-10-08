# AI SQL Writer

Streamlit app that helps you draft and debug SQL using the OpenAI Responses API (`text-to-sql.py`) or the legacy Assistants API sample (`app.py`). A vector store can be attached so the model can retrieve schema context before writing SQL.

## Requirements
- Python 3.9+
- Valid OpenAI API key with access to the `gpt-4o-mini` model
- (Optional) Streamlit Community Cloud account for deployment

## Project layout
- `text-to-sql.py`: Primary Streamlit entry point that calls the Responses API and supports token usage reporting.
- `app.py`: Legacy Assistants API version retained for reference.
- `schema/emulsion_amra_vector_docs.json`: Example documents already embedded into the vector store (table name `emulsion_amra_data`, project “EMULSION AMRA”).
- `.streamlit/secrets.toml`: Where Streamlit reads sensitive config when running locally or on Community Cloud.
- `requirements.txt`: Python dependencies.

## Environment setup
```bash
python -m venv .venv
source .venv/bin/activate              # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Secrets & configuration
Both scripts first look for environment variables, then fall back to `st.secrets`. Configure **either** environment variables **or** `.streamlit/secrets.toml`.

### Option A. Environment variables (recommended for local development)
```bash
export OPENAI_API_KEY="sk-..."                   # required
export OPENAI_MODEL="gpt-4o-mini"                # default model in use
export VECTOR_STORE_IDS="vs_68e38c858f748191adcca03cfa9607fc"  # vector store with the EMULSION AMRA schema
export DEFAULT_SQL_SYSTEM="..."                  # optional custom system prompt
```

### Option B. `.streamlit/secrets.toml`
```toml
# Never commit live credentials.
OPENAI_API_KEY = "sk-your-openai-key"
OPENAI_MODEL = "gpt-4o-mini"
VECTOR_STORE_IDS = "vs_68e38c858f748191adcca03cfa9607fc"
DEFAULT_SQL_SYSTEM = """
You write one SQL query for a Postgres-like database.
- Use exact column and table names from retrieved files or context.
- All measurements (like left/right/anterior/posterior) are stored as separate columns in the same table — do NOT use JOIN for them.
- Prefer SELECT queries; no schema-altering or deletion statements.
- If unsure about a threshold or column, add a short SQL comment like: -- assume VAT ratio > 30
- Return exactly one SQL query in a single ```sql block with no prose or markdown headings.
"""
```

- `OPENAI_MODEL`: Currently set to `gpt-4o-mini`.
- `VECTOR_STORE_IDS`: Points to the vector store that contains the `emulsion_amra_data` schema.
- `DEFAULT_SQL_SYSTEM`: System prompt shared below in full; adjust if your schema changes.

> 🔐 **Security note:** Replace any example keys with your own and keep them out of version control.

### Default SQL system prompt
The app ships with the following system prompt, optimised for Postgres-style SQL over the EMULSION AMRA dataset:

```text
You write one SQL query for a Postgres-like database.

- Use exact column and table names from retrieved files or context.
- All measurements (like left/right/anterior/posterior) are stored as separate columns in the same table — do NOT use JOIN for them.
- Prefer SELECT queries; no schema-altering or deletion statements.
- If unsure about a threshold or column, add a short SQL comment like: -- assume VAT ratio > 30
- Return exactly one SQL query in a single ```sql block with no prose or markdown headings.
```

## Run locally

### Recommended: Responses API app
```bash
streamlit run text-to-sql.py
```
- Opens at http://localhost:8501 by default.
- Maintains the latest 6 chat turns and surfaces token usage in the sidebar.

### Legacy Assistants API sample
```bash
streamlit run app.py
```
- Provided for historical reference; the production flow should prefer `text-to-sql.py`.

## Smoke test checklist
- The Streamlit UI should launch without “Missing OPENAI_API_KEY”.
- Prompt `“Write SQL to count subjects in emulsion_amra_data”` and confirm a single SQL block is returned.
- If vector retrieval is configured, ask for a column-specific query and confirm relevant fields appear in the SQL.

## Deploy on Streamlit Community Cloud
1. Push this folder to GitHub (ensure secrets are removed).
2. On https://share.streamlit.io, create a new app pointing to `text-to-sql.py`.
3. Paste the secrets from above into **App secrets** in the Streamlit dashboard.
4. Deploy; future git pushes trigger rebuilds automatically.

## Troubleshooting
- **401/403 from OpenAI:** Check the API key, billing limits, and that the vector store lives in the same OpenAI project as your key.
- **Empty or malformed responses:** Inspect the Streamlit terminal logs; the Responses API will report schema or payload issues there.
- **No retrieval hits:** Confirm `VECTOR_STORE_IDS` matches the store containing the EMULSION AMRA embeddings and that the documents reference `emulsion_amra_data`.

