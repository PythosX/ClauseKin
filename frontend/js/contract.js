async function load(){
  let id=new URLSearchParams(location.search).get('id');
  shell('contracts','Contract details','Source-backed contract intelligence.');
  if(!id){
    document.querySelector('#content').innerHTML='<div class="card"><p class="muted">No contract selected.</p></div>';
    return;
  }

  async function fetchContract(){
    return api('/contracts/'+id);
  }

  try{
    let c=await fetchContract();
    if(c.status && c.status!=='completed'){
      document.querySelector('#content').innerHTML=`
        <div class="card hero">
          <div class="processing-spinner"></div>
          <h2>Contract is being analyzed</h2>
          <p class="muted">Current status: ${esc(c.status)}</p>
          <p class="muted">This page will refresh automatically when analysis is complete.</p>
        </div>`;
      const poll=async()=>{
        try{
          const r=await fetch('/api/contracts/'+id+'/status');
          const s=await r.json();
          if(s.status==='completed') return location.reload();
          if(s.status==='failed'){
            document.querySelector('#content').innerHTML=`<div class="card"><h2>Analysis failed</h2><p class="muted">${esc(s.error||'Unknown error')}</p></div>`;
            return;
          }
        }catch{}
        setTimeout(poll,2000);
      };
      poll();
      return;
    }

    document.querySelector('#content').innerHTML=`
      <div class="grid two">
        <div class="card"><div class="kpi">CONTRACT</div><h2>${esc(c.name)}</h2><p class="muted">${esc(c.filename)}</p>
          <div class="grid three">
            <div><div class="kpi">Effective</div><b>${fmt(c.effective)}</b></div>
            <div><div class="kpi">Expires</div><b>${fmt(c.expires)}</b></div>
            <div><div class="kpi">Parties</div><b>${c.parties.length}</b></div>
          </div>
        </div>
        <div class="card"><h3>AI summary</h3><p>${esc(c.summary)}</p></div>
      </div>
      <div class="grid three" style="margin-top:16px">
        <div class="card"><div class="kpi">PAYMENT</div><p>${esc(c.payment)}</p></div>
        <div class="card"><div class="kpi">RENEWAL</div><p>${esc(c.renewal)}</p></div>
        <div class="card"><div class="kpi">TERMINATION</div><p>${esc(c.termination)}</p></div>
      </div>
      <div class="grid two" style="margin-top:16px">
        <div class="card"><h3>Obligations</h3>${c.obligations.map(o=>`
          <div class="source"><b>${esc(o.description)}</b>
          <div class="kpi">${esc(o.party)} · ${fmt(o.deadline)} · ${esc(o.frequency)}</div>
          <span class="badge ${o.risk.toLowerCase()}">${o.risk} risk</span>
          <div class="kpi">§${esc(o.section)} · Page ${o.page}</div></div>`).join('')||'<p class="muted">No obligations extracted.</p>'}</div>
        <div class="card"><h3>Indexed clauses</h3>${c.clauses.map(x=>`
          <div class="source"><b>${esc(x.type)} · §${esc(x.section)}</b><p>${esc(x.text)}</p><div class="kpi">Page ${x.page}</div></div>`).join('')||'<p class="muted">No clauses indexed.</p>'}</div>
      </div>`;
  }catch(err){
    document.querySelector('#content').innerHTML=`<div class="card"><h2>Unable to load contract</h2><p class="muted">${esc(err.message)}</p></div>`;
  }
}
load();
