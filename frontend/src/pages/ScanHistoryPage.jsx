import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getScanHistory } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function ScanHistoryPage() {
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const token = await getToken();
        const data = await getScanHistory(token);
        if (data.status === "ok") {
          setScans(data.scans || []);
        }
      } catch (err) {
        console.error("Error cargando historial", err);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [getToken]);

  const handleScanClick = (scanId) => {
    navigate(`/history/${scanId}`);
  };

  return (
    <div className="page-container fade-in">
      <button className="btn btn-back" onClick={() => navigate("/")}>
        ← Volver al Inicio
      </button>

      <div className="results-header">
        <h1>Cápsulas de Tiempo</h1>
        <p>Historial de auditorías de red.</p>
      </div>

      {loading ? (
        <div className="scanning-spinner" style={{ margin: "40px auto", width: "40px", height: "40px" }} />
      ) : scans.length > 0 ? (
        <div className="capsule-grid">
          {scans.map((scan, i) => {
            const hasVulns = scan.vulnerabilidades_found > 0;
            return (
              <div 
                key={scan.id} 
                className={`capsule-card slide-up ${hasVulns ? 'danger' : ''}`} 
                style={{ animationDelay: `${i * 0.05}s` }}
                onClick={() => handleScanClick(scan.id)}
              >
                <div className="capsule-header">
                  <div>
                    <div className="capsule-date">
                      🕰️ {new Date(scan.timestamp).toLocaleString()}
                    </div>
                    <div className="capsule-id">
                      ID: {scan.id.substring(0, 8)} | Org: {scan.ip || 'Auto'}
                    </div>
                  </div>
                  <div className={`capsule-status ${scan.status === 'completed' ? 'completed' : 'processing'}`}>
                    {scan.status === 'completed' ? 'Completado' : scan.status}
                  </div>
                </div>

                <div className="capsule-body">
                  <div className="capsule-stat">
                    <div className="capsule-stat-icon">💻</div>
                    <div className="capsule-stat-value" style={{ color: 'var(--accent-cyan)' }}>
                      {scan.devices_found ?? '?'}
                    </div>
                    <div className="capsule-stat-label">Dispositivos</div>
                  </div>
                  
                  <div className="capsule-stat">
                    <div className="capsule-stat-icon">🛡️</div>
                    <div className="capsule-stat-value" style={{ color: hasVulns ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                      {scan.vulnerabilidades_found ?? '?'}
                    </div>
                    <div className="capsule-stat-label">CVEs</div>
                  </div>
                </div>

                <div className="capsule-actions">
                  <button 
                    className="btn-export" 
                    onClick={(e) => { 
                      e.stopPropagation(); 
                      alert(`Exportar reporte para el escaneo: ${scan.id}\nEsta función generará un PDF en la versión final de la tesis.`);
                      // window.print(); // Se puede habilitar para imprimir directo
                    }}
                  >
                    📄 Exportar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <p>No tienes escaneos registrados aún.</p>
        </div>
      )}
    </div>
  );
}
