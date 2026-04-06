# Diccionario Arquitectónico del Código Backend

Este documento sirve como "Guía de Defensa" permanente para la tesis. Contiene la justificación técnica de cómo funciona cada archivo `.py` de la aplicación y a qué patrón de diseño pertenece. Este documento se auditará y expandirá si los módulos reciben mejoras.

---

## 1. Archivo: `core/scanner.py`
**Rol Principal:** El Motor / Traductor (Wrapper) de Ciberseguridad.

**¿Qué hace a nivel de Ingeniería?**
Python no se encarga nativamente de inyectar paquetes ICMP a las placas de red (NIC); este archivo funciona como un **Patrón Wrapper**. Llama al ejecutable de sistema `Nmap.exe`, procesa el masivo texto/XML que genera el demonio, lo desarma, lo traduce, y lo convierte en arreglos tipo **Diccionario (JSON)** estandarizado para la nube.

**Sus 3 Funciones Internas:**
1. **`__init__`:** (Clásico Bootstrapper) Verifica la existencia física del binario original de Nmap. Implementa un patrón "Fail-fast" garantizando evitar caídas del servidor por falta de dependencias en Windows.
2. **`discover_network`:** Lanza Nmap con argumento `-sn`. Suprime la inspección de la capa de transporte y lanza Broadcasting para un reconocimiento pasivo ultrarrápido (Encontrar Vivos).
3. **`scan_ports`:** Lanza Nmap sobre **UNA IP atómica**. Usa agresivas banderas: `-sV` (Toma Huellas / Banner Grabbing de versiones app), `-F` (Poda puertos muertos limitándose al top 100 para no hacer esperar al orquestador) y la inyección `-T4 --min-rate 1000` (Evita penalizaciones obligando a lanzar lotes rápidos sobre subredes reacias al ping).

---

## 2. Archivo: `core/firebase_client.py`
**Rol Principal:** Cliente Intermediario hacia la Base de Datos NoSQL.

**¿Qué hace a nivel de Ingeniería?**
Implementa uno de los patrones más famosos del mundo del software empresarial: **El Patrón de Diseño Singleton**. El propósito del Singleton es asegurar que independientemente cuantas peticiones paralelas envíe nuestro Orquestador n8n (ej. 30 escaneos simultáneos), Python **fuerza y enruta** a todos a re-utilizar la *misma única conexión HTTP a internet* con Google GCP. Reduce el latigazo al pool de memoria al evitar inicializar 30 instancias del Cloud Firestore sobrepasando cuellos de botella y ahorrando cuota. Se alimenta desde el archivo confinado `firebase_admin.json`.

---

## 3. Archivo: `main.py`
**Rol Principal:** Controlador RESTful Frontal (API FastAPI/Uvicorn).

**¿Qué hace a nivel de Ingeniería?**
Encapsula la complejidad orientada a objetos de los otros Módulos y "Levanta las Puertas HTTP". Transformó el monolito antiguo en un estado *Microservicio Stateless*:
- Carece de memoria persistente interna. Lo que lo vuelve fácilmente descartable/desplegable en Docker de necesitarse.
- `POST /api/discover`: Actúa como una función pura (Extrae datos rápidos pero ni siquiera llama a la Base de Datos).
- `POST /api/deep-scan/{ip}`: Esqueleto clave de la operación persistente; interroga un escaneo duro y llama al método `.set()` de Firestore para obligar a empujar la data directo a la matriz `devices` en la colección.

---

## 4. Componente Externo: Workflow n8n (Orquestador Visual)
**Rol Principal:** Director de Orquesta / Message Broker Visual.

**¿Qué hace a nivel de Ingeniería?**
n8n no es un archivo `.py` nuestro sino un motor externo que corre sobre Node.js en `localhost:5678`. Funciona como un **Orquestador de Servicios** basado en el patrón arquitectónico **"Pipes and Filters"** (Tuberías y Filtros). Cada nodo del flujo es un "Filtro" que procesa datos y los pasa al siguiente por una "Tubería".

**Sus 4 Nodos (Flujo Actual):**
1. **Gatillo Manual (`When clicking Execute`):** Punto de entrada. En producción se reemplazaría por un `Schedule Trigger` (Cron Job Visual) para ejecutar auditorías automáticas cada X horas sin intervención humana.
2. **HTTP Request (Discover):** Envía un `POST` a nuestra API FastAPI pidiendo la lista de dispositivos vivos. Es el equivalente a un cliente HTTP programático (como Postman) pero automatizado.
3. **Split Out (`dispositivos`):** Toma el arreglo JSON agrupado que devuelve FastAPI y lo descompone en elementos individuales. Sin este nodo, n8n trataría a los 254 equipos como "un solo bloque" en vez de procesarlos individualmente.
4. **HTTP Request (Deep-Scan):** Usa la variable dinámica `{{ $json.ip }}` para inyectar cada IP viva en la URL del endpoint `/api/deep-scan/{ip}`. n8n ejecuta este nodo **una vez por cada elemento** que generó el Split Out, logrando paralelismo masivo.

---

## 5. Archivo: `core/cve_client.py`
**Rol Principal:** Cliente de Inteligencia de Amenazas (Threat Intelligence).

**¿Qué hace a nivel de Ingeniería?**
Implementa un **Patrón Cliente HTTP** que se comunica con la API REST pública del NVD (National Vulnerability Database) del gobierno de Estados Unidos. Es el puente entre los datos crudos de nuestro escáner y la base de datos mundial de vulnerabilidades conocidas.

**Su Función Principal:**
- **`buscar_vulnerabilidades(servicio, version)`:** Recibe el nombre del software y su versión (extraídos por Nmap), construye una keyword de búsqueda, y realiza una petición GET a `https://services.nvd.nist.gov/rest/json/cves/2.0`. Parsea la respuesta JSON del gobierno y extrae: ID del CVE, descripción en inglés, severidad (CRITICAL/HIGH/MEDIUM/LOW) y score CVSS numérico (0-10). Implementa rate-limiting (`time.sleep(1.5)`) para respetar los límites de la API pública (máx ~5 peticiones por 30 segundos sin API Key) y manejo defensivo de errores (Timeout, códigos HTTP no-200) para evitar crashes durante escaneos masivos.
