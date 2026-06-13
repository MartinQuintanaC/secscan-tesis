import datetime
import threading
import time
import subprocess
import socket
import ipaddress
import nmap
from core.scanner import ScannerEngine, get_local_cidr, get_local_ip, get_local_mac
from core.cve_client import CVEClient
from services.db_service import DatabaseService

# Caché en memoria global recopilada por el demonio pasivo de fondo
_passive_device_cache = {}
_last_subnet = None
_daemon_started = False
_daemon_lock = threading.Lock()

def start_passive_daemon():
    """Inicializa de forma segura el hilo del demonio en segundo plano."""
    global _daemon_started
    with _daemon_lock:
        if _daemon_started:
            return
        _daemon_started = True
        
    thread = threading.Thread(target=run_passive_background_worker, daemon=True, name="PassiveScanDaemon")
    thread.start()
    print("[PassiveScanDaemon] Hilo de escaneo pasivo en segundo plano iniciado correctamente.")

def run_passive_background_worker():
    """Ciclo en segundo plano del demonio pasivo."""
    global _last_subnet, _passive_device_cache
    
    # Espera inicial para la estabilización de interfaces de red
    time.sleep(2)
    
    while True:
        try:
            current_cidr = get_local_cidr()
            if not current_cidr:
                time.sleep(10)
                continue
                
            if current_cidr != _last_subnet:
                print(f"[PassiveScanDaemon] Cambio de red o nueva subred detectada: {current_cidr}. Limpiando caché anterior.")
                _last_subnet = current_cidr
                _passive_device_cache.clear()
            
            print(f"[PassiveScanDaemon] Iniciando ciclo de escaneo pasivo en segundo plano en {current_cidr}...")
            prefix = current_cidr.split('/')[0].rsplit('.', 1)[0] + '.'
            
            # 1. Refresco Silencioso (Ping Sweep rápido en background para poblar ARP cache)
            try:
                nm = nmap.PortScanner()
                nm.scan(hosts=current_cidr, arguments='-sn -PE -T3')
            except Exception:
                pass

            # 2. Lectura y parsing de la caché ARP local del SO
            found_ips = set()
            new_devices = {}
            try:
                arp_output = subprocess.check_output('arp -a', shell=True).decode('cp1252', errors='ignore')
                for line in arp_output.split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        ip_arp = parts[0].strip()
                        mac_arp = parts[1].strip().replace('-', ':').upper()
                        if (ip_arp.startswith(prefix)
                                and ip_arp not in found_ips
                                and not ip_arp.endswith('.255')
                                and mac_arp not in ('FF:FF:FF:FF:FF:FF', 'FF-FF-FF-FF-FF-FF')
                                and len(mac_arp) == 17):
                            
                            cached_dev = _passive_device_cache.get(ip_arp)
                            hostname = cached_dev.get("hostname") if cached_dev else ""
                            vendor = cached_dev.get("vendor", "") if cached_dev else ""
                            
                            if not hostname or hostname == "Caché ARP Pasiva":
                                try:
                                    hostname = socket.gethostbyaddr(ip_arp)[0]
                                except Exception:
                                    hostname = "Caché ARP Pasiva"
                                    
                            new_devices[ip_arp] = {
                                "ip": ip_arp,
                                "mac": mac_arp,
                                "hostname": hostname,
                                "vendor": vendor,
                                "discovery_method": "arp_cache_passive",
                                "parent_ip": current_cidr.split('/')[0]
                            }
                            found_ips.add(ip_arp)
            except Exception as e:
                print(f"[PassiveScanDaemon] Error leyendo tabla ARP: {e}")

            # 3. Incorporar la máquina host actual a la lista
            try:
                local_ip = get_local_ip()
                if local_ip not in found_ips and local_ip.startswith(prefix):
                    new_devices[local_ip] = {
                        "ip": local_ip,
                        "mac": get_local_mac(),
                        "hostname": socket.gethostname(),
                        "vendor": "",
                        "discovery_method": "local_passive",
                        "parent_ip": current_cidr.split('/')[0]
                    }
            except Exception:
                pass
                
            if new_devices:
                _passive_device_cache = new_devices
            
            print(f"[PassiveScanDaemon] Ciclo de fondo finalizado. Dispositivos en caché: {len(new_devices)} | IPs: {list(new_devices.keys())}")

                
        except Exception as e:
            print(f"[PassiveScanDaemon] Excepción en ciclo del worker: {e}")
            
        # Espera de 30 segundos entre barridos
        time.sleep(30)


class ScanService:
    def __init__(self):
        self.scanner = ScannerEngine()
        self.cve_client = CVEClient()
        self.db_service = DatabaseService()
        # Inicialización de seguridad si no se gatilló desde app.py
        start_passive_daemon()

    def set_log_cb(self, cb):
        from core.scanner import _thread_local
        _thread_local.log_cb = cb

    def _log(self, msg: str):
        print(msg)
        from core.scanner import _thread_local
        cb = getattr(_thread_local, 'log_cb', None)
        if cb:
            cb(msg)

    def discover(self, target_ip: str, passive: bool = False):
        # Limpieza de input
        ip_limpia = target_ip.replace('=', '').strip() if target_ip else ''
        
        # Auto-configuración
        if ip_limpia.lower() == "auto" or ip_limpia == "":
            ip_real = get_local_cidr()
        else:
            ip_real = ip_limpia

        if not getattr(self.scanner, 'nmap_installed', True):
            return {"error": "NMAP_MISSING", "target": ip_real}

        if passive:
            self._log(f"🤫 [SCAN PASIVO] Retornando estado en segundo plano instantáneo para {ip_real}...")
            topology = self.scanner.fallback_to_gateway("Escaneo Pasivo en segundo plano. Descubrimiento extraído de la memoria del daemon.")
            
            # Retornar la caché instantánea si el objetivo coincide con la red local activa
            if ip_real == _last_subnet or ip_limpia.lower() == "auto" or ip_limpia == "":
                dispositivos = list(_passive_device_cache.values())
            else:
                # Fallback pasivo en vivo para subredes distintas a la local activa
                prefix = ip_real.split('/')[0].rsplit('.', 1)[0] + '.'
                dispositivos = []
                found_ips = set()
                try:
                    arp_output = subprocess.check_output('arp -a', shell=True).decode('cp1252', errors='ignore')
                    for line in arp_output.split('\n'):
                        parts = line.split()
                        if len(parts) >= 2:
                            ip_arp = parts[0].strip()
                            mac_arp = parts[1].strip().replace('-', ':').upper()
                            if (ip_arp.startswith(prefix)
                                    and ip_arp not in found_ips
                                    and not ip_arp.endswith('.255')
                                    and mac_arp not in ('FF:FF:FF:FF:FF:FF', 'FF-FF-FF-FF-FF-FF')
                                    and len(mac_arp) == 17):
                                hostname = ""
                                try:
                                    hostname = socket.gethostbyaddr(ip_arp)[0]
                                except Exception:
                                    hostname = "Caché ARP Pasiva"
                                dispositivos.append({
                                    "ip": ip_arp,
                                    "mac": mac_arp,
                                    "hostname": hostname,
                                    "vendor": "",
                                    "discovery_method": "arp_cache_passive",
                                    "parent_ip": ip_real.split('/')[0]
                                })
                                found_ips.add(ip_arp)
                except Exception as e:
                    self._log(f"  [Scan Pasivo Fallback Error] {e}")
            
            topology["advertencias"].append("Auditoría Pasiva en Segundo Plano: Este mapa se generó a partir de la caché en memoria recopilada silenciosamente por el daemon de fondo.")
            topology["devices"] = dispositivos
            return {"status": "ok", "dispositivos": dispositivos, "target": ip_real, "topology": topology, "passive": True}

        # Escaneo Activo
        # Obtener IPs activas de la caché del demonio pasivo de fondo si aplica a la subred local
        active_ips = None
        if (ip_real == _last_subnet or ip_limpia.lower() == "auto" or ip_limpia == "") and _passive_device_cache:
            active_ips = list(_passive_device_cache.keys())

        # Fase 1: Descubrir esqueleto de red con Traceroute
        topology = self.scanner.fase1_traceroute()
        advertencias = topology.get("advertencias", [])

        # Extraer la IP real del Router Principal (puede ser "unknown" en redes blindadas)
        router_principal_ip = None
        for hop in topology.get("hops_privados", []):
            if hop.get("tipo") == "router_principal" and hop.get("ip") != "unknown":
                router_principal_ip = hop["ip"]
                break

        # Fase 2: Cascada SNMP → DHCP → Nmap fallback (Acelerado por caché)
        dispositivos = self.scanner.discover_network(
            ip_real,
            router_principal_ip=router_principal_ip,
            advertencias=advertencias,
            active_ips=active_ips
        )

        topology["advertencias"] = advertencias
        topology["devices"] = dispositivos

        return {"status": "ok", "dispositivos": dispositivos, "target": ip_real, "topology": topology}




    def deep_scan(self, ip: str, user_id: str = "", scan_id: str = ""):
        self._log(f"====== INICIANDO ESCANEO PARA: {ip} (user: {user_id}, scan: {scan_id}) ======")

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
