const API_BASE = "http://127.0.0.1:8000";

const getHeaders = (token) => ({
  "Content-Type": "application/json",
  ...(token ? { "Authorization": `Bearer ${token}` } : {})
});

export async function triggerN8nScan(targetIp, token, scanId) {
  const res = await fetch(`${API_BASE}/api/trigger-scan`, {
    method: "POST",
    headers: getHeaders(token),
    body: JSON.stringify({ 
      target_ip: targetIp,
      scan_id: scanId 
    }),
  });
  return res.json();
}


export async function deepScan(ip, token) {
  const res = await fetch(`${API_BASE}/api/deep-scan/${ip}`, {
    method: "POST",
    headers: getHeaders(token),
  });
  return res.json();
}

export async function getDevices(token) {
  const res = await fetch(`${API_BASE}/api/devices`, {
    headers: getHeaders(token),
  });
  return res.json();
}

export async function getVulnerabilities(token) {
  const res = await fetch(`${API_BASE}/api/vulnerabilities`, {
    headers: getHeaders(token),
  });
  return res.json();
}

export async function checkHealth(token) {
  const res = await fetch(`${API_BASE}/api/health`, {
    headers: getHeaders(token),
  });
  return res.json();
}

export async function installNmap(token) {
  const res = await fetch(`${API_BASE}/api/install-nmap`, {
    method: "POST",
    headers: getHeaders(token),
  });
  return res.json();
}

export async function getScanHistory(token) {
  const res = await fetch(`${API_BASE}/api/history`, {
    headers: getHeaders(token),
  });
  return res.json();
}

export async function getScanDetails(scanId, token) {
  const res = await fetch(`${API_BASE}/api/history/${scanId}`, {
    headers: getHeaders(token),
  });
  return res.json();
}

export async function getScanDevices(scanId, token) {
  const res = await fetch(`${API_BASE}/api/history/${scanId}/devices`, {
    headers: getHeaders(token),
  });
  return res.json();
}
