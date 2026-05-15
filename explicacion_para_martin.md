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
*   **`services/scan_service.py`**: Es el **Orquestador de Negocio**. Su función es coordinar múltiples motores (Scanner + CVE) y transformarlos datos crudos en información útil antes de enviarla a la capa de persistencia.
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
*   **Heurística de Red:** Uso de algoritmos de deducción en el frontend para inferir partes de la red que están escondidas por firewalls, permitiendo pintar el mapa completo aunque falten piezas de información directa.

---

## 🖥️ Topología y Heurística (Fase 1)

### ¿Qué es un "Gateway Inferido" y por qué es tan valioso?
Cuando escaneas redes masivas institucionales (universidades, corporativos), los administradores de TI configuran los routers (Gateways) para que sean invisibles y bloqueen herramientas como Traceroute o Ping (ICMP Bloqueado). Si el Router Local bloquea nuestra sonda, el árbol debería teóricamente "romperse" al no saber de dónde cuelgan las PCs.

Sin embargo, aquí entra la **magia heurística de SecScan**. Nuestro software razona: *"Acabo de encontrar 15 computadoras en la red `65.52.99.x`. Las leyes de redes dictan que tiene que existir una puerta de salida para ellas, aunque no me responda"*. En ese momento, el Frontend crea matemáticamente un **"Gateway Inferido"** (asignándole la IP teórica `.1`) y anida todas las PCs debajo de él. 

Esto le demuestra a los evaluadores de la tesis que tu sistema no falla ante bloqueos, sino que **reconstruye lógicamente** la topología de la red evadiendo las políticas restrictivas de los Firewalls corporativos.

### ¿Por qué el "Router Principal" tiene la IP como `unknown`?
El árbol de SecScan es lineal desde Internet hacia ti:
Internet ➔ Router ISP ➔ Router Principal (Firewall del campus) ➔ Routers Intermedios (Edificios/Pabellones) ➔ Gateway (Tu sala) ➔ Tu PC.

Si en la red del instituto el Router Principal (el gran Firewall perimetral) está configurado para rechazar escaneos, SecScan pintará un nodo que dirá `Router Principal (C) - unknown`. Lejos de ser un error, **es una radiografía perfecta de un perímetro de seguridad militarizado**. SecScan sabe que hay un aparato enorme allí protegiendo el acceso a la nube, pero detectó que este aparato está omitiendo su nombre e IP a propósito. SecScan documenta la existencia de este nodo fantasma, dándote visibilidad completa de cuántas capas de hardware hay entre tu laptop y el proveedor de Internet.

### ¿Qué le dices al profesor si pregunta por los Nodos Invisibles y el NAT?
> *"Las redes empresariales no son planas; utilizan subredes profundas y bloqueos de seguridad. Mi sistema cuenta con un motor heurístico que detecta Doble NAT (cuando un router esconde otra subred por debajo) y soporta bloqueos ICMP. Si un Firewall intercepta la traza, SecScan no genera un error; en su lugar, clasifica el salto como 'Invisible' y mantiene intacta la jerarquía del árbol. Además, si un Gateway de piso deniega el rastreo, el frontend ejecuta una Inferencia Matemática: si hay clientes en una subred, deduce la existencia y dirección del Gateway faltante, graficándolo como un 'Gateway Inferido'."*

---

## 🖥️ Resolución de Nombres de Dispositivos (Hostname)

### ¿Qué es el Hostname y por qué lo agregamos?
Imagínate que tu red es un edificio de departamentos. Cada dispositivo tiene un número de departamento (la **IP**, ej. `192.168.18.51`). Pero en la vida real, tú no vas al "departamento 51", vas a "la casa de Sebastián" o "la oficina de contabilidad". Ese nombre amigable es el **hostname**: el nombre real del equipo dentro de la red.

Lo agregamos porque tu profesor hizo una observación muy válida: si ya sabemos dónde vive cada dispositivo (IP) y quién lo fabricó (MAC), lo lógico es también saber cómo se llama.

### ¿Cómo intenta SecScan encontrar el nombre?
SecScan es como un detective que no se rinde fácil. Si el primer método falla, prueba el segundo, y si ese falla también, prueba el tercero:

1. **Primer intento — Preguntarle a Nmap:** Nmap a veces ya sabe el nombre porque el router se lo dijo durante el escaneo. Es el método más rápido.

2. **Segundo intento — Preguntarle al router (DNS):** Si Nmap no sabe, el sistema le pregunta directamente al "directorio telefónico" de tu red (el servidor DNS del router): *"Oye, ¿cómo se llama el que vive en la IP .51?"*. El router, si tiene el registro, responde con el nombre.

3. **Tercer intento — NetBIOS (hablar el idioma Windows):** Windows tiene su propio protocolo antiguo para anunciarse en la red, llamado NetBIOS. Es como si el dispositivo gritara su nombre en la red local. SecScan lo escucha y lo captura.

### ¿Por qué algunos aparecen como "👻 Dispositivo Oculto"?
Los celulares modernos (iPhone, Android) son muy celosos de su privacidad. Por diseño, **no responden** a ninguna de esas preguntas. Es como un vecino que no tiene su nombre en el timbre y no abre la puerta aunque toques. Eso no es un error de SecScan, es una limitación del protocolo que el sistema detecta correctamente y lo muestra con honestidad.
