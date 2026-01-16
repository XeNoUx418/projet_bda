import { API_BASE } from "./config.js";

async function request(path, { method = "GET", params, body } = {}) {
  const url = new URL(`${API_BASE}${path}`);

  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
  }

  const res = await fetch(url.toString(), {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok || data.ok === false) {
    const msg = data?.error || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data.data;
}

export const api = {
  health: () => request("/health"),
  departements: () => request("/departements"),
  formations: (dept_id) => request("/formations", { params: { dept_id } }),
  annees: (formation_id) => request("/annees", { params: { formation_id } }),
  sessions: (formation_id, annee) => request("/sessions", { params: { formation_id, annee } }),
  schedule: (formation_id, annee, periode_id) =>
    request("/schedule", { params: { formation_id, annee, periode_id } }),

  studentSchedule: (student_id, periode_id) =>
    request("/student_schedule", { params: { student_id, periode_id } }),

  professeurs: () => request("/professeurs"),
  profSchedule: (prof_id, date_start, date_end) =>
    request("/prof_schedule", { params: { prof_id, date_start, date_end } }),

  periodes: () => request("/periodes"),
  createPeriode: (date_debut, date_fin, description) =>
    request("/periodes", { method: "POST", body: { date_debut, date_fin, description } }),
  generatePlanning: (pid) => request(`/periodes/${pid}/generate_planning`, { method: "POST" }),
  deletePlanning: (pid) => request(`/periodes/${pid}/planning`, { method: "DELETE" }),
  previewPlanning: (pid, limit = 100) => request(`/periodes/${pid}/preview`, { params: { limit } }),
  roomConflicts: (pid) => request(`/periodes/${pid}/conflicts/rooms`),

  dashKpis: (periode_id) => request("/dashboard/kpis", { params: { periode_id } }),
  dashRoomDist: (periode_id) => request("/dashboard/room_distribution", { params: { periode_id } }),
  dashTopRooms: (periode_id) => request("/dashboard/top_rooms", { params: { periode_id } }),
  dashProfLoad: (periode_id) => request("/dashboard/prof_load", { params: { periode_id } }),
  dashProfConflicts: (periode_id) => request("/dashboard/prof_conflicts", { params: { periode_id } }),
};
