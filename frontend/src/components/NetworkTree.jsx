import { useState, useRef, useCallback, useMemo } from "react";

/* ─── UTILIDADES ────────────────────────────────────────────── */
function isPrivateIP(ip) {
  if (!ip) return false;
  const [a, b] = ip.split(".").map(Number);
  return a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
}
function getSubnetPrefix(ip) { return ip ? ip.split(".").slice(0, 3).join(".") : ""; }
function getScoreColor(s) {
  if (!s || s === 0) return "#00ff88";
  if (s >= 9.0) return "#ff3366";
  if (s >= 7.0) return "#ff8c00";
  if (s >= 4.0) return "#ffd000";
  return "#00ff88";
}
function getRiskLabel(s) {
  if (!s || s === 0) return "SEGURO";
  if (s >= 9.0) return "CRÍTICO";
  if (s >= 7.0) return "ALTO";
  if (s >= 4.0) return "MEDIO";
  return "BAJO";
}
export function getDeviceIcon(d) {
  const f = (d.fabricante || "").toLowerCase();
  const h = (d.hostname || "").toLowerCase();
  
  // Routers / APs / Switches
  if (f.includes("cisco") || f.includes("tp-link") || f.includes("netgear") || f.includes("ubiquiti") || f.includes("mikrotik") || f.includes("d-link") || f.includes("aruba") || h.includes("router") || h.includes("gateway") || h.includes("ap")) return "📡";
  
  // Smartphones & Tablets
  if (f.includes("apple") || h.includes("iphone") || h.includes("ipad")) return "🍎";
  if (f.includes("samsung") || f.includes("motorola") || f.includes("huawei") || f.includes("xiaomi") || f.includes("oppo") || f.includes("vivo") || f.includes("oneplus") || h.includes("android") || h.includes("phone")) return "📱";
  
  // TVs & Media Players
  if (f.includes("roku") || f.includes("lg electronics") || f.includes("tcl") || f.includes("hisense") || h.includes("tv") || h.includes("chromecast") || h.includes("fire") || h.includes("cast")) return "📺";
  
  // Consolas de Videojuegos
  if (f.includes("nintendo") || f.includes("sony interactive") || h.includes("xbox") || h.includes("playstation") || h.includes("switch")) return "🎮";
  
  // Cámaras / Seguridad
  if (f.includes("hikvision") || f.includes("dahua") || f.includes("axis") || h.includes("camera") || h.includes("cam") || h.includes("dvr") || h.includes("nvr")) return "📷";
  
  // Impresoras
  if (f.includes("hewlett") || f.includes("hp") || f.includes("epson") || f.includes("canon") || f.includes("brother") || h.includes("print")) return "🖨️";
  
  // IoT / Domótica
  if (f.includes("tuya") || f.includes("sonoff") || f.includes("philips") || h.includes("smart") || h.includes("iot") || h.includes("home")) return "💡";
  
  // Servidores / NAS
  if (f.includes("synology") || f.includes("qnap") || h.includes("server") || h.includes("srv") || h.includes("nas")) return "🗄️";
  
  // Laptops / PCs (Fallback)
  if (f.includes("dell") || f.includes("lenovo") || f.includes("asus") || f.includes("acer") || f.includes("msi") || h.includes("macbook") || h.includes("pc") || h.includes("desktop") || h.includes("laptop")) return "💻";
  
  // Default Desconocido
  return "💻";
}

/* ─── ÁRBOL HEURÍSTICO ──────────────────────────────────────── */
function buildTree(devices) {
  if (!devices?.length) return null;
  const bySubnet = {};
  devices.forEach(d => {
    const p = getSubnetPrefix(d.ip);
    if (!bySubnet[p]) bySubnet[p] = [];
    bySubnet[p].push(d);
  });
  const subnets = Object.entries(bySubnet)
    .map(([prefix, devs]) => ({
      prefix,
      gateway: devs.find(d => d.ip === `${prefix}.1`) || null,
      devices: devs.filter(d => d.ip !== `${prefix}.1`),
      total: devs.length,
    }))
    .sort((a, b) => b.total - a.total);
  return { main: subnets[0], extensors: subnets.slice(1) };
}

/* ─── CARD: INTERNET ────────────────────────────────────────── */
function InternetCard() {
  return (
    <div className="nt-card nt-card--internet">
      <div className="nt-card-glow" style={{ background: "radial-gradient(circle, rgba(0,212,255,0.3) 0%, transparent 70%)" }} />
      <div className="nt-card-icon">🌐</div>
      <div className="nt-card-label">Internet</div>
      <div className="nt-badge" style={{ background: "rgba(0,212,255,0.15)", color: "#00d4ff", border: "1px solid rgba(0,212,255,0.3)" }}>
        INTERNET
      </div>
    </div>
  );
}

/* ─── CARD: GATEWAY ─────────────────────────────────────────── */
function GatewayCard({ ip, hostname, fabricante }) {
  return (
    <div className="nt-card nt-card--gateway">
      <div className="nt-card-glow" style={{ background: "radial-gradient(circle, rgba(91,127,222,0.35) 0%, transparent 70%)" }} />
      <div className="nt-card-icon">🔵</div>
      <div className="nt-card-label">Router Principal</div>
      {hostname && <div className="nt-card-hostname">{hostname}</div>}
      <div className="nt-card-ip">{ip}</div>
      {fabricante && fabricante !== "Desconocido" && <div className="nt-card-fab">{fabricante}</div>}
      <div className="nt-badge" style={{ background: "rgba(91,127,222,0.2)", color: "#7b9fff", border: "1px solid rgba(91,127,222,0.4)" }}>
        GATEWAY
      </div>
    </div>
  );
}

/* ─── CARD: EXTENSOR ────────────────────────────────────────── */
function ExtensorCard({ ip, hostname, fabricante, deviceCount }) {
  return (
    <div className="nt-card nt-card--extensor">
      <div className="nt-card-glow" style={{ background: "radial-gradient(circle, rgba(243,156,18,0.3) 0%, transparent 70%)" }} />
      <div className="nt-card-icon">📡</div>
      <div className="nt-card-label">{hostname || "Extensor / AP"}</div>
      <div className="nt-card-ip">{ip}</div>
      {fabricante && fabricante !== "Desconocido" && <div className="nt-card-fab">{fabricante}</div>}
      <div style={{ display: "flex", gap: 6, justifyContent: "center", flexWrap: "wrap" }}>
        <div className="nt-badge" style={{ background: "rgba(243,156,18,0.15)", color: "#f39c12", border: "1px solid rgba(243,156,18,0.35)" }}>
          EXTENSOR
        </div>
        <div className="nt-badge" style={{ background: "rgba(255,255,255,0.05)", color: "#7a8ba8" }}>
          {deviceCount} dispositivos
        </div>
      </div>
    </div>
  );
}

/* ─── CARD: DISPOSITIVO ─────────────────────────────────────── */
function DeviceCard({ device }) {
  const [open, setOpen] = useState(false);
  const color = getScoreColor(device.max_score);
  const hasPorts = device.puertos_abiertos?.length > 0;

  return (
    <div className="nt-device-wrapper">
      <div
        className="nt-card nt-card--device"
        style={{ "--risk-color": color, cursor: hasPorts ? "pointer" : "default" }}
        onClick={() => hasPorts && setOpen(!open)}
      >
        <div className="nt-card-glow" style={{ background: `radial-gradient(circle, ${color}22 0%, transparent 70%)` }} />
        <div className="nt-card-icon">{getDeviceIcon(device)}</div>
        <div className="nt-card-ip">{device.ip}</div>
        {device.hostname && device.hostname !== "Caché Local ARP" && (
          <div className="nt-card-hostname">{device.hostname}</div>
        )}
        {device.fabricante && device.fabricante !== "Desconocido" && (
          <div className="nt-card-fab">{device.fabricante}</div>
        )}
        <div style={{ display: "flex", gap: 5, justifyContent: "center", flexWrap: "wrap" }}>
          {device.max_score > 0 ? (
            <div className="nt-badge" style={{ background: `${color}22`, color, border: `1px solid ${color}55`, fontWeight: 800 }}>
              {device.max_score.toFixed(1)} {getRiskLabel(device.max_score)}
            </div>
          ) : (
            <div className="nt-badge" style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.25)" }}>
              ✓ SEGURO
            </div>
          )}
          {device.total_vulnerabilidades > 0 && (
            <div className="nt-badge" style={{ background: "rgba(255,51,102,0.1)", color: "#ff3366", border: "1px solid rgba(255,51,102,0.25)" }}>
              {device.total_vulnerabilidades} CVE
            </div>
          )}
          {device.es_nuevo && (
            <div className="nt-badge" style={{ background: "rgba(255,51,102,0.15)", color: "#ff3366", border: "1px solid #ff336650" }}>
              🚨 NUEVO
            </div>
          )}
          {hasPorts && (
            <div className="nt-badge" style={{ background: "rgba(255,255,255,0.05)", color: "#7a8ba8" }}>
              {device.puertos_abiertos.length} puertos {open ? "▾" : "▸"}
            </div>
          )}
        </div>
      </div>

      {/* Puertos expandibles */}
      {open && hasPorts && (
        <div className="nt-ports-popup">
          {device.puertos_abiertos.map((p, i) => {
            const hasVulns = p.vulnerabilidades?.length > 0;
            const pColor = hasVulns ? getScoreColor(Math.max(...p.vulnerabilidades.map(v => v.score || 0))) : "#4a5568";
            return (
              <div key={i} className="nt-port-row" style={{ "--pc": pColor }}>
                <span className="nt-port-dot" style={{ background: pColor }} />
                <span className="nt-port-num">:{p.puerto}</span>
                <span className="nt-port-svc">{p.servicio}</span>
                {p.version && <span className="nt-port-ver">{p.version}</span>}
                {hasVulns && (
                  <span style={{ marginLeft: "auto", color: pColor, fontSize: 11, fontWeight: 700 }}>
                    ⚠ {p.vulnerabilidades.length} CVE
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── RAMA DEL ÁRBOL (nodo + hijos) ─────────────────────────── */
function OrgBranch({ card, children }) {
  return (
    <li className="nt-branch">
      {card}
      {children && (
        <ul className="nt-children">
          {children}
        </ul>
      )}
    </li>
  );
}

/* ─── COMPONENTE PRINCIPAL ──────────────────────────────────── */
export default function NetworkTree({ devices }) {
  const tree = useMemo(() => buildTree(devices), [devices]);
  const viewportRef = useRef(null);
  const [zoom, setZoom] = useState(1);
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  /* Pan con drag */
  const onMouseDown = useCallback((e) => {
    if (e.target.closest(".nt-card") || e.target.closest(".nt-ports-popup")) return;
    dragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
    e.currentTarget.style.cursor = "grabbing";
  }, []);
  const onMouseMove = useCallback((e) => {
    if (!dragging.current) return;
    const vp = viewportRef.current;
    vp.scrollLeft -= e.clientX - lastPos.current.x;
    vp.scrollTop  -= e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };
  }, []);
  const onMouseUp = useCallback((e) => {
    dragging.current = false;
    e.currentTarget.style.cursor = "grab";
  }, []);

  /* Zoom con rueda */
  const onWheel = useCallback((e) => {
    e.preventDefault();
    setZoom(z => Math.min(Math.max(z * (e.deltaY > 0 ? 0.92 : 1.08), 0.3), 2.5));
  }, []);

  if (!tree) {
    return (
      <div className="nt-empty">
        <div style={{ fontSize: 48 }}>🌐</div>
        <p>No hay datos para construir el árbol.</p>
      </div>
    );
  }

  const { main, extensors } = tree;
  const hasExtensors = extensors.length > 0;

  return (
    <div className="nt-root">
      {/* Leyenda */}
      <div className="nt-legend">
        {[
          { color: "#00d4ff", label: "Internet" },
          { color: "#7b9fff", label: "Gateway" },
          { color: "#f39c12", label: "Extensor / AP" },
          { color: "#00ff88", label: "Seguro" },
          { color: "#ffd000", label: "Riesgo Medio" },
          { color: "#ff3366", label: "Riesgo Crítico" },
        ].map(({ color, label }) => (
          <span key={label} className="nt-legend-item">
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block", flexShrink: 0 }} />
            {label}
          </span>
        ))}
        <span className="nt-legend-item" style={{ marginLeft: "auto", color: "#4a5568", fontSize: 11 }}>
          🖱 Arrastrar para mover · Rueda para zoom
        </span>
      </div>

      {/* Viewport pan/zoom */}
      <div
        className="nt-viewport"
        ref={viewportRef}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
        style={{ cursor: "grab" }}
      >
        <div className="nt-canvas" style={{ transform: `scale(${zoom})`, transformOrigin: "top center" }}>
          <ul className="nt-children nt-children--root">

            {/* INTERNET → GATEWAY */}
            <OrgBranch
              card={<InternetCard />}
            >
              <OrgBranch
                card={
                  <GatewayCard
                    ip={`${main.prefix}.1`}
                    hostname={main.gateway?.hostname}
                    fabricante={main.gateway?.fabricante}
                  />
                }
              >
                {/* Dispositivos directos en la red principal */}
                {main.devices.map((d, i) => (
                  <OrgBranch key={d.ip || i} card={<DeviceCard device={d} />} />
                ))}

                {/* Extensores con sus dispositivos */}
                {hasExtensors && extensors.map((ext, i) => (
                  <OrgBranch
                    key={ext.prefix}
                    card={
                      <ExtensorCard
                        ip={`${ext.prefix}.1`}
                        hostname={ext.gateway?.hostname}
                        fabricante={ext.gateway?.fabricante}
                        deviceCount={ext.devices.length}
                      />
                    }
                  >
                    {ext.devices.map((d, j) => (
                      <OrgBranch key={d.ip || j} card={<DeviceCard device={d} />} />
                    ))}
                  </OrgBranch>
                ))}
              </OrgBranch>
            </OrgBranch>

          </ul>
        </div>
      </div>

      {/* Controles de zoom */}
      <div className="nt-controls">
        <button className="nt-ctrl-btn" onClick={() => setZoom(z => Math.min(z * 1.15, 2.5))} title="Zoom +">＋</button>
        <span className="nt-zoom-label">{Math.round(zoom * 100)}%</span>
        <button className="nt-ctrl-btn" onClick={() => setZoom(z => Math.max(z * 0.85, 0.3))} title="Zoom −">－</button>
        <button className="nt-ctrl-btn" onClick={() => setZoom(1)} title="Restablecer">⊡</button>
      </div>
    </div>
  );
}
