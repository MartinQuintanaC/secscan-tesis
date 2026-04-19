# 📑 Documento de Traspaso de Proyecto: SecScan

Este documento resume la arquitectura técnica y el estado del desarrollo hasta el Checkpoint de abril de 2026. Es la "Biblia" del proyecto.

## 1. Arquitectura del Sistema (Flujo "Turbo" con n8n)
El sistema utiliza una arquitectura de microservicios híbrida diseñada para el alto rendimiento y la escalabilidad:

- **Frontend (React + Vite)**: Interfaz de usuario premium que maneja la autenticación con Firebase (Google Login) y genera un `scanId` (UUID) único por sesión para garantizar que no se dupliquen datos.
- **BFF (Backend-for-Frontend - FastAPI)**: Actúa como el orquestador principal. Recibe el escaneo, valida el JWT del usuario, limpia los datos temporales y dispara el webhook de n8n pasando el token real y el ID de escaneo.
- **n8n (Motor de Orquestación)**: Procesa el escaneo en paralelo. Llama a los servicios internos de descubrimiento y escaneo profundo. Actúa como un puente seguro entre el usuario y las herramientas de red.
- **Backend Interno (FastAPI)**: Rutas protegidas (`/internal/*`) que solo n8n puede llamar mediante una `INTERNAL_API_KEY`. Estas rutas realizan la validación final del JWT para extraer la identidad real del usuario directamente del token de Google.

## 2. Sistema de Trazabilidad y Logs (Los "Prints")
Para depurar el flujo asíncrono (donde n8n trabaja en segundo plano), hemos implementado un sistema de logs visuales en la terminal:

- 🚀 **[BFF] Iniciando Escaneo**: Confirma que el frontend ha enviado la petición correctamente al servidor.
- 👤 **Usuario: [UID]**: Muestra quién está escaneando según el token.
- **[N8N -> BACKEND] Petición Recibida**: El hito más importante. Confirma que n8n ha logrado "volver" al backend para entregar resultados.
- ✅ **[OK] Usuario Identificado**: Confirma que el backend ha validado el token de n8n y ha recuperado la identidad real del usuario para guardar los datos.

## 3. Progreso: Base de Datos Multi-Tenant e Idempotencia
Este es el núcleo de la tesis y el mayor avance técnico logrado:

- **Aislamiento Total**: Se ha pasado de una estructura plana a una jerarquía profesional en Firestore:
  - `users/{uid}/profile`: Datos del perfil del usuario.
  - `users/{uid}/scans/{scanId}/devices/{ip}`: Cada escaneo es una "cápsula" de tiempo independiente. Esto permite ver el historial de qué dispositivos había en la red en una fecha específica.
- **Idempotencia con scanId**: Mediante el `scan_id` generado en el frontend, el sistema ignora peticiones duplicadas. Si n8n intenta enviar el mismo dispositivo dos veces por error de red, el backend detecta el ID y solo lo guarda una vez.
- **Seguridad de Identidad**: El sistema ya no confía en el `user_id` que le envían (que podría ser falsificado), sino que lo extrae siempre del Token JWT firmado por Google.

## Estado Actual para la Nueva Conversación:
- **Backend**: Listo y configurado con validación de tokens y rutas internas.
- **n8n**: Workflow configurado con Headers de seguridad y expresiones dinámicas conectadas al nodo Webhook.
- **Frontend**: Generando UUIDs y pasando tokens reales.
- **Base de Datos**: Estructura jerárquica implementada en `db_service.py` y `scan_service.py`.

## 4. Conceptos Clave para la Defensa de Tesis (Sprint Actual)
A continuación se explican los conceptos técnicos avanzados implementados para la gestión del historial y el flujo paralelo:

### A. Cápsulas de Tiempo (Time Capsules) y Auditoría Inmutable
SecScan no solo muestra el estado en vivo de una red, sino que genera "Cápsulas de Tiempo" (`users/{uid}/scans/{scanId}`). 
- **¿Qué son?** Son snapshots (instantáneas) inmutables que congelan el estado exacto de la red (dispositivos y vulnerabilidades) en el milisegundo en que ocurrió el escaneo. 
- **¿Para qué sirven en la industria?** Cumplen con los estándares de *Auditoría y Compliance*. Permiten a un administrador probar que en una fecha "X" el sistema no era vulnerable (o sí lo era). Si un dispositivo se desconecta mañana, la cápsula de hoy guarda evidencia de que estuvo conectado.
- **Diseño Glassmorphism:** La UI de las cápsulas utiliza colores reactivos (Cyan para 0 riesgos, Rojo para >0 riesgos) alertando visualmente al operador de ciberseguridad sobre anomalías históricas sin necesidad de leer todo el reporte.

### B. Consistencia de Datos en Entornos Altamente Paralelos (Contadores Atómicos)
El uso de n8n introduce el desafío del procesamiento en paralelo masivo (concurrencia). Como n8n escanea múltiples dispositivos al mismo tiempo en hilos separados, el backend no puede saber en qué momento exacto termina "todo" el escaneo para hacer una suma global de las vulnerabilidades.
- **El Problema de Condición de Carrera (Race Condition):** Si 10 hilos intentan leer, sumar y actualizar un contador global al mismo tiempo, los datos se sobrescribirían y la suma final sería errónea (por ejemplo, mostraría un `?` o un número incorrecto).
- **La Solución (Operaciones Atómicas):** Implementamos `firestore.Increment()`. En lugar de que cada hilo lea y escriba el total, cada hilo le envía una instrucción matemática directa al servidor de base de datos de Google: *"Suma +1 a la cuenta actual"*. Al ser una transacción atómica a nivel de hardware/base de datos, se garantiza una exactitud matemática del 100% en el resumen de la cápsula de tiempo, independientemente de cuántos hilos de n8n disparen peticiones simultáneas.
