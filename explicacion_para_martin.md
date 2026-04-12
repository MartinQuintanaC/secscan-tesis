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
*   **`installer.py`**: El instalador automático.

---

## 🔒 Capa de Seguridad (Autenticación)

Para el Sprint 12, añadimos una capa de seguridad de nivel industrial:

### 1. El Portero Digital (JWT/Bearer)
Cada vez que haces login en el frontend, Google nos entrega un **ID Token (JWT)**. Este es como un "Pasaporte Digital" temporal. El frontend guarda este pasaporte y lo envía en el bolsillo de cada petición (Header `Authorization: Bearer`).

### 2. Verificación en Backend (`api/deps.py`)
El backend no confía en nadie. Cada vez que recibe una orden de escaneo, toma ese "Pasaporte Digital" y le pregunta a los servidores de Google: *"¿Es este Martín realmente quien dice ser?"*. Si la respuesta es sí, se permite la operación. Si no, se bloquea con un error **401 Unauthorized**.

### 3. Estado Global (Context API)
En el frontend usamos `AuthContext`. Esto permite que toda la aplicación sepa si estás logueado, quién eres (Nombre y Foto) y maneja el cierre de sesión de forma segura.

---

## 🧠 Glosario Técnico para Tesis (Actualizado)

*   **Firebase Auth:** Servicio de identidad que delegamos a Google para no tener que guardar contraseñas nosotros mismos (cumpliendo con normativas de privacidad).
*   **JWT (JSON Web Token):** El formato estándar de los tokens de seguridad que viajan entre tu navegador y el servidor.
*   **Protected Routes:** Componentes de React que actúan como "muros": si no detectan una sesión activa, te expulsan automáticamente hacia la página de Login.
*   **Singleton Pattern:** Usado en Firebase para no re-inicializar el SDK en cada consulta, lo que ahorra tiempo de respuesta y memoria.
*   **Decoupling (Desacoplamiento):** Haber separado los servicios permite que si mañana cambias Nmap por otra herramienta (ej: ZMap), solo tendrías que modificar el archivo del motor en `core/`, y tu interfaz web ni lo notaría.
*   **Asynchronous Orchestration:** El uso de n8n para paralelizar llamadas a los endpoints atómicos de FastAPI demuestra una arquitectura escalable y distribuida.
*   **Payload Validation:** El uso de Pydantic Models previene ataques de inyección de datos malformados en los puntos finales de la API.
