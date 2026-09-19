import os
import json
import re
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

# Keep the AI prompt compact. The original MVP sent up to 50,000 characters,
# which can make Gemini the slowest part of the upload experience.
MAX_AI_CHARS = int(os.getenv("MAX_AI_CHARS", "40000"))


def demo(filename):
    d = date.today()
    return {
        "parties": ["Demo Company", "Acme Vendor"],
        "effective": d.isoformat(),
        "expires": (d + timedelta(days=180)).isoformat(),
        "renewal": "Automatic renewal unless notice is provided 60 days before expiration.",
        "payment": "Net 30 days for undisputed invoices.",
        "termination": "Either party may terminate with 60 days written notice.",
        "summary": f"{filename} contains vendor terms, payment, service reporting, renewal and termination obligations.",
        "obligations": [
            ("Acme Vendor", "Provide monthly service report", (d + timedelta(days=10)).isoformat(), "Monthly", "Medium", "7.2", 8),
            ("Demo Company", "Pay undisputed invoices within 30 days", (d + timedelta(days=18)).isoformat(), "Per invoice", "High", "5.1", 6),
            ("Demo Company", "Send renewal notice before automatic renewal", (d + timedelta(days=75)).isoformat(), "Annual", "High", "12.1", 14),
        ],
        "clauses": [
            ("5.1", 6, "Payment", "Customer shall pay undisputed invoices within thirty (30) days."),
            ("7.2", 8, "Service", "Vendor shall provide a monthly service report."),
            ("12.1", 14, "Renewal", "Agreement automatically renews unless notice is provided 60 days before expiration."),
            ("11.2", 13, "Termination", "Either party may terminate with 60 days written notice."),
        ],
    }


def _clean_json(raw: str):
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)
    # Gemini can occasionally return surrounding prose. Try to isolate the JSON object.
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start:end + 1]
    return json.loads(raw)


def analyze(text, filename):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return demo(filename)

    try:
        from google import genai

        client = genai.Client(api_key=key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        source = text[:MAX_AI_CHARS]

        prompt = f"""Analyze this business contract. Extract ONLY facts explicitly supported by the text.
Return ONLY valid JSON with this exact top-level shape:
{{"parties":[],"effective":"","expires":"","renewal":"","payment":"","termination":"","summary":"","obligations":[{{"party":"","description":"","deadline":null,"frequency":"","risk":"Low|Medium|High","section":"","page":null}}],"clauses":[{{"section":"","page":null,"type":"","text":""}}]}}
Rules: never invent missing facts; use null or an empty string when absent; keep summary concise; prioritize payment, renewal, termination, SLA, security, audit, insurance, milestone and notice obligations.
FILE: {filename}
CONTRACT TEXT:
{source}"""

        response = client.models.generate_content(model=model, contents=prompt)
        x = _clean_json(response.text)

        x.setdefault("parties", [])
        x.setdefault("effective", "")
        x.setdefault("expires", "")
        x.setdefault("renewal", "")
        x.setdefault("payment", "")
        x.setdefault("termination", "")
        x.setdefault("summary", "")
        x.setdefault("obligations", [])
        x.setdefault("clauses", [])

        # Preserve the tuple shape expected by the existing database code.
        x["obligations"] = [
            (
                o.get("party", "Unknown"),
                o.get("description", ""),
                o.get("deadline"),
                o.get("frequency", ""),
                o.get("risk", "Medium"),
                o.get("section", ""),
                o.get("page"),
            )
            for o in x["obligations"]
            if isinstance(o, dict)
        ]
        x["clauses"] = [
            (
                o.get("section", ""),
                o.get("page"),
                o.get("type", ""),
                o.get("text", ""),
            )
            for o in x["clauses"]
            if isinstance(o, dict)
        ]
        return x
    except Exception:
        # Keep the existing MVP's graceful fallback behavior.
        return demo(filename)


def parse(path):
    try:
        from docling.document_converter import DocumentConverter
        return DocumentConverter().convert(str(path)).document.export_to_markdown()
    except Exception:
        try:
            return path.read_text(errors="ignore")
        except Exception:
            return ""
