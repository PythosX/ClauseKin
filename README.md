# ContractLens — 30-hour hackathon MVP

## Features
Dashboard, contract upload, structured extraction, obligations, timeline, source sections/pages, Q&A, version comparison, alerts, responsive gradient UI.

## AI
- Default: deterministic demo fallback, so the application works without an API key.
- Optional Gemini API: put GEMINI_API_KEY in `.env`. The backend sends parsed contract text to Gemini and asks for structured JSON.
- Optional Docling: used for PDF/DOCX parsing when installed.

## Run on Windows
1. Install Python 3.11+.
2. Extract the ZIP.
3. Open the extracted folder in a terminal.
4. `python -m venv .venv`
5. `.venv\\Scripts\\activate`
6. `pip install -r requirements.txt`
7. Copy `.env.example` to `.env` and optionally add `GEMINI_API_KEY`.
8. `uvicorn backend.main:app --reload`
9. Open `http://127.0.0.1:8000`.

## GitHub
Upload the extracted folder to a new GitHub repository. Do NOT upload `.env`, API keys, `.venv`, or the SQLite database.

## Demo
Upload any PDF/DOCX/TXT. The fallback creates sample structured obligations so every dashboard workflow can be demonstrated even before configuring an AI key.

## Disclaimer
Prototype only. ContractLens is not legal advice and extracted terms must be verified against the source agreement.
