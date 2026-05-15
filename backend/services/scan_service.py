import datetime
from core.scanner import ScannerEngine, get_local_cidr
from core.cve_client import CVEClient
from services.db_service import DatabaseService

class ScanService:
    def __init__(self):
        self.scanner = ScannerEngine()
        self.cve_client = CVEClient()
        self.db_service = DatabaseService()

    def discover(self, target_ip: str):
        # Limpieza de input
        ip_limpia = target_ip.replace('=', '').strip() if target_ip else ''
        
        # Auto-configuración
        if ip_limpia.lower() == "auto" or ip_limpia == "":
            ip_real = get_local_cidr()
        else:
            ip_real = ip_limpia

        if not getattr(self.scanner, 'nmap_installed', True):
            return {"error": "NMAP_MISSING", "target": ip_real}

        # Fase 1: Descubrir esqueleto de red con Traceroute
        topology = self.scanner.fase1_traceroute()

        # Fase 2: Escaneo liviano (por ahora Nmap, pronto DHCP/SNMP)
        dispositivos = self.scanner.discover_network(ip_real)
        
        # Guardar todo en topology para que Frontend lo use
        topology["devices"] = dispositivos

        return {"status": "ok", "dispositivos": dispositivos, "target": ip_real, "topology": topology}

    def deep_scan(self, ip: str, user_id: str = "", scan_id: str = ""):
        print(f"====== INICIANDO ESCANEO PARA: {ip} (user: {user_id}, scan: {scan_id}) ======")

        puertos_info = self.scanner.scan_ports(ip)
        puertos = puertos_info.get("puertos_abiertos", [])
        
        total_vulnerabilidades = 0
        for puerto in puertos:
            servicio = puerto.get("servicio", "")
            version = puerto.get("version", "")
            
            if version and version.strip() != "":
                cves = self.cve_client.buscar_vulnerabilidades(servicio, version)
                puerto["vulnerabilidades"] = cves
                total_vulnerabilidades += len(cves)
            else:
                puerto["vulnerabilidades"] = []
        
        mac_real = puertos_info.get("mac", "Desconocida")
        id_unico = mac_real if mac_real != "Desconocida" else ip
        
        # Lógica de Historial e Intrusos
        doc_snap = self.db_service.get_historial_doc(id_unico, user_id)
        hora_actual = datetime.datetime.utcnow().isoformat()
        es_nuevo = False
        primera_conexion = hora_actual
        
        if not doc_snap.exists:
            es_nuevo = True
            self.db_service.save_historial_doc(id_unico, {
                "ip_inicial": ip,
                "mac": mac_real,
                "primera_conexion": hora_actual,
                "fabricante": puertos_info.get("fabricante", "Desconocido")
            }, user_id)
        else:
            datos_historial = doc_snap.to_dict()
            primera_conexion = datos_historial.get("primera_conexion", hora_actual)
            
        # Cálculo de Riesgo Máximo
        max_score = 0
        for puerto in puertos:
            for v in puerto.get("vulnerabilidades", []):
                v_score = v.get("score", 0)
                if v_score > max_score:
                    max_score = v_score

        documento = {
            "ip": ip,
            "mac": mac_real,
            "hostname": puertos_info.get("hostname", ""),
            "fabricante": puertos_info.get("fabricante", "Desconocido"),
            "puertos_abiertos": puertos,
            "total_vulnerabilidades": total_vulnerabilidades,
            "max_score": max_score,
            "fecha_auditoria": hora_actual,
            "estado": "Completado",
            "es_nuevo": es_nuevo,
            "primera_conexion": primera_conexion,
            "scan_id": scan_id
        }
        
        # 1. Guardar en vista general del usuario
        self.db_service.save_device(ip, documento, user_id)
        
        # 2. Guardar en el histórico de este escaneo específico
        if scan_id:
            self.db_service.save_scan_device(user_id, scan_id, ip, documento)
        
        if total_vulnerabilidades > 0:

            for puerto in puertos:
                for cve in puerto.get("vulnerabilidades", []):
                    self.db_service.save_vulnerability(cve["cve_id"], {
                        **cve,
                        "ip": ip,
                        "puerto": puerto.get("puerto"),
                        "servicio": puerto.get("servicio"),
                        "version": puerto.get("version"),
                        "fecha_deteccion": datetime.datetime.utcnow().isoformat()
                    }, user_id)
        
        return documento
