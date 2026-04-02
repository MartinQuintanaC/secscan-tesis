# Plan de Implementación Ágil: SecScan (Versión Refinada)

Como este proyecto corresponde a una Tesis de Título (aprox. 10 a 12 semanas), tienes toda la razón: dividirlo solo en 4 Sprints generaba bloques de trabajo muy "pesados" y riesgosos. 

Objetivamente, para una tesis es mucho mejor **dividir el proyecto en 6 Sprints de 2 semanas cada uno**. Esto permite un desarrollo escalonado, menos estresante, y asegura que en cada entrega tengas algo funcional que mostrarle a tu profesor guía.

Además, **tomando una decisión ejecutiva desde un punto de vista objetivo**, te recomiendo fuertemente usar **React** para el frontend en lugar de Streamlit. Aunque Streamlit es más rápido, React + FastAPI demuestra una arquitectura "Desacoplada" estándar de la industria, lo cual elevará enormemente la nota y percepción de tu comité evaluador.

---

## Proposed Changes (Estructura de 6 Sprints)

### Sprint 1: Arquitectura y Base de Datos (Semanas 1-2)
**Objetivo:** Dejar configurado el entorno de trabajo y la Base de Datos para que sea capaz de guardar la información sin errores.
* Configuración del entorno virtual Python y FastAPI (`backend/main.py`).
* Creación de los modelos de Base de Datos en SQLite SQLAlchemy (`backend/database/models.py`).
* PRUEBA: Insertar un "escaneo falso" en la base de datos mediante la API.

### Sprint 2: Motor de Escaneo Local (Semanas 3-4)
**Objetivo:** Lograr que Python se comunique con la red real y descubra dispositivos reales.
* Integración de la librería `python-nmap` (`backend/core/scanner.py`).
* Lógica para escanear una IP o subred y extraer (Puertos Abiertos, Servicios y Versiones).
* PRUEBA: Escanear tu propio Computador y Router, y que se guarde en la Base de Datos.

### Sprint 3: Inteligencia de Vulnerabilidades (API) (Semanas 5-6)
**Objetivo:** Darle el "Cerebro" de ciberseguridad a la plataforma.
* Creación del motor de requests hacia la API pública (NIST NVD o Vulners) (`backend/core/cve_mapper.py`).
* Toma las versiones descubiertas en el Sprint 2 y se las envía a la API para recibir los CVEs y su puntaje de Severidad.
* PRUEBA: Lograr que la consola imprima "Vulnerabilidad Alta detectada" en algún servicio viejo.

### Sprint 4: Arquitectura Asíncrona (Semanas 7-8)
**Objetivo:** Optimización de nivel profesional. Como un escaneo tarda minutos, el sistema no puede quedarse "congelado".
* Refactorización de la ruta de escaneo en FastAPI para usar un gestor de tareas asíncronas (`BackgroundTasks` o Celery de ser necesario).
* PRUEBA: Lanzar un escaneo largo y comprobar que la API responde inmediatamente "Escaneo Iniciado", permitiendo seguir usando el sistema.

### Sprint 5: Desarrollo Frontend / Dashboard (Semanas 9-10)
**Objetivo:** Darle un rostro moderno y profesional al proyecto usando React (o Vue).
* Creación del proyecto React (`frontend/`).
* Consumo de los endpoints de FastAPI mediante `fetch` o `axios`.
* Diseño del Panel: Tarjetas con Semáforos (Crítico=Rojo, Medio=Naranja, Bajo=Verde) e historial de dispositivos.
* PRUEBA: Ver los resultados de la BBDD visualmente en el navegador.

### Sprint 6: Reportes, Pruebas y Cierre (Semanas 11-12)
**Objetivo:** Preparar el producto para la defensa de Tesis.
* Creación de un botón "Exportar a PDF" o "CSV" que genere un reporte de las vulnerabilidades encontradas.
* Limpieza de código, manejo de errores finales y preparación del documento de presentación.

---

## User Review Required

> [!IMPORTANT]
> **Visto Bueno del Plan de 6 Sprints:** Revisa estructuración a 6 Sprints. Esta división reduce el riesgo de estancarse y garantiza que las primeras semanas te enfoques 100% en la lógica dura (backend) antes de tocar colores o botones (frontend).
> 
> *¿Aceptas esta propuesta y la recomendación técnica de usar React para darle mayor madurez a la Tesis?* Si estás de acuerdo, daremos inicio de inmediato al **Sprint 1**, configurando los archivos base en tu carpeta local.
