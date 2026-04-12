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

        dispositivos = self.scanner.discover_network(ip_real)
        return {"status": "ok", "dispositivos": dispositivos, "target": ip_real}

    def deep_scan(self, ip: str):
        print(f"====== INICIANDO ESCANEO MAESTRO PARA: {ip} ======")
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
        doc_snap = self.db_service.get_historial_doc(id_unico)
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
            })
        else:
            datos_historial = doc_snap.to_dict()
            primera_conexion = datos_historial.get("primera_conexion", hora_actual)
            
        documento = {
            "ip": ip,
            "mac": mac_real,
            "fabricante": puertos_info.get("fabricante", "Desconocido"),
            "puertos_abiertos": puertos,
            "total_vulnerabilidades": total_vulnerabilidades,
            "fecha_auditoria": hora_actual,
            "estado": "Completado",
            "es_nuevo": es_nuevo,
            "primera_conexion": primera_conexion
        }
        
        # Persistencia
        self.db_service.save_device(ip, documento)
        
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
                    })
        
        return documento
