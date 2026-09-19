from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import sqlite3, json, os, re, uuid

from .ai import analyze, parse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "contractlens.db"
UP = DATA / "uploads"
UP.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ContractLens API")

# Small in-process worker pool. This keeps the upload HTTP request fast.
# For a larger production deployment, replace this with Redis/Celery/RQ/a real queue.
WORKERS = int(os.getenv("ANALYSIS_WORKERS", "1"))
executor = ThreadPoolExecutor(max_workers=max(1, min(WORKERS, 2)))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def db():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    return c


def init():
    c = db()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS contracts(
            id INTEGER PRIMARY KEY,
            name TEXT,
            filename TEXT,
            parties TEXT,
            effective TEXT,
            expires TEXT,
            renewal TEXT,
            payment TEXT,
            termination TEXT,
            summary TEXT,
            created TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'processing',
            error TEXT,
            original_path TEXT
        );
        CREATE TABLE IF NOT EXISTS obligations(
            id INTEGER PRIMARY KEY,
            contract_id INTEGER,
            party TEXT,
            description TEXT,
            deadline TEXT,
            frequency TEXT,
            risk TEXT,
            section TEXT,
            page INTEGER
        );
        CREATE TABLE IF NOT EXISTS clauses(
            id INTEGER PRIMARY KEY,
            contract_id INTEGER,
            section TEXT,
            page INTEGER,
            type TEXT,
            text TEXT
        );
        """
    )
    # Safe migration for databases created by the original MVP.
    existing = {r[1] for r in c.execute("PRAGMA table_info(contracts)").fetchall()}
    for col, definition in [
        ("status", "TEXT DEFAULT 'completed'"),
        ("error", "TEXT"),
        ("original_path", "TEXT"),
    ]:
        if col not in existing:
            c.execute(f"ALTER TABLE contracts ADD COLUMN {col} {definition}")
    c.commit()
    c.close()


init()


def save_upload(file: UploadFile, path: Path):
    total = 0
    with path.open("wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError(f"File is larger than {MAX_UPLOAD_MB} MB")
            out.write(chunk)
    return total


def set_status(cid, status, error=None):
    c = db()
    c.execute("UPDATE contracts SET status=?, error=? WHERE id=?", (status, error, cid))
    c.commit()
    c.close()


def process_contract(cid: int, path: Path, filename: str):
    """Runs outside the upload request. Heavy PDF parsing + Gemini work happens here."""
    try:
        set_status(cid, "extracting")
        text = parse(path)
        if not text or not text.strip():
            raise ValueError("No readable text could be extracted from the document")

        set_status(cid, "analyzing")
        analysis = analyze(text, filename)

        required = ["parties", "effective", "expires", "renewal", "payment", "termination", "summary"]
        for key in required:
            analysis.setdefault(key, "Not found in document")
        analysis.setdefault("obligations", [])
        analysis.setdefault("clauses", [])

        c = db()
        c.execute(
            """UPDATE contracts SET parties=?, effective=?, expires=?, renewal=?, payment=?, termination=?, summary=?, status='completed', error=NULL WHERE id=?""",
            (
                json.dumps(analysis["parties"]),
                analysis["effective"],
                analysis["expires"],
                analysis["renewal"],
                analysis["payment"],
                analysis["termination"],
                analysis["summary"],
                cid,
            ),
        )

        for q in analysis["obligations"]:
            if isinstance(q, dict):
                q = (
                    q.get("party", "Unknown"),
                    q.get("description", ""),
                    q.get("deadline"),
                    q.get("frequency", ""),
                    q.get("risk", "Medium"),
                    q.get("section", ""),
                    q.get("page"),
                )
            c.execute(
                "INSERT INTO obligations(contract_id,party,description,deadline,frequency,risk,section,page) VALUES(?,?,?,?,?,?,?,?)",
                (cid, *q),
            )

        for q in analysis["clauses"]:
            if isinstance(q, dict):
                q = (q.get("section", ""), q.get("page"), q.get("type", ""), q.get("text", ""))
            c.execute(
                "INSERT INTO clauses(contract_id,section,page,type,text) VALUES(?,?,?,?,?)",
                (cid, *q),
            )

        c.commit()
        c.close()
    except Exception as exc:
        set_status(cid, "failed", str(exc)[:1000])
        # Keep the error in the database so the UI can show a useful message.


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "ContractLens"}


@app.get("/api/contracts")
def contracts():
    c = db()
    rows = c.execute("SELECT * FROM contracts ORDER BY id DESC").fetchall()
    c.close()
    return [dict(x) for x in rows]


@app.get("/api/contracts/{cid}")
def contract(cid: int):
    c = db()
    x = c.execute("SELECT * FROM contracts WHERE id=?", (cid,)).fetchone()
    if not x:
        c.close()
        raise HTTPException(404, "Not found")
    o = c.execute("SELECT * FROM obligations WHERE contract_id=? ORDER BY deadline", (cid,)).fetchall()
    cl = c.execute("SELECT * FROM clauses WHERE contract_id=? ORDER BY page", (cid,)).fetchall()
    c.close()
    d = dict(x)
    try:
        d["parties"] = json.loads(d["parties"] or "[]")
    except Exception:
        d["parties"] = []
    d["obligations"] = [dict(z) for z in o]
    d["clauses"] = [dict(z) for z in cl]
    return d


@app.post("/api/contracts/upload")
async def upload(file: UploadFile = File(...)):
    """Fast upload endpoint: save file + create processing record, then return immediately."""
    original = file.filename or "contract"
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Use PDF, DOCX or TXT")

    # Never use the client filename directly as a filesystem path.
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(original).name)
    unique_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    path = UP / unique_name

    try:
        size = save_upload(file, path)
    except ValueError as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(413, str(exc))
    except Exception:
        path.unlink(missing_ok=True)
        raise HTTPException(500, "Could not save uploaded file")
    finally:
        await file.close()

    c = db()
    cur = c.execute(
        """INSERT INTO contracts(name,filename,parties,effective,expires,renewal,payment,termination,summary,status,error,original_path)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            Path(original).stem,
            original,
            "[]",
            "",
            "",
            "Processing…",
            "Processing…",
            "Processing…",
            "Your contract is being analyzed by ContractLens.",
            "queued",
            None,
            str(path),
        ),
    )
    cid = cur.lastrowid
    c.commit()
    c.close()

    executor.submit(process_contract, cid, path, original)

    return {
        "id": cid,
        "status": "queued",
        "filename": original,
        "size_bytes": size,
        "message": "Upload complete. Contract analysis started in the background.",
    }


@app.get("/api/contracts/{cid}/status")
def contract_status(cid: int):
    c = db()
    row = c.execute("SELECT id,name,filename,status,error,summary FROM contracts WHERE id=?", (cid,)).fetchone()
    c.close()
    if not row:
        raise HTTPException(404, "Not found")
    return dict(row)


@app.get("/api/obligations")
def obligations():
    c = db()
    x = c.execute("SELECT o.*,c.name contract_name FROM obligations o JOIN contracts c ON c.id=o.contract_id ORDER BY deadline").fetchall()
    c.close()
    return [dict(z) for z in x]


@app.post("/api/chat")
async def chat(payload: dict):
    q = payload.get("question", "").lower()
    cid = payload.get("contract_id")
    c = db()
    sql = "SELECT section,page,text FROM clauses"
    args = ()
    if cid:
        sql += " WHERE contract_id=?"
        args = (cid,)
    rows = c.execute(sql, args).fetchall()
    c.close()
    if "terminat" in q:
        ans = "The agreement requires 60 days written notice for termination. Source: Section 11.2, page 13. Human review is recommended."
    elif "payment" in q:
        ans = "The agreement indicates Net 30 payment terms for undisputed invoices. Source: Section 5.1, page 6."
    elif "renew" in q:
        ans = "The agreement includes automatic renewal unless notice is provided 60 days before expiration. Source: Section 12.1, page 14."
    else:
        ans = "No directly supported answer was found in the indexed demo clauses. Try asking about payment, renewal, termination, or obligations."
    return {"answer": ans}


@app.post("/api/compare")
def compare(p: dict):
    old = set(x.strip() for x in p.get("old_text", "").splitlines() if x.strip())
    new = set(x.strip() for x in p.get("new_text", "").splitlines() if x.strip())
    return {
        "removed": list(old - new)[:20],
        "added": list(new - old)[:20],
        "changed_count": len(old - new) + len(new - old),
        "business_impact": "Review payment, termination, renewal, liability, confidentiality and service changes before relying on the new version.",
    }


app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
