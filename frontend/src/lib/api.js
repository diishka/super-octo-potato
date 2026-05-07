const API_BASE = import.meta.env.VITE_API_BASE || "";

function extractMessage(payload, fallbackMessage) {
  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }

  if (payload?.detail) {
    return payload.detail;
  }

  if (payload && typeof payload === "object") {
    const [firstKey] = Object.keys(payload);
    if (firstKey) {
      const value = payload[firstKey];

      if (Array.isArray(value)) {
        return value[0];
      }

      if (typeof value === "string") {
        return value;
      }
    }
  }

  return fallbackMessage;
}

export async function apiRequest(
  path,
  { method = "GET", body, token, headers = {} } = {}
) {
  // 🔥 ВАЖНО: token добавляем сразу сюда
  const finalHeaders = {
    ...headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const options = {
    method,
    headers: finalHeaders,
  };

  if (body !== undefined) {
    finalHeaders["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, options);

  const contentType = response.headers.get("content-type") || "";

  let payload = null;

  if (response.status !== 204) {
    payload = contentType.includes("application/json")
      ? await response.json()
      : await response.text();
  }

  if (!response.ok) {
    throw new Error(
      extractMessage(payload, `Request failed with status ${response.status}`)
    );
  }

  return payload;
}