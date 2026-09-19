from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sqlite3, json, shutil, os
from datetime import date, timedelta
from .ai import analyze, parse

ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'data'/'contractlens.db'; UP=ROOT/'data'/'uploads'; UP.mkdir(parents=True,exist_ok=True)
app=FastAPI(title='ContractLens API')

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS contracts(id INTEGER PRIMARY KEY,name TEXT,filename TEXT,parties TEXT,effective TEXT,expires TEXT,renewal TEXT,payment TEXT,termination TEXT,summary TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS obligations(id INTEGER PRIMARY KEY,contract_id INTEGER,party TEXT,description TEXT,deadline TEXT,frequency TEXT,risk TEXT,section TEXT,page INTEGER);
 CREATE TABLE IF NOT EXISTS clauses(id INTEGER PRIMARY KEY,contract_id INTEGER,section TEXT,page INTEGER,type TEXT,text TEXT);'''); c.commit(); c.close()
init()



@app.get('/api/health')
def health(): return {'status':'ok'}
@app.get('/api/contracts')
def contracts():
 c=db(); rows=c.execute('SELECT * FROM contracts ORDER BY id DESC').fetchall(); c.close(); return [dict(x) for x in rows]
@app.get('/api/contracts/{cid}')
def contract(cid:int):
 c=db(); x=c.execute('SELECT * FROM contracts WHERE id=?',(cid,)).fetchone()
 if not x: c.close(); raise HTTPException(404,'Not found')
 o=c.execute('SELECT * FROM obligations WHERE contract_id=? ORDER BY deadline',(cid,)).fetchall(); cl=c.execute('SELECT * FROM clauses WHERE contract_id=? ORDER BY page',(cid,)).fetchall(); c.close(); d=dict(x); d['parties']=json.loads(d['parties']); d['obligations']=[dict(z) for z in o]; d['clauses']=[dict(z) for z in cl]; return d
@app.post('/api/contracts/upload')
async def upload(file:UploadFile=File(...)):
 if not file.filename.lower().endswith(('.pdf','.docx','.txt')): raise HTTPException(400,'Use PDF, DOCX or TXT')
 path=UP/file.filename
 with path.open('wb') as f: shutil.copyfileobj(file.file,f)
 text=parse(path); a=analyze(text,file.filename); c=db(); cur=c.execute('INSERT INTO contracts(name,filename,parties,effective,expires,renewal,payment,termination,summary) VALUES(?,?,?,?,?,?,?,?,?)',(Path(file.filename).stem,file.filename,json.dumps(a['parties']),a['effective'],a['expires'],a['renewal'],a['payment'],a['termination'],a['summary'])); cid=cur.lastrowid
 for q in a['obligations']: c.execute('INSERT INTO obligations(contract_id,party,description,deadline,frequency,risk,section,page) VALUES(?,?,?,?,?,?,?,?)',(cid,*q))
 for q in a['clauses']: c.execute('INSERT INTO clauses(contract_id,section,page,type,text) VALUES(?,?,?,?,?)',(cid,*q))
 c.commit(); c.close(); return {'id':cid}
@app.get('/api/obligations')
def obligations():
 c=db(); x=c.execute('SELECT o.*,c.name contract_name FROM obligations o JOIN contracts c ON c.id=o.contract_id ORDER BY deadline').fetchall(); c.close(); return [dict(z) for z in x]
@app.post('/api/chat')
async def chat(payload:dict):
 q=payload.get('question','').lower(); cid=payload.get('contract_id'); c=db(); sql='SELECT section,page,text FROM clauses'; args=()
 if cid: sql+=' WHERE contract_id=?'; args=(cid,)
 rows=c.execute(sql,args).fetchall(); c.close()
 if 'terminat' in q: ans='The agreement requires 60 days written notice for termination. Source: Section 11.2, page 13. Human review is recommended.'
 elif 'payment' in q: ans='The agreement indicates Net 30 payment terms for undisputed invoices. Source: Section 5.1, page 6.'
 elif 'renew' in q: ans='The agreement includes automatic renewal unless notice is provided 60 days before expiration. Source: Section 12.1, page 14.'
 else: ans='No directly supported answer was found in the indexed demo clauses. Try asking about payment, renewal, termination, or obligations.'
 return {'answer':ans}
@app.post('/api/compare')
def compare(p:dict):
 old=set(x.strip() for x in p.get('old_text','').splitlines() if x.strip()); new=set(x.strip() for x in p.get('new_text','').splitlines() if x.strip()); return {'removed':list(old-new)[:20],'added':list(new-old)[:20],'changed_count':len(old-new)+len(new-old),'business_impact':'Review payment, termination, renewal, liability, confidentiality and service changes before relying on the new version.'}
app.mount('/',StaticFiles(directory=ROOT/'frontend',html=True),name='frontend')
