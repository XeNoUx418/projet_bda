import { api } from "./api.js";
const $ = (id)=>document.getElementById(id);

const msg = $("msg");
const rowsEl = $("rows");

function setMsg(t,bad=false){
  msg.textContent=t;
  msg.style.borderColor = bad ? "rgba(239,68,68,.35)" : "rgba(255,255,255,.18)";
  msg.style.background = bad ? "rgba(239,68,68,.12)" : "rgba(255,255,255,.06)";
}

function rowHTML(p){
  const has = Number(p.has_planning) === 1;
  return `
    <tr>
      <td>${p.id_periode}</td>
      <td>${p.description ?? ""}</td>
      <td>${(p.date_debut ?? "").slice(0,10)}</td>
      <td>${(p.date_fin ?? "").slice(0,10)}</td>
      <td>${has ? "Yes" : "—"}</td>
      <td style="display:flex; gap:8px; flex-wrap:wrap;">
        <button class="btn small" data-act="preview" data-id="${p.id_periode}">Preview</button>
        <button class="btn small" data-act="conflicts" data-id="${p.id_periode}">Conflicts</button>
        <button class="btn small primary" data-act="generate" data-id="${p.id_periode}">Generate</button>
        <button class="btn small danger" data-act="delete" data-id="${p.id_periode}">Delete planning</button>
      </td>
    </tr>
  `;
}

async function refresh(){
  try{
    setMsg("Loading periods…");
    const periods = await api.periodes();
    rowsEl.innerHTML = periods.map(rowHTML).join("");
    setMsg(`Loaded ${periods.length} periods ✅`);
  }catch(e){
    rowsEl.innerHTML="";
    setMsg(e.message,true);
  }
}

$("create").addEventListener("click", async ()=>{
  try{
    const date_debut = $("start").value;
    const date_fin = $("end").value;
    const description = $("desc").value || "Session d'examen";
    if(!date_debut || !date_fin) throw new Error("Start/End dates are required.");
    setMsg("Creating period…");
    const res = await api.createPeriode(date_debut, date_fin, description);
    setMsg(`Created period #${res.id_periode} ✅`);
    await refresh();
  }catch(e){
    setMsg(e.message,true);
  }
});

$("refresh").addEventListener("click", refresh);

rowsEl.addEventListener("click", async (ev)=>{
  const btn = ev.target.closest("button");
  if(!btn) return;
  const act = btn.dataset.act;
  const id = Number(btn.dataset.id);

  try{
    if(act === "generate"){
      setMsg(`Generating planning for period ${id}… (may take time)`);
      const r = await api.generatePlanning(id);
      console.log("Generate logs:", r.logs);
      setMsg(`Generated ✅ in ${r.elapsed_seconds}s`);
    }
    if(act === "delete"){
      setMsg(`Deleting planning for period ${id}…`);
      await api.deletePlanning(id);
      setMsg("Deleted ✅");
    }
    if(act === "preview"){
      setMsg(`Loading preview for period ${id}…`);
      const r = await api.previewPlanning(id, 50);
      console.table(r);
      setMsg(`Preview loaded (${r.length} rows) ✅ (check console)`);
    }
    if(act === "conflicts"){
      setMsg(`Checking conflicts for period ${id}…`);
      const r = await api.roomConflicts(id);
      console.table(r);
      setMsg(`Conflicts loaded (${r.length} rows) ✅ (check console)`);
    }
    await refresh();
  }catch(e){
    setMsg(e.message,true);
  }
});

refresh();
