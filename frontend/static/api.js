const BASE = "http://localhost:8000";

function getToken() {
  return localStorage.getItem("access_token");
}

function authHeaders() {
  return {
    "Authorization": `Bearer ${getToken()}`,
    "Content-Type": "application/x-www-form-urlencoded"
  };
}

export async function login(username, password) {
  const res = await fetch(`${BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username, password })
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  localStorage.setItem("access_token", data.access_token);
}

export async function register(username, password) {
  const res = await fetch(`${BASE}/api/register`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username, password })
  });
  if (!res.ok) throw new Error("Registration failed");
  const data = await res.json();
  localStorage.setItem("access_token", data.access_token);
}

export function logout() {
  localStorage.removeItem("access_token");
  window.location.href = "/login.html";
}

export async function getTasks() {
  const res = await fetch(`${BASE}/api/tasks`, { headers: authHeaders() });
  if (res.status === 401) { logout(); return; }
  return res.json();
}

export async function addTask(title) {
  const res = await fetch(`${BASE}/api/tasks`, {
    method: "POST",
    headers: authHeaders(),
    body: new URLSearchParams({ title })
  });
  return res.json();
}

export async function updateTaskTitle(id, title) {
    const res = await fetch(`${BASE}/api/tasks/${id}/title`, {
        method: "PATCH",
        headers: authHeaders(),
        body: new URLSearchParams({ title })
    });
    if (!res.ok) throw new Error("Failed to update task");
    return res.json();
}

export async function toggleTask(id) {
    const res = await fetch(`${BASE}/api/tasks/${id}/toggle`, {
        method: "PATCH",
        headers: authHeaders()
    });
    if (!res.ok) throw new Error("Failed to toggle task");
    return res.json();
}

export async function deleteTask(id) {
  await fetch(`${BASE}/api/tasks/${id}`, {
    method: "DELETE",
    headers: authHeaders()
  });
}