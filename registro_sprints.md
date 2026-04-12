# Registro Histórico de Avances (Sprints) SecScan

Este documento registra los hitos arquitectónicos alcanzados en la plataforma, evolucionando desde un prototipo universitario hasta un Software-as-a-Service (SaaS) Cloud-Ready. Se actualizará constantemente en este repositorio.

## ✅ Sprint 1: Refactorización y Limpieza Base
**Objetivo:** Eliminar el código monolítico antiguo y sentar las bases para escalabilidad.
- **SQLite Eliminado:** Se removió la persistencia local bloqueante (archivos `.db`) y sus respectivos modelos en SQLAlchemy que ataban la aplicación al disco bajo rendimiento I/O.
- **Git Iniciado:** Primer commit de la arquitectura V2 y estandarización del `.gitignore` para proteger llaves y variables de entorno (`venv`).

## ✅ Sprint 2: Adopción Cloud y Bases NoSQL
**Objetivo:** Conectar el Backend de procesamiento a una Base de Datos en tiempo real.
- **SDK Integrado:** Instalación de `firebase-admin` mediante el Patrón de Diseño "Singleton" para ahorro de rendimiento bajo el modelo REST.
- **Firestore Configurado:** Inyección directa hacia la nube de Google mediante cuenta de servicio con llaves HMAC / Certificate.
- **Endpoint Test:** Escritura probada de un JSON directo hacia el cluster de Google con latencias mínimas.

## ✅ Sprint 3: Arquitectura de Microservicios y API Atómica
**Objetivo:** Dividir el núcleo escaneador en rutas individuales operables de manera concurrente para orquestadores.
- **Optimización Nmap:** Se inyectó al cerebo Nmap los parámetros extremos de ancho de banda (`-T4` y `--min-rate 1000`) para reducir severamente los Timeout limits si una subred local muere o no responde a tiempo.
- **División de Rutas:** El controlador `main.py` se separó en verbos asíncronos atómicos:
  - `POST /api/discover`: Mapeo de vivos veloz en red completa (Ping Sweep `-sn`), para uso directo del Maestro Orquestador.
  - `POST /api/deep-scan/{ip}`: Ataque profundo puerto a puerto (`-sV -F`) a una IP unitaria que interactúa con la persistencia inyectándolo como un Documento NoSQL en la colección `devices` de Firestore Nube.

## ✅ Sprint 4: Orquestación y Automatización con n8n
**Objetivo:** Levantar al "Director de Orquesta" n8n para paralelizar los Microservicios y eliminar la intervención humana.
- **n8n Instalado:** Motor de orquestación visual levantado localmente en `localhost:5678` mediante `npx n8n` sobre Node.js v22.
- **Workflow Diseñado:** Se construyó un flujo de 4 nodos encadenados:
  1. `When clicking Execute` (Gatillo Manual): Dispara la secuencia bajo demanda.
  2. `HTTP Request → POST /api/discover`: Llama a FastAPI para obtener la lista de IPs vivas.
  3. `Split Out (dispositivos)`: Descompone el arreglo JSON agrupado en elementos individuales iterables.
  4. `HTTP Request → POST /api/deep-scan/{{ $json.ip }}`: Para cada IP viva, dispara un escaneo profundo en paralelo e inyecta los resultados en Firebase automáticamente.
- **Validación en Vivo:** Se ejecutó el Workflow completo verificando en la consola de Firebase que los documentos NoSQL aparecieran en tiempo real sin intervención humana.

### Sprint 5: Orquestador n8n e Inteligencia de Vulnerabilidades (Integración NVD)
- [x] Levantar base de datos NoSQL Firestore y configurar esquema.
- [x] Orquestar el flujo automatizado local con **n8n** (Split en lotes).
- [x] Desarrollar microservicio puente `trigger-scan` para sortear restricciones CORS.
- [x] Extracción en tiempo real de Vulnerabilidades cruzando el Nacional Vulnerability Database (NVD API v2).

### Sprint 6: Plataforma Web Dashboard "Ciberseguridad Premium"
- [x] Diseño completo de la Interfaz Web con React + Vite.
- [x] Tema visual "Premium Dark" enfocado en UX de ciberseguridad.
- [x] Lógica de Polling recursivo hacia Firestore para visualizar escaneos asíncronos en tiempo real.
- [x] Construcción de páginas de Historial e Interacciones Modales por IP específica.

### Sprint 7: Calibración Antifantasmas y Hardware Forense
- [x] Corrección de falsos positivos en Nmap (eliminando `1000 min-rate`) usando forzado a ping físico (`-PR`).
- [x] Implementación de **Vendor Fingerprinting** automático (Conversión de MAC a nombres de manufactura ej: "Huawei", "Apple").
- [x] Renderizado condicional en frontend para dar prioridad visual al Fabricante frente a la MAC.

### Sprint 8: Arquitectura Zero Configure (Producto Abierto)
- [x] Creado subsistema de red para cálculo autónomo e instanciado del CIDR (`get_local_cidr()`) vía sockets DGRAM de bajo nivel.
- [x] Escáner blindado contra errores forzados de tipeo por interfaces humanas (n8n Webhook Fallback System).
- [x] Integración de un Doble Motor Geográfico: Fusión de **Nmap** + Motor nativo de SO (**ARP Cache `arp -a`**). Esto rescata Smart-TVs y Móviles en Suspensión Profunda o Privacy Configured.

### Sprint 9: Detección de Intrusos y UX de Vulnerabilidades
- [x] Implementación de arquitectura Firestore doble vía: Colección inmutable `historial` vs estatus transitorio `devices`.
- [x] Lógica de Inyección de Tiempos Periciales (`primera_conexion`) de los visitantes/intrusos detectados.
- [x] Interfaz Gráfica con Indicadores Neón de Aparatos Nuevos y auto-scroll agrupado inteligente desde IPs hacia CVEs (DOM Manipulación).

### Sprint 10: Zero-Touch Provisioning (Auto-Instalador de Dependencias)
- [x] Desarrollo del subsistema de auto-descarga de binarios nativos desde servidores oficiales.
- [x] Implementación de elevación de privilegios (UAC Windows) mediante PowerShell `RunAs` integrada en Python.
- [x] Creación de la interfaz de "Emergencia Técnica" en React que bloquea el dashboard si faltan motores de escaneo.
- [x] Refactorización del motor de Scanner para soportar "Soft Errors" y evitar crashes del servidor por falta de software host.

### Sprint 11: Arquitectura Modular (Clean Architecture)
- [x] Migración del backend monolítico a un modelo de Capas (Rutas, Servicios, Esquemas).
- [x] Implementación de **Singleton Pattern** y **Service Layer** para desacoplar la lógica de red de la persistencia en base de datos.
- [x] Estandarización de modelos Pydantic para validación estricta de payloads.
- [x] Transición del punto de entrada `main.py` hacia `app.py` unificado.

## ✅ Sprint 5 (Original): Cruce de Vulnerabilidades CVE (Inteligencia de Ciberseguridad)
**Objetivo:** Transformar datos crudos de puertos/versiones en alertas accionables cruzándolos con la base de datos mundial de vulnerabilidades conocidas (NVD del gobierno de EE.UU.).
- **Módulo `core/cve_client.py`:** Cliente HTTP que consulta la API REST pública del NVD v2.0 (`services.nvd.nist.gov`). Recibe un servicio + versión y devuelve CVEs con su ID, descripción, severidad CVSS y score numérico.
- **Endpoint `/api/cve-lookup`:** Ruta atómica independiente para consultas manuales directas de vulnerabilidades sin necesidad de escanear la red.
- **Integración en `/api/deep-scan`:** El endpoint de escaneo profundo ahora automáticamente cruza cada puerto con versión detectada contra el NVD, y persiste los resultados en dos colecciones de Firebase: `devices` (reporte completo) y `vulnerabilities` (índice individual por CVE).
- **Validación:** Se probó con `apache 2.4.49` obteniendo 2 CVEs CRÍTICOS reales (CVE-2021-41773 y CVE-2021-42013, score 9.8/10).

### 📌 Hallazgo Técnico Documentado (Sprint 5)
> **"La calidad de la inteligencia de vulnerabilidades depende directamente de la precisión del fingerprinting de Nmap."**
> Cuando Nmap logra extraer el nombre y versión exactos del software (ej: `apache 2.4.49`), el cruce con el NVD es quirúrgico y devuelve CVEs precisos con severidad CRÍTICA real. Sin embargo, cuando Nmap solo detecta un nombre genérico (ej: `http 2.0`), los resultados del NVD son "ruido" — CVEs antiguos e irrelevantes de servidores HTTP diversos que coinciden textualmente pero no pertenecen al software real del equipo auditado. Este hallazgo es vital para la interpretación de resultados en ambientes de producción.
