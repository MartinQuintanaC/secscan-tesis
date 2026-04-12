# Guía Técnica de Arquitectura Modular (SecScan)

Esta documentación utiliza terminología de Ingeniería de Software avanzada. Úsala como base para tu defensa técnica de tesis; demostrará que el sistema no solo funciona, sino que está construido bajo estándares de industria.

---

## 🏗️ Desglose de Capas y Patrones

### 1. Punto de Entrada: `app.py`
Es el **Bootstrap** de la aplicación. Aquí se inicializa la instancia de FastAPI, se configuran los middlewares de seguridad (CORS) y se realiza el montaje de los routers de la API. No contiene lógica de negocio, solo configuración de infraestructura.

### 2. Capa de Comunicación: `api/`
Implementamos un sistema de ruteo modularizado por versiones (`v1`).
*   **`api/v1/api.py`**: Funciona como un **Router Central** que unifica los diferentes controladores.
*   **`api/v1/endpoints/scans.py`**: Controlador de operaciones de red. Maneja las peticiones POST de descubrimiento y auditoría profunda.
*   **`api/v1/endpoints/devices.py`**: Controlador de persistencia. Expone los recursos almacenados para su consumo en el frontend.
*   **`api/v1/endpoints/system.py`**: Utilidades de mantenimiento y comprobación de dependencias del Sistema Operativo.

### 3. Capa de Servicio: `services/` (Lógica de Negocio)
Aquí se aplica el patrón **Service Layer** para desacoplar la API de los motores base.
*   **`services/scan_service.py`**: Es el **Orquestador de Negocio**. Su función es coordinar múltiples motores (Scanner + CVE) y transformar los datos crudos en información útil antes de enviarla a la capa de persistencia.
*   **`services/db_service.py`**: Encapsula todas las operaciones CRUD y consultas complejas hacia Firestore, evitando que el resto del sistema tenga que conocer los detalles de implementación de la base de datos.

### 4. Capa de Modelado: `schemas/`
Utilizamos **Pydantic** para definir **DTOs (Data Transfer Objects)**. Estos modelos garantizan la integridad de los datos mediante validaciones de tipo en tiempo de ejecución, asegurando que los payloads recibidos cumplan estrictamente con lo que el backend requiere.

### 5. Motores Base: `core/`
Son las herramientas de bajo nivel o adaptadores de terceros.
*   **`scanner.py`**: Wrapper de Nmap.
*   **`firebase_client.py`**: Implementa el patrón **Singleton**. Garantiza que solo exista una instancia de conexión hacia Google Cloud, optimizando el uso de recursos y sockets HTTPS.
*   **`installer.py`**: Subsistema de automatización de instalación de binarios nativos.

---

## 🧠 Glosario Técnico para Tesis

*   **Singleton Pattern:** Usado en Firebase para no re-inicializar el SDK en cada consulta, lo que ahorra tiempo de respuesta y memoria.
*   **Decoupling (Desacoplamiento):** Haber separado los servicios permite que si mañana cambias Nmap por otra herramienta (ej: ZMap), solo tendrías que modificar el archivo del motor en `core/`, y tu interfaz web ni lo notaría.
*   **Asynchronous Orchestration:** El uso de n8n para paralelizar llamadas a los endpoints atómicos de FastAPI demuestra una arquitectura escalable y distribuida.
*   **Payload Validation:** El uso de Pydantic Models previene ataques de inyección de datos malformados en los puntos finales de la API.
