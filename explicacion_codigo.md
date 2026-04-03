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
