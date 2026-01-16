import { api } from "./api.js";
const $ = (id)=>document.getElementById(id);
const periodeSel = $("periode");
const refreshBtn = $("refresh");

function fillSelect(sel, items, getVal, getLabel){
  sel.innerHTML = "";
  items.forEach(it=>{
    const opt=document.createElement("option");
    opt.value=getVal(it);
    opt.textContent=getLabel(it);
    sel.appendChild(opt);
  });
}

let roomChart = null;
let groupChart = null;

function setMsg(t, bad=false){
  const msg = $("msg");
  msg.textContent = t;
  msg.className = bad ? "alert-box bad" : "alert-box good";
}

function renderConf(rows){
  const confEl = $("conf");
  if(!confEl) return;

  confEl.innerHTML = "";

  if(!rows || rows.length === 0){
    confEl.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-success fw-bold">
          ✅ Aucun conflit détecté
        </td>
      </tr>`;
    return;
  }

  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.classList.add("table-danger");

    tr.innerHTML = `
      <td class="fw-bold">${r.Professor}</td>
      <td>${new Date(r.date).toLocaleDateString()}</td>
      <td>${r.Start}</td>
      <td>
        <span class="badge bg-danger">${r.Assignments}</span>
      </td>
      <td class="small text-muted">
        ${r.Details || "—"}
      </td>
    `;
    confEl.appendChild(tr);
  });
}


function renderTopRooms(rows){
  const tbody = $("topRooms");
  tbody.innerHTML = "";
  
  if(!rows || rows.length === 0) {
    tbody.innerHTML = "<tr><td colspan='3' class='text-center text-muted py-3'>Aucune donnée</td></tr>";
    return;
  }
  
  // Sort by sessions descending
  const sorted = rows.sort((a, b) => b.sessions - a.sessions);
  
  sorted.forEach((r, index) => {
    const tr = document.createElement("tr");
    const typeIcon = r.type === "salle" ? "🏠" : "🏛️";
    const typeClass = r.type === "amphi" ? "bg-info" : "bg-secondary";
    
    // Highlight top 3
    if(index < 4) {
      tr.classList.add("table-warning");
    }
    
    tr.innerHTML = `
      <td class="ps-4">${typeIcon} ${r.nom}</td>
      <td><span class="badge ${typeClass}">${r.type}</span></td>
      <td><strong>${r.sessions}</strong></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderProfLoad(rows){
  const tbody = $("profLoad");
  if(!tbody) return;
  
  tbody.innerHTML = "";
  if(!rows || rows.length === 0) {
    tbody.innerHTML = "<tr><td colspan='3' class='text-center text-muted py-3'>Aucune donnée</td></tr>";
    return;
  }

  // Sort by total_surveillances descending (most busy first)
  const sorted = rows.sort((a,b) => b.total_surveillances - a.total_surveillances);

  sorted.forEach((r, index) => {
    const tr = document.createElement("tr");
    
    // Highlight top 5 most loaded professors
    if(index < 10) {
      tr.classList.add("table-warning");
    }
    
    // Add badge color based on workload
    let badge = "";
    if(r.total_surveillances >= 100) {
      badge = '<span class="badge bg-danger ms-1">Élevé</span>';
    } else if(r.total_surveillances >= 80) {
      badge = '<span class="badge bg-warning text-dark ms-1">Moyen</span>';
    } else if(r.total_surveillances >= 50) {
      badge = '<span class="badge bg-success ms-1">Normal</span>';
    }
    
    tr.innerHTML = `
      <td class="ps-4"><strong>${r.nom}</strong></td>
      <td>${r.Dept}</td>
      <td><strong>${r.total_surveillances}</strong> ${badge}</td>
    `;
    tbody.appendChild(tr);
  });
}

function createRoomChart(data){
  if(!data || data.length === 0) return;
  
  if(roomChart) roomChart.destroy();
  
  const types = data.map(d => d.type || "Unknown");
  const counts = data.map(d => d.usage_count || 0);
  const colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];
  
  const ctx = $("roomChart").getContext("2d");
  roomChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: types,
      datasets: [{
        data: counts,
        backgroundColor: colors.slice(0, types.length),
        borderColor: "#ffffff",
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { size: 12 }, padding: 15 }
        }
      }
    }
  });
}

function createGroupChart(totalPlanned, mergedCount, splitCount){
  if(!totalPlanned) return;
  
  if(groupChart) groupChart.destroy();
  
  const regular = totalPlanned - mergedCount - splitCount;
  
  const ctx = $("groupChart").getContext("2d");
  groupChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Merged\n(Amphi)", "Split"],
      datasets: [{
        label: "Count",
        data: [mergedCount, splitCount],
        backgroundColor: ["#10b981", "#06b6d4"],
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } }
      }
    }
  });
}

async function loadDashboard(periode_id){
  try {
    setMsg("Loading analytics…");

    // KPIs
    const kpis = await api.dashKpis(periode_id);
    const { total_planned, expected_slots, merged_count, split_count, total_profs, total_students } = kpis;
    
    $("k1").textContent = total_planned;
    $("k2").textContent = merged_count;
    $("k3").textContent = split_count;
    $("k4").textContent = total_profs;
    $("k5").textContent = total_students;
    
    // Percentages
    const success_pct = expected_slots > 0 ? Math.round((total_planned / expected_slots) * 100) : 0;
    const merged_pct = total_planned > 0 ? Math.round((merged_count / total_planned) * 100) : 0;
    const split_pct = total_planned > 0 ? Math.round((split_count / total_planned) * 100) : 0;
    
    $("k1-pct").textContent = success_pct + "%";
    $("k2-pct").textContent = merged_pct + "%";
    $("k3-pct").textContent = split_pct + "%";
    
    // Room distribution chart
    const roomDist = await api.dashRoomDist(periode_id);
    createRoomChart(roomDist);
    
    // Group handling chart
    createGroupChart(total_planned, merged_count, split_count);
    
    // Top rooms
    const topRooms = await api.dashTopRooms(periode_id);
    renderTopRooms(topRooms);
    
    // Prof load
    const profLoad = await api.dashProfLoad(periode_id);
    renderProfLoad(profLoad);
    
    // Conflicts
    const conflicts = await api.dashProfConflicts(periode_id);
    renderConf(conflicts);
    
    if(conflicts.length === 0){
      setMsg("✅ No professor overlaps detected. System is optimal.", false);
    } else {
      setMsg(`⚠️ ${conflicts.length} conflict(s) detected. Review immediately.`, true);
    }
    
  } catch(e) {
    setMsg("Error: " + e.message, true);
    console.error(e);
  }
}

(async function init(){
  try {
    // Get periode_id from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const urlPeriodeId = urlParams.get('periode_id');
    
    // load periodes
    const periodes = await api.periodes();
    fillSelect(periodeSel, periodes, p=>p.id_periode, p=>{
      // Create a label from description and dates
      const start = p.date_debut ? new Date(p.date_debut).toLocaleDateString('fr-FR') : '';
      const end = p.date_fin ? new Date(p.date_fin).toLocaleDateString('fr-FR') : '';
      return `${p.description || 'Période ' + p.id_periode} (${start} → ${end})`;
    });
    
    // Set the selected period from URL or use first period
    if(urlPeriodeId){
      periodeSel.value = urlPeriodeId;
    }
    
    const periode_id = Number(periodeSel.value) || undefined;
    
    // Load dashboard data
    await loadDashboard(periode_id);
    
  } catch(e) {
    setMsg("Error: " + e.message, true);
    console.error(e);
  }
})();

// refresh handler
refreshBtn?.addEventListener('click', ()=>{
  window.location.reload();
});

// period change handler - update URL and reload data
periodeSel?.addEventListener('change', ()=>{
  const periode_id = periodeSel.value;
  // Update URL with selected period
  const url = new URL(window.location);
  url.searchParams.set('periode_id', periode_id);
  window.history.pushState({}, '', url);
  
  // Reload dashboard data
  loadDashboard(Number(periode_id) || undefined);
});