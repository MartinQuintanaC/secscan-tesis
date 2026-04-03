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

## ⏳ Sprint 4: Automatización n8n (Siguiente)
**Objetivo:** Levantar al "Director de Orquesta" n8n para paralelizar los Microservicios.
