const A='/api';
async function api(p,o={}){let r=await fetch(A+p,o);if(!r.ok)throw Error(await r.text());return r.json()}
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const fmt=d=>d?new Date(d+'T00:00:00').toLocaleDateString(undefined,{day:'2-digit',month:'short',year:'numeric'}):'—';
function shell(active,title,sub){
  const user = (window.Auth && Auth.user()) || {email:"demo@contractlens.ai",name:"Demo User"};
  document.body.innerHTML=`<div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="logo">CL</div>
        <div><b>ContractLens</b><small>Contract intelligence</small></div>
      </div>
      <nav class="nav">
        <a class="${active==='dashboard'?'active':''}" href="/pages/dashboard.html">⌂ Dashboard</a>
        <a class="${active==='contracts'?'active':''}" href="/pages/contracts.html">▣ Contracts</a>
        <a class="${active==='obligations'?'active':''}" href="/pages/obligations.html">◈ Obligations</a>
        <a class="${active==='compare'?'active':''}" href="/pages/compare.html">⇄ Compare</a>
        <a class="${active==='chat'?'active':''}" href="/pages/chat.html">✦ Ask AI</a>
        <a class="${active==='alerts'?'active':''}" href="/pages/alerts.html">◉ Alerts</a>
      </nav>
      <div class="sidebar-user">
        <div class="avatar">${esc((user.name||"D").slice(0,1).toUpperCase())}</div>
        <div class="user-meta">
          <b>${esc(user.name||"Demo User")}</b>
          <small>${esc(user.email||"")}</small>
        </div>
        <button class="logout-icon" id="logoutBtn" title="Log out">↪</button>
      </div>
    </aside>
    <main class="main">
      <div class="topbar">
        <div class="title"><h1>${title}</h1><p>${sub}</p></div>
        <div class="top-actions">
          <div class="top-user"><span>${esc(user.email||"")}</span><button class="btn secondary" id="logoutTop">Log out</button></div>
          <a class="btn" href="/pages/contracts.html">+ Upload contract</a>
        </div>
      </div>
      <div id="content"></div>
    </main>
  </div>`;
  const logout = () => Auth.logout();
  document.getElementById("logoutBtn")?.addEventListener("click", logout);
  document.getElementById("logoutTop")?.addEventListener("click", logout);
}
