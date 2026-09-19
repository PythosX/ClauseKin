async function load(){
  shell('contracts','Contracts','Upload, inspect and manage agreements.');
  document.querySelector('#content').innerHTML=`
    <div class="card">
      <div class="drop" id="dropZone">
        <h3>Upload a contract</h3>
        <p class="muted">PDF, DOCX or TXT · Max 25 MB</p>
        <input id="file" type="file" accept=".pdf,.docx,.txt">
        <button class="btn" id="upload">Analyze contract</button>
      </div>
      <div id="uploadProcessing" class="upload-processing" aria-live="polite">
        <div class="processing-spinner"></div>
        <div class="processing-content">
          <div class="processing-title">Analyzing contract<span class="processing-dots"></span></div>
          <div id="uploadStatus" class="processing-status">Preparing upload...</div>
          <div class="processing-bar"><div id="uploadProgress" class="processing-bar-fill"></div></div>
        </div>
      </div>
    </div>
    <div class="card upload-tip" style="margin-top:16px">
      <b>What happens next?</b>
      <span class="muted">Your file is uploaded first, then text extraction and AI analysis run in the background. You can keep watching the live status instead of waiting on a single long request.</span>
    </div>
    <div id="list" class="cards" style="margin-top:16px"></div>`;

  async function render(){
    const c=await api('/contracts');
    document.querySelector('#list').innerHTML=c.map(x=>{
      const status=x.status||'completed';
      const cls=status==='failed'?'high':(status==='completed'?'low':'medium');
      const clickable=status==='completed';
      return `<div class="card contract-card ${clickable?'':'contract-card-processing'}" ${clickable?`onclick="location='/pages/contract.html?id=${x.id}'"`:''}>
        <div class="contract-row"><div><div class="kpi">CONTRACT</div><h3>${esc(x.name)}</h3><p class="muted">${esc(x.filename)}</p></div><span class="badge ${cls}">${esc(status)}</span></div>
        <div class="contract-meta">${status==='completed'?`<span>${fmt(x.expires)} expiry</span>`:`<span>${status==='failed'?'Analysis failed':'Processing in background'}</span>`}</div>
        ${status==='failed'?`<div class="notice" style="margin-top:12px">${esc(x.error||'The contract could not be analyzed.')}</div>`:''}
      </div>`;
    }).join('')||'<div class="card"><p class="muted">No contracts yet.</p></div>';
  }

  async function monitorContract(contractId){
    const statusText=document.querySelector('#uploadStatus');
    const progress=document.querySelector('#uploadProgress');
    const messages={queued:['Queued — preparing the contract...',15],extracting:['Extracting text and contract structure...',40],analyzing:['AI is identifying dates, obligations and clauses...',75],completed:['Analysis completed successfully!',100],failed:['Analysis failed.',100]};
    for(let i=0;i<180;i++){
      const r=await fetch(`/api/contracts/${contractId}/status`);
      if(!r.ok){
        let detail='Could not check analysis status';
        try{const err=await r.json(); detail=err.detail||detail;}catch{}
        throw new Error(`${detail} (HTTP ${r.status})`);
      }
      const data=await r.json();
      const item=messages[data.status]||['Processing contract...',50];
      statusText.textContent=item[0]; progress.style.width=item[1]+'%';
      if(data.status==='completed'){
        await render();
        statusText.textContent='Analysis completed. Opening contract...';
        setTimeout(()=>location.href=`/pages/contract.html?id=${contractId}`,500);
        return;
      }
      if(data.status==='failed') throw new Error(data.error||'Contract analysis failed');
      await new Promise(resolve=>setTimeout(resolve,2000));
    }
    throw new Error('Analysis is taking longer than expected. Refresh the page to check its status.');
  }

  document.querySelector('#upload').onclick=async()=>{
    const f=document.querySelector('#file').files[0];
    if(!f)return alert('Choose a file first');
    const allowed=['application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','text/plain'];
    const ext=/\.([^.]+)$/.exec(f.name)?.[1]?.toLowerCase();
    if(!['pdf','docx','txt'].includes(ext))return alert('Use a PDF, DOCX or TXT file.');
    if(f.size>25*1024*1024)return alert('File is larger than 25 MB.');
    const btn=document.querySelector('#upload'), processing=document.querySelector('#uploadProcessing'), status=document.querySelector('#uploadStatus'), progress=document.querySelector('#uploadProgress');
    btn.disabled=true; btn.textContent='Uploading…'; processing.classList.add('active'); status.textContent='Uploading document…'; progress.style.width='8%';
    try{
      const fd=new FormData(); fd.append('file',f);
      const r=await fetch('/api/contracts/upload',{method:'POST',body:fd});
      let data={}; try{data=await r.json()}catch{}
      if(!r.ok){
        const detail=data.detail || data.message || `Server returned HTTP ${r.status}`;
        throw new Error(`Upload failed (${r.status}): ${detail}`);
      }
      status.textContent='Upload complete. Starting background analysis…'; progress.style.width='15%';
      await render();
      await monitorContract(data.id);
    }catch(e){
      console.error(e); status.textContent=e.message; progress.style.width='100%';
      processing.classList.add('error'); await render();
      setTimeout(()=>processing.classList.remove('active','error'),5000);
    }finally{btn.disabled=false;btn.textContent='Analyze contract';}
  };
  render().catch(e=>{document.querySelector('#list').innerHTML=`<div class="card"><div class="notice">Could not load contracts: ${esc(e.message)}</div></div>`});
}
load();
