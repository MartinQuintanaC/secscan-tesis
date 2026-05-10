import nmap
import subprocess
import socket
import re
import ipaddress

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def get_local_cidr():
    ip = get_local_ip()
    if ip != '127.0.0.1':
        parts = ip.split('.')
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    return "192.168.1.0/24"

def get_local_mac():
    import uuid
    return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1]).upper()

class ScannerEngine:
    def __init__(self):
        # python-nmap intentará buscar el ejecutable "nmap" en el PATH de Windows o en su ruta base
        self.reload_engine()

    def reload_engine(self):
        try:
            self.nm = nmap.PortScanner(nmap_search_path=('nmap', r'C:\Program Files (x86)\Nmap\nmap.exe', r'C:\Program Files\Nmap\nmap.exe'))
            self.nmap_installed = True
            return True
        except nmap.PortScannerError:
            self.nmap_installed = False
            self.nm = None
            print("Soft Error: Nmap no detectado. El sistema requerirá instalación autónoma.")
            return False

    def _is_private_ip(self, ip_str: str) -> bool:
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private
        except ValueError:
            return False

    def _get_mac_from_arp(self, ip_target: str) -> str:
        """Intenta obtener la MAC de una IP mediante el comando arp -a local."""
        try:
            arp_output = subprocess.check_output(['arp', '-a', ip_target], shell=True).decode('cp1252', errors='ignore')
            for line in arp_output.split('\n'):
                parts = line.split()
                if len(parts) >= 2 and parts[0] == ip_target:
                    mac = parts[1].replace('-', ':').upper()
                    if mac != 'FF:FF:FF:FF:FF:FF':
                        return mac
        except Exception:
            pass
        return "Desconocida"

    def fase1_traceroute(self) -> dict:
        """
        FASE 1: Ejecuta tracert hacia 8.8.8.8 para descubrir el 'esqueleto' de la red.
        Retorna:
            - hops_privados: Nodos internos (ej. Extensores, Router Principal).
            - router_isp: Primer salto con IP pública (Internet).
        """
        print("[FASE 1] Iniciando Traceroute hacia 8.8.8.8 para descubrir la columna vertebral...")
        hops_privados = []
        router_isp = None
        
        try:
            # tracert -d: no resuelve nombres, -h 15: máximo 15 saltos
            # -w 500: timeout de 500ms por salto para que sea súper rápido
            result = subprocess.run(
                ['tracert', '-d', '-h', '15', '-w', '500', '8.8.8.8'], 
                capture_output=True, text=True, timeout=20
            )
            
            # Buscar IPs en cada línea usando regex
            ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
            
            for line in result.stdout.splitlines():
                match = ip_pattern.search(line)
                if match:
                    ip = match.group(0)
                    
                    # Ignoramos si es la IP destino 8.8.8.8
                    if ip == '8.8.8.8':
                        continue
                        
                    if self._is_private_ip(ip):
                        mac = self._get_mac_from_arp(ip)
                        hops_privados.append({
                            "ip": ip,
                            "mac": mac,
                            "tipo": "router_privado",
                            "hostname": "Hop Interno"
                        })
                        print(f"  -> [HOP PRIVADO] {ip} (MAC: {mac})")
                    else:
                        # La primera IP pública que encontramos es el ISP
                        router_isp = {"ip": ip, "tipo": "router_isp", "hostname": "ISP Público"}
                        print(f"  -> [HOP PÚBLICO - ISP] {ip} (Fin de la red local)")
                        break # Detenemos la búsqueda de hops, ya salimos a Internet
                        
        except subprocess.TimeoutExpired:
            print("  [Traceroute] Timeout expirado.")
        except Exception as e:
            print(f"  [Traceroute] Error: {e}")
            
        # El Router Principal (C) es el último salto privado que vimos antes de salir a Internet
        if hops_privados:
            hops_privados[-1]["hostname"] = "Router Principal (C)"
            hops_privados[-1]["tipo"] = "router_principal"
            
        return {
            "hops_privados": hops_privados,
            "router_isp": router_isp
        }
    
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
                
                # Suplemento MAC local
                if host == get_local_ip() and mac == "Desconocida":
                    mac = get_local_mac()
                    
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
        
        # --- SUPLEMENTO MAC LOCAL ---
        if ip_target == get_local_ip() and mac == 'Desconocida':
            mac = get_local_mac()
        # --- FIN SUPLEMENTO MAC LOCAL ---
        
        # Intentamos obtener el fabricante a partir de la MAC usando la base de Nmap
        fabricante = "Desconocido"
        if 'vendor' in self.nm[ip_target] and mac in self.nm[ip_target]['vendor']:
            fabricante = self.nm[ip_target]['vendor'][mac]
            
        hostname = self.nm[ip_target].hostname() if hasattr(self.nm[ip_target], 'hostname') else ""
        
        # Fallback 1: DNS inverso con socket (funciona para routers y PCs bien configuradas)
        if not hostname:
            try:
                hostname = socket.gethostbyaddr(ip_target)[0]
                print(f"[DNS] Hostname resuelto para {ip_target}: {hostname}")
            except Exception:
                pass
        
        # Fallback 2: NetBIOS via nbtstat -A (para PCs Windows en la misma LAN)
        if not hostname:
            try:
                result = subprocess.run(
                    ['nbtstat', '-A', ip_target],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    # Buscamos la línea con <00> que es el nombre del equipo
                    if '<00>' in line and 'UNIQUE' in line:
                        hostname = line.strip().split()[0].strip()
                        print(f"[NetBIOS] Hostname resuelto para {ip_target}: {hostname}")
                        break
            except Exception:
                pass
            
        return {
            "ip": ip_target,
            "mac": mac,
            "hostname": hostname,
            "fabricante": fabricante,
            "puertos_abiertos": puertos_descubiertos
        }

# Prueba simple: Si ejecutas este archivo directamente en la consola
if __name__ == "__main__":
    scanner = ScannerEngine()
    
    print("\n--- PRUEBA FASE 1: TRACEROUTE ---")
    resultados_traceroute = scanner.fase1_traceroute()
    import json
    print(json.dumps(resultados_traceroute, indent=2))
