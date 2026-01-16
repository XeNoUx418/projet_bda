import { api } from "./api.js";

const $ = (id) => document.getElementById(id);
const deptSel = $("dept");
const formSel = $("formation");
const anneeSel = $("annee");
const periodeSel = $("periode");
const msg = $("msg");
const tablesContainer = document.getElementById("tables-container");
const studentIdInput = document.getElementById("student_id");
const loadPersonalBtn = document.getElementById("load_personal");
let lastRows = [];

function setMsg(text, bad=false){
  msg.textContent = text;
  msg.style.borderColor = bad ? "rgba(239,68,68,.35)" : "rgba(255,255,255,.18)";
  msg.style.background = bad ? "rgba(239,68,68,.12)" : "rgba(255,255,255,.06)";
}

function fillSelect(sel, items, getVal, getLabel){
  sel.innerHTML = "";
  items.forEach(it=>{
    const opt=document.createElement("option");
    opt.value=getVal(it);
    opt.textContent=getLabel(it);
    sel.appendChild(opt);
  });
}

function renderGroupTables(groupsData) {
  tablesContainer.innerHTML = "";

  // Check if groupsData is empty
  if (!groupsData || (Array.isArray(groupsData) && groupsData.length === 0) || 
      (typeof groupsData === 'object' && Object.keys(groupsData).length === 0)) {
    tablesContainer.innerHTML = '<div class="alert alert-info">Aucun examen trouvé.</div>';
    return;
  }

  // Handle both array and object formats
  const groups = Array.isArray(groupsData) ? groupsData : Object.values(groupsData);

  groups.forEach(group => {
    const card = document.createElement("div");
    card.className = "card mb-3";

    card.innerHTML = `
      <div class="card-header small fw-bold">
        Groupe: ${group.label || group.FullGroupLabel || 'Non spécifié'}
        <span class="text-muted small">(${(group.exams || [group]).length} examens)</span>
      </div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-sm mb-0">
            <thead class="table-light small">
              <tr>
                <th>Date</th>
                <th>Début</th>
                <th>Fin</th>
                <th>Module</th>
                <th>Salle</th>
                <th>Bâtiment</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    `;

    const tbody = card.querySelector("tbody");

    // Handle both formats: group.exams array or single exam object
    const exams = group.exams || [group];
    
    exams.forEach(exam => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${exam.DateLabel || exam.dateLabel || ""}</td>
        <td>${exam.Start || exam.start || ""}</td>
        <td>${exam.End || exam.end || ""}</td>
        <td>${exam.Module || exam.module || ""}</td>
        <td>${exam.Room || exam.room || ""}</td>
        <td>${exam.Building || exam.building || ""}</td>
      `;
      tbody.appendChild(tr);
    });

    tablesContainer.appendChild(card);
  });
}

function convertPersonalScheduleToGroups(rows) {
  /**
   * Convert flat array from studentSchedule API to grouped format
   * Groups exams by student's group
   */
  if (!rows || rows.length === 0) {
    return {};
  }

  const grouped = {};

  rows.forEach(exam => {
    // Use FullGroupLabel as the key, or fall back to GroupCode
    const groupKey = exam.FullGroupLabel || exam.GroupCode || 'Mon Groupe';
    
    if (!grouped[groupKey]) {
      grouped[groupKey] = {
        label: groupKey,
        type: exam.SplitPart ? 'split' : 'normal',
        exams: []
      };
    }

    grouped[groupKey].exams.push({
      dateLabel: exam.DateLabel,
      start: exam.Start,
      end: exam.End,
      module: exam.Module,
      room: exam.Room,
      building: exam.Building,
      date: exam.exam_date
    });
  });

  // Sort exams within each group by date and time
  Object.values(grouped).forEach(group => {
    group.exams.sort((a, b) => {
      if (a.date !== b.date) return a.date.localeCompare(b.date);
      return a.start.localeCompare(b.start);
    });
  });

  return grouped;
}

async function loadDepts(){
  const depts = await api.departements();
  fillSelect(deptSel, depts, d=>d.id_dept, d=>d.nom);
}

async function loadFormations(){
  const dept_id = Number(deptSel.value);
  const forms = await api.formations(dept_id);
  fillSelect(formSel, forms, f=>f.id_formation, f=>f.nom);
}

async function loadAnnees(){
  const formation_id = Number(formSel.value);
  const years = await api.annees(formation_id);
  fillSelect(anneeSel, years, y=>y, y=>y);
}

async function loadPeriodes(){
  const formation_id = Number(formSel.value);
  const annee = anneeSel.value;
  const sessions = await api.sessions(formation_id, annee);
  fillSelect(periodeSel, sessions, s=>s.id_periode, s=>s.label);
}

function toCSV(rows){
  // Handle both array and object formats
  const dataRows = Array.isArray(rows) ? rows : Object.values(rows).flatMap(g => 
    (g.exams || []).map(e => ({
      DateLabel: e.dateLabel,
      Start: e.start,
      End: e.end,
      Module: e.module,
      Room: e.room,
      Building: e.building,
      FullGroupLabel: g.label
    }))
  );

  const cols = ["DateLabel","Start","End","Module","Room","Building","FullGroupLabel"];
  const head = cols.join(",");
  const body = dataRows.map(r => cols.map(c => `"${String(r[c] ?? "").replaceAll('"','""')}"`).join(",")).join("\n");
  return head + "\n" + body;
}

$("load").addEventListener("click", async ()=>{
  try{
    setMsg("Loading schedule…");
    const formation_id = Number(formSel.value);
    const annee = anneeSel.value;
    const periode_id = Number(periodeSel.value);

    const rows = await api.schedule(formation_id, annee, periode_id);
    lastRows = rows;
    renderGroupTables(rows);
    
    // Count total exams
    const totalExams = Object.values(rows).reduce((sum, group) => sum + group.exams.length, 0);
    setMsg(`Loaded ${Object.keys(rows).length} groups, ${totalExams} exams`);
  }catch(e){
    lastRows = [];
    renderGroupTables({});
    setMsg(e.message, true);
  }
});

$("export").addEventListener("click", ()=>{
  if(!lastRows || (Array.isArray(lastRows) && lastRows.length === 0) || 
     (typeof lastRows === 'object' && Object.keys(lastRows).length === 0)) {
    return setMsg("Nothing to export.", true);
  }
  
  const csv = toCSV(lastRows);
  const blob = new Blob([csv], {type:"text/csv;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "student_schedule.csv";
  a.click();
  URL.revokeObjectURL(a.href);
});

async function init(){
  try{
    setMsg("Loading lists…");
    await loadDepts();
    await loadFormations();
    await loadAnnees();
    await loadPeriodes();
    setMsg("");
  }catch(e){
    setMsg(e.message, true);
  }
}

deptSel.addEventListener("change", async ()=>{
  try{
    await loadFormations(); await loadAnnees(); await loadPeriodes();
    setMsg("");
  }catch(e){ setMsg(e.message, true); }
});

formSel.addEventListener("change", async ()=>{
  try{
    await loadAnnees(); await loadPeriodes();
    setMsg("");
  }catch(e){ setMsg(e.message, true); }
});

anneeSel.addEventListener("change", async ()=>{
  try{
    await loadPeriodes();
    setMsg("");
  }catch(e){ setMsg(e.message, true); }
});

loadPersonalBtn.addEventListener('click', async () => {
  const student_id = Number(studentIdInput.value);
  const periode_id = Number(periodeSel.value);
  
  if (!student_id) {
    return setMsg('Veuillez saisir un ID étudiant', true);
  }
  if (!periode_id) {
    return setMsg('Veuillez sélectionner une session', true);
  }

  try {
    setMsg('Chargement de votre emploi du temps…');
    
    // Get personal schedule (returns array)
    const rows = await api.studentSchedule(student_id, periode_id);
    
    // Convert to grouped format for display
    const groupedData = convertPersonalScheduleToGroups(rows);
    
    lastRows = rows; // Keep original for CSV export
    renderGroupTables(groupedData);
    
    setMsg(`Loaded ${rows.length} exams`);
  } catch (e) {
    lastRows = [];
    renderGroupTables({});
    setMsg(e.message, true);
  }
});

init();