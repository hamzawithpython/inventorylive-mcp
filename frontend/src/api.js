// Thin API client. Reads base URLs from Vite env.
const API_BASE = import.meta.env.VITE_API_BASE;

export async function login(email, password) {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Invalid email or password");
  return res.json();
}

export async function fetchUnits(token, { projectId, status } = {}) {
  const params = new URLSearchParams();
  if (projectId != null) params.set("project_id", projectId);
  if (status) params.set("status", status);
  const res = await fetch(`${API_BASE}/api/units?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to load units");
  return res.json();
}

export async function fetchProjects(token) {
  const res = await fetch(`${API_BASE}/api/projects`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to load projects");
  return res.json();
}

export async function reserveUnit(token, unitId) {
  const res = await fetch(`${API_BASE}/api/units/${unitId}/reserve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Reserve failed");
  return data;
}
export async function askAI(token, question) {
  const res = await fetch(`${import.meta.env.VITE_API_BASE}/api/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "AI query failed");
  return data; // { answer, tools_used }
}
