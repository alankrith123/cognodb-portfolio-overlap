const API_UNREACHABLE = "Can't reach the database right now.";
const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error(API_UNREACHABLE);
  }

  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }

  if (!response.ok) {
    throw new Error(payload.detail || API_UNREACHABLE);
  }
  return payload;
}

export function getFunds() {
  return request("/api/funds");
}

export function getExposure(fundNames) {
  return request("/api/exposure", {
    method: "POST",
    body: JSON.stringify({ fund_names: fundNames }),
  });
}
