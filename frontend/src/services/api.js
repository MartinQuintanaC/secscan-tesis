const API_BASE = "http://127.0.0.1:8000";

export async function triggerN8nScan(targetIp) {
  const res = await fetch(`${API_BASE}/api/trigger-scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_ip: targetIp }),
  });
  return res.json();
}

export async function deepScan(ip) {
  const res = await fetch(`${API_BASE}/api/deep-scan/${ip}`, {
    method: "POST",
  });
  return res.json();
}

export async function getDevices() {
  const res = await fetch(`${API_BASE}/api/devices`);
  return res.json();
}

export async function getVulnerabilities() {
  const res = await fetch(`${API_BASE}/api/vulnerabilities`);
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function installNmap() {
  const res = await fetch(`${API_BASE}/api/install-nmap`, {
    method: "POST"
  });
  return res.json();
}
