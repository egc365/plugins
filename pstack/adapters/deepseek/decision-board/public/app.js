const $ = id => document.getElementById(id);
let loading = false;
let refreshSeconds = 15;
const text = (tag, value, className) => { const node = document.createElement(tag); node.textContent = value; if (className) node.className = className; return node; };
const clear = node => { node.replaceChildren(); return node; };
const pill = value => text("span", value, "pill " + value.replace(/[^a-z-]/g, "-"));
const row = (title, detail, status, origin) => { const node = text("article", "", "row"); const head = text("p", ""); head.append(text("strong", title), document.createTextNode(" "), pill(status)); node.append(head, text("p", detail)); if (origin) node.append(text("p", origin, "origin")); return node; };
const card = (item, body) => { const node = text("article", "", "card"); node.append(pill(item.status), text("h3", item.title ?? item.role ?? item.id), text("p", body)); return node; };
function table(items) { const wrap = document.createElement("table"); const head = document.createElement("thead"); const hr = document.createElement("tr"); ["Unit","Track","State","Branch / SHA","Evidence origin"].forEach(v=>hr.append(text("th",v))); head.append(hr); const body=document.createElement("tbody"); items.forEach(item=>{const tr=document.createElement("tr"); [item.id,item.track,item.state,[item.branch,item.sha].filter(Boolean).join(" · ")||"—",item.brief].forEach(v=>tr.append(text("td",v)));body.append(tr)}); wrap.append(head,body); return wrap; }
function render(data) {
  $("title").textContent=data.title; $("observed").textContent="Observed " + new Date(data.observedAt).toLocaleString() + " · auto-refresh " + data.refreshSeconds + "s";
  const summary=clear($("summary")); const banner=text("article","","metric banner "+(data.buildLoopActive?"":"off")); banner.append(text("span",data.buildLoopActive?"BUILD LOOP ACTIVE":"BUILD LOOP NOT CONFIRMED","label"),text("strong",data.overallDone?"Overall accepted":"Acceptance open")); summary.append(banner);
  [[data.requirements.length,"requirements"],[data.workers.filter(x=>x.status==="running").length,"live roles"],[data.ledger.length,"independent verdicts"]].forEach(([n,label])=>{const m=text("article","","metric");m.append(text("strong",String(n)),text("span",String(label),"label"));summary.append(m)});
  const requirements=clear($("requirements")); data.requirements.forEach(item=>{const node=card(item,item.detail);node.append(text("p",item.cardPaths.join(" · "),"origin"));requirements.append(node)});
  const workers=clear($("workers")); data.workers.forEach(item=>{const node=card({...item,title:item.role},item.identity+" · "+item.detail);node.append(text("p","Session "+item.sessionId,"origin"),text("p","Observed "+(item.observedAt?new Date(item.observedAt).toLocaleString():"not observed"),"origin"),text("p","Card "+item.card,"origin"),text("p","Next: "+item.nextAction));workers.append(node)});
  clear($("units")).append(table(data.units));
  const evidence=clear($("evidence")); evidence.append(text("h3","Evidence")); data.evidence.forEach(item=>evidence.append(row(item.label,item.scope,item.status,item.sourcePath))); data.legacyImports.forEach(item=>evidence.append(row(item.label,"Legacy imports cannot establish acceptance",item.status,item.sourcePath)));
  const decisions=clear($("decisions")); decisions.append(text("h3","Decision trail")); if(!data.decisions.length) decisions.append(row("No decisions recorded","The canonical log currently contains only its header","unverified")); data.decisions.slice().reverse().slice(0,12).forEach(item=>decisions.append(row(item.decision,item.why+" → "+item.result,item.phase,item.evidence+" · "+item.sourcePath+" · "+item.ts)));
  const health=clear($("health")); data.health.forEach(item=>health.append(row(item.source,item.detail,item.status)));
  refreshSeconds=data.refreshSeconds;
  summary.append(row("Provenance warning",data.provenanceWarning,"stale"));
}
async function load(){if(loading)return;loading=true;window.clearTimeout(window.__refreshTimer);const button=$("refresh");button.disabled=true;try{const response=await fetch("/api/snapshot",{cache:"no-store"});const data=await response.json();if(!response.ok)throw new Error(data.error??"Snapshot failed");render(data)}catch(error){clear($("summary")).append(row("Board refresh failed",String(error),"error"))}finally{button.disabled=false;loading=false;window.__refreshTimer=window.setTimeout(load,refreshSeconds*1000)}}
$("refresh").addEventListener("click",load);load();
