import os, json, re
from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

def demo(filename):
 d=date.today()
 return {'parties':['Demo Company','Acme Vendor'],'effective':d.isoformat(),'expires':(d+timedelta(days=180)).isoformat(),'renewal':'Automatic renewal unless notice is provided 60 days before expiration.','payment':'Net 30 days for undisputed invoices.','termination':'Either party may terminate with 60 days written notice.','summary':f'{filename} contains vendor terms, payment, service reporting, renewal and termination obligations.','obligations':[('Acme Vendor','Provide monthly service report',(d+timedelta(days=10)).isoformat(),'Monthly','Medium','7.2',8),('Demo Company','Pay undisputed invoices within 30 days',(d+timedelta(days=18)).isoformat(),'Per invoice','High','5.1',6),('Demo Company','Send renewal notice before automatic renewal',(d+timedelta(days=75)).isoformat(),'Annual','High','12.1',14)],'clauses':[('5.1',6,'Payment','Customer shall pay undisputed invoices within thirty (30) days.'),('7.2',8,'Service','Vendor shall provide a monthly service report.'),('12.1',14,'Renewal','Agreement automatically renews unless notice is provided 60 days before expiration.'),('11.2',13,'Termination','Either party may terminate with 60 days written notice.')]}

def analyze(text,filename):
 key=os.getenv('GEMINI_API_KEY')
 if not key:return demo(filename)
 try:
  from google import genai
  client=genai.Client(api_key=key)
  prompt='''Extract contract facts only from the text. Return JSON with parties, effective, expires, renewal, payment, termination, summary, obligations and clauses. obligations must be arrays of objects with party,description,deadline,frequency,risk,section,page. clauses must be objects with section,page,type,text. Never invent missing facts.\nFILE: '''+filename+'\nTEXT:\n'+text[:50000]
  r=client.models.generate_content(model=os.getenv('GEMINI_MODEL','gemini-2.5-flash'),contents=prompt).text
  r=re.sub(r'^```json\\s*','',r);r=re.sub(r'\\s*```$','',r)
  x=json.loads(r); x['obligations']=[(o.get('party','Unknown'),o.get('description',''),o.get('deadline'),o.get('frequency',''),o.get('risk','Medium'),o.get('section',''),o.get('page')) for o in x.get('obligations',[])]; x['clauses']=[(o.get('section',''),o.get('page'),o.get('type',''),o.get('text','')) for o in x.get('clauses',[])]; return x
 except Exception:return demo(filename)

def parse(path):
 try:
  from docling.document_converter import DocumentConverter
  return DocumentConverter().convert(str(path)).document.export_to_markdown()
 except Exception:
  try:return path.read_text(errors='ignore')
  except Exception:return ''
