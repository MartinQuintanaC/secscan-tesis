import nmap

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
        
        # Ejecutamos el motor verdadero de Nmap
        self.nm.scan(hosts=network_range, arguments='-sn')
        
        discovered_devices = []
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
                
        return discovered_devices

    def scan_ports(self, ip_target: str) -> dict:
        """
        Escaneo profundo (Opción A): Busca puertos abiertos y descubre qué programas corren adentro.
        """
        print(f"Iniciando escaneo profundo en: {ip_target}...")
        
        # -sV: Nmap intentará descubrir la versión exacta del servicio (CRÍTICO para la tesis).
        # -F: Fast scan (escanea los 100 puertos más comunes para no demorar horas).
        self.nm.scan(hosts=ip_target, arguments='-sV -F')
        
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
                    
        return {
            "ip": ip_target,
            "mac": self.nm[ip_target]['addresses'].get('mac', 'Desconocida'),
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
