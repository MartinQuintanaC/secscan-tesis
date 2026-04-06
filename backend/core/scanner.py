import nmap
import subprocess
import socket
import re

def get_local_cidr():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    
    if ip != '127.0.0.1':
        parts = ip.split('.')
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    return "192.168.1.0/24"

class ScannerEngine:
    def __init__(self):
        # python-nmap intentará buscar el ejecutable "nmap" en el PATH de Windows o en su ruta base
        try:
            self.nm = nmap.PortScanner(nmap_search_path=('nmap', r'C:\Program Files (x86)\Nmap\nmap.exe', r'C:\Program Files\Nmap\nmap.exe'))
        except nmap.PortScannerError:
            print("ERROR: Nmap no se encuentra instalado en tu sistema o no está en el PATH.")
            raise
    
    def discover_network(self, network_range: str) -> list:
        """
        Realiza un escaneo de descubrimiento (ping sweep) para encontrar dispositivos vivos.
        El argumento '-sn' le dice a Nmap que NO escanee puertos aún, ahorrando muchísimo tiempo.
        """
        print(f"Iniciando descubrimiento de red rápida en: {network_range}...")
        
        # Usamos -sn -PR para forzar un descubrimiento ARP físico (irrompible por firewalls locales)
        self.nm.scan(hosts=network_range, arguments='-sn -PR')
        
        discovered_devices = []
        found_ips = set()
        
        for host in self.nm.all_hosts():
            # Solo guardamos los hosts que Nmap confirme como encendidos ("up")
            if self.nm[host]['status']['state'] == 'up':
                
                # Nmap a veces no puede leer la MAC si estás escaneando localhost u otra subred distinta.
                mac = "Desconocida"
                if 'mac' in self.nm[host]['addresses']:
                    mac = self.nm[host]['addresses']['mac']
                    
                device_info = {
                    "ip": host,
                    "mac": mac,
                    "hostname": self.nm[host].hostname()
                }
                discovered_devices.append(device_info)
                found_ips.add(host)
                
        # --- SUPLEMENTO ARP SUGERIDO POR EL USUARIO ---
        print("Ejecutando motor suplementario ARP cache para rescatar dispositivos silenciosos...")
        try:
            arp_output = subprocess.check_output('arp -a', shell=True).decode('cp1252', errors='ignore')
            lines = arp_output.split('\n')
            
            # Prefijo para la subred local (Ej: 192.168.18.)
            prefix = network_range.split('/')[0].rsplit('.', 1)[0] + '.'
            
            for line in lines:
                parts = line.split()
                # Normalmente arp arroja: 192.168.18.212   00-11-22-...   dinámico
                if len(parts) >= 2:
                    ip_arp = parts[0]
                    mac_arp = parts[1].replace('-', ':').upper()
                    
                    if ip_arp.startswith(prefix) and ip_arp not in found_ips and not ip_arp.endswith('.255'):
                        if mac_arp != 'FF:FF:FF:FF:FF:FF':
                            print(f"[!] Dispositivo Silencioso Rescatado de ARP Cache: {ip_arp}")
                            discovered_devices.append({
                                "ip": ip_arp,
                                "mac": mac_arp,
                                "hostname": "Caché Local ARP"
                            })
                            found_ips.add(ip_arp)
        except Exception as e:
            print(f"Advertencia: No se pudo procesar la tabla ARP ({e})")
                
        return discovered_devices

    def scan_ports(self, ip_target: str) -> dict:
        """
        Escaneo profundo (Opción A): Busca puertos abiertos y descubre qué programas corren adentro.
        """
        print(f"Iniciando escaneo profundo en: {ip_target}...")
        
        # -sV: Nmap intentará descubrir la versión exacta del servicio.
        # -F: Fast scan (100 puertos top).
        # -T4 y --min-rate obligan a nmap a ir al límite de red, previendo timeouts.
        self.nm.scan(hosts=ip_target, arguments='-sV -F -T4 --min-rate 1000 --max-retries 1')
        
        if ip_target not in self.nm.all_hosts():
            return {"ip": ip_target, "puertos": []}
            
        puertos_descubiertos = []
        
        # Si encuentra puertos TCP
        if 'tcp' in self.nm[ip_target]:
            for port in self.nm[ip_target]['tcp'].keys():
                port_data = self.nm[ip_target]['tcp'][port]
                # Solo guardamos los puertos confirmados como "abiertos"
                if port_data['state'] == 'open':
                    puertos_descubiertos.append({
                        "puerto": port,
                        "protocolo": "TCP",
                        "servicio": port_data['name'],   # ej. 'http', 'smb'
                        "version": port_data['version']  # ej. 'Apache 2.4.49'
                    })
                    
        mac = self.nm[ip_target]['addresses'].get('mac', 'Desconocida')
        
        # Intentamos obtener el fabricante a partir de la MAC usando la base de Nmap
        fabricante = "Desconocido"
        if 'vendor' in self.nm[ip_target] and mac in self.nm[ip_target]['vendor']:
            fabricante = self.nm[ip_target]['vendor'][mac]
            
        return {
            "ip": ip_target,
            "mac": mac,
            "fabricante": fabricante,
            "puertos_abiertos": puertos_descubiertos
        }

# Prueba simple: Si ejecutas este archivo directamente en la consola
if __name__ == "__main__":
    scanner = ScannerEngine()
    
    print("\n--- PRUEBA 1: VIVOS ---")
    resultados_vivos = scanner.discover_network("127.0.0.1")
    print(resultados_vivos)
    
    print("\n--- PRUEBA 2: PUERTOS ---")
    resultados_puertos = scanner.scan_ports("127.0.0.1")
    import json
    print(json.dumps(resultados_puertos, indent=2))
