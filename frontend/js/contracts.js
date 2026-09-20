async function load(){
  shell('contracts','Contracts','Upload, inspect and manage agreements.');

  document.querySelector('#content').innerHTML=`
    <div class="card">
      <div class="drop">
        <h3>Upload a contract</h3>
        <p class="muted">PDF, DOCX or TXT • Maximum 25 MB</p>
        <input id="file" type="file" accept=".pdf,.docx,.txt">
        <button class="btn" id="upload">Analyze contract</button>
      </div>
      <div id="uploadProcessing" class="upload-processing">
        <div class="processing-spinner"></div>
        <div class="processing-content">
          <div class="processing-title" id="processingTitle">Analyzing contract<span class="processing-dots"></span></div>
          <div id="uploadStatus" class="processing-status">Preparing...</div>
          <div class="processing-track"><div id="processingBar" class="processing-bar"></div></div>
        </div>
      </div>
    </div>
    <div id="list" class="cards" style="margin-top:16px"></div>`;

  async function render(){
    let c=await api('/contracts');
    document.querySelector('#list').innerHTML=c.map(x=>`
      <div class="card contract-card" onclick="location='/pages/contract.html?id=${x.id}'">
        <div class="kpi">${String(x.status||'completed').toUpperCase()}</div>
        <h3>${esc(x.name)}</h3>
        <p class="muted">${esc(x.filename)}</p>
        <span class="badge ${x.status==='failed'?'high':x.status==='completed'?'low':'medium'}">${esc(x.status||'Analyzed')}</span>
        <span class="kpi"> ${fmt(x.expires)} expiry</span>
      </div>`).join('')||'<div class="card"><p class="muted">No contracts yet.</p></div>';
  }

  const processing=document.querySelector('#uploadProcessing');
  const statusText=document.querySelector('#uploadStatus');
  const bar=document.querySelector('#processingBar');
  const title=document.querySelector('#processingTitle');

  function showProcessing(message, percent=10, failed=false){
    processing.classList.add('active');
    statusText.textContent=message;
    bar.style.width=percent+'%';
    title.textContent=failed?'Upload failed':'Analyzing contract';
    processing.classList.toggle('processing-failed',failed);
  }

  function hideProcessing(){
    setTimeout(()=>processing.classList.remove('active'),1200);
  }

  async function monitorContract(id){
    const messages={
      queued:['Queued for analysis...',15],
      extracting:['Extracting text and contract structure...',35],
      analyzing:['AI is identifying obligations, dates and clauses...',70],
      completed:['Analysis completed successfully!',100],
      failed:['Contract analysis failed.',100]
    };
    for(let attempt=0;attempt<180;attempt++){
      const r=await fetch(`/api/contracts/${id}/status`);
      if(!r.ok) throw new Error(`Status check failed (${r.status})`);
      const data=await r.json();
      const [msg,pct]=messages[data.status]||['Processing contract...',50];
      showProcessing(msg,pct,data.status==='failed');
      if(data.status==='completed'){
        await render();
        setTimeout(()=>location=`/pages/contract.html?id=${id}`,700);
        return;
      }
      if(data.status==='failed') throw new Error(data.error||'Contract analysis failed.');
      await new Promise(resolve=>setTimeout(resolve,2000));
    }
    throw new Error('Analysis timed out. Check the Contracts page or Render logs.');
  }

  document.querySelector('#upload').onclick=async()=>{
    const f=document.querySelector('#file').files[0];
    if(!f)return alert('Choose a file first.');

    const allowed=['application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','text/plain'];
    const ext=f.name.toLowerCase().split('.').pop();
    if(!['pdf','docx','txt'].includes(ext))return alert('Use PDF, DOCX or TXT.');
    if(f.size>25*1024*1024)return alert('File is larger than the 25 MB limit.');

    showProcessing('Uploading document...',5);
    try{
      const fd=new FormData();
      fd.append('file',f);
      const r=await fetch('/api/contracts/upload',{method:'POST',body:fd});
      const raw=await r.text();
      let data={};
      try{data=JSON.parse(raw)}catch{}
      if(!r.ok)throw new Error(data.detail||`Upload failed (${r.status})`);
      if(!data.id)throw new Error('Upload succeeded but no contract ID was returned.');
      showProcessing('Upload complete. Starting AI analysis...',12);
      await monitorContract(data.id);
    }catch(err){
      console.error(err);
      showProcessing(err.message||'Upload failed.',100,true);
      setTimeout(hideProcessing,5000);
    }
  };

  await render();
}
load().catch(console.error);
