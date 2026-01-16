import { api } from "./api.js";
const $ = (id)=>document.getElementById(id);

const profSel = $("prof");
const msg = $("msg");
const rowsEl = $("rows");
let lastRows = [];

function setMsg(t,bad=false){
  msg.textContent=t;
  msg.style.borderColor = bad ? "rgba(239,68,68,.35)" : "rgba(255,255,255,.18)";
  msg.style.background = bad ? "rgba(239,68,68,.12)" : "rgba(255,255,255,.06)";
}
function fillSelect(sel, items){
  sel.innerHTML="";
  items.forEach(p=>{
    const opt=document.createElement("option");
    opt.value=p.id_prof;
    opt.textContent=`${p.nom} (${p.specialite})`;
    sel.appendChild(opt);
  });
}
function render(rows){
  rowsEl.innerHTML="";
  rows.forEach(r=>{
    const tr=document.createElement("tr");
    tr.innerHTML = `
      <td>${r.DateLabel ?? ""}</td>
      <td>${r.Start ?? ""}</td>
      <td>${r.End ?? ""}</td>
      <td>${r.Module ?? ""}</td>
      <td>${r.Room ?? ""}</td>
      <td>${r.Building ?? ""}</td>
      <td>${r.GroupLabel ?? ""}</td>
    `;
    rowsEl.appendChild(tr);
  });
}
function toCSV(rows){
  const cols = ["DateLabel","Start","End","Module","Room","Building","GroupLabel"];
  const head = cols.join(",");
  const body = rows.map(r => cols.map(c => `"${String(r[c] ?? "").replaceAll('"','""')}"`).join(",")).join("\n");
  return head + "\n" + body;
}

$("load").addEventListener("click", async ()=>{
  try{
    setMsg("Loading…");
    const prof_id = Number(profSel.value);
    const date_start = $("d1").value;
    const date_end = $("d2").value;
    const rows = await api.profSchedule(prof_id, date_start, date_end);
    lastRows = rows;
    render(rows);
    setMsg(`Loaded ${rows.length} rows `);
  }catch(e){
    lastRows=[];
    render([]);
    setMsg(e.message,true);
  }
});

$("export").addEventListener("click", ()=>{
  if(!lastRows.length) return setMsg("Nothing to export.", true);
  const csv = toCSV(lastRows);
  const blob = new Blob([csv], {type:"text/csv;charset=utf-8"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download="prof_schedule.csv";
  a.click();
  URL.revokeObjectURL(a.href);
});

(async function init(){
  try{
    setMsg("Loading professors…");
    const profs = await api.professeurs();
    fillSelect(profSel, profs);
    setMsg("");
  }catch(e){
    setMsg(e.message,true);
  }
})();
