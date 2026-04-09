# Guía de Explicación para Martín (SecScan)

Esta guía está diseñada especialmente para ti. Úsala para estudiar, repasar y explicar tu proyecto a cualquier profesor o jurado durante tu tesis. Usa las analogías, te harán sonar como un absoluto profesional de la ingeniería de software.

---

## 1. La Gran Analogía: ¿Qué es SecScan?
Imagina que aplicamos auditoría de seguridad a un "Edificio de Departamentos" (Tu Red WiFi).
SecScan no es solo una persona buscando problemas, es un **Equipo de Detectives Altamente Coordinado**.
*   **React (Frontend):** Es la oficina central. Aquí es donde tú (el usuario) pides informes y ves resultados bonitos.
*   **Python (Backend):** Es el jefe de policías. Él da las órdenes y controla las herramientas pesadas.
*   **n8n (Orquestador):** Es el gerente de recursos humanos. Si hay que registrar 10 departamentos, él divide a 10 policías para que lo hagan todos al mismo tiempo en vez de uno por uno.
*   **Nmap (Motor):** Es el policía táctico que va puerta por puerta.
*   **Firebase (Base de Datos):** Es el archivo de la comisaría donde todo queda anotado para siempre.

---

## 2. Botón "Escaneo General" (El flujo más importante)
Cuando aprietas el botón de Escaneo General, pasan **7 pasos mágicos** en cuestión de segundos:

1. **La Orden:** Aprietas el botón y la Oficina Central (React) le dice a Python: *"Oye, audita la red completa pero actúa en modo automático"*.
2. **Autodescubrimiento Inteligente:** Python no sabe en qué edificio está (si la IP es 192.168.1.x o 10.0.0.x). Usa una herramienta llamada "Socket" para enviar un zumbido, mirar su propia tarjeta de red y decir matemáticamente: *"Ah, estoy en la red 192.168.18.0"* (Esto se llama Arquitectura Zero-Configure o Agnóstica).
3. **El Disparo Inmediato:** Python le avisa al Orquestador (n8n): *"Empieza ya en la red 192.168.18.0"*.
4. **El Censo Rápido (Discover):** n8n llama a la herramienta Nmap para hacer un Censo Rápido. Le dice: *"Dime a quiénes ves encendidos, pero rápido"*. 
   * *El Truco Ninja (ARP + Caché):* Algunos celulares (como Roku o Samsung) se esconden de estos censos apagando sus respuestas de Ping de seguridad (ICMP). Así que Python los descubre "por la fuerza física" revisando el protocolo ARP (preguntándole directo al switch del router) y leyendo su propia memoria.
5. **División de Trabajo (Split In Batches):** Si Nmap descubre que hay 4 teléfonos/compus vivas, n8n crea 4 hilos distintos.
6. **El Escaneo de Puertos Profundo:** n8n le ordena a Python lanzar un ataque profundo a esos 4 aparatos, pero **al mismo tiempo** (Paralelismo). Nmap va y toca todos los puertos de esas 4 IP para ver qué "Puertas (Software)" están abiertas y qué versión de programa tienen.
7. **El Reporte a NVD:** Lo que sea que descubran, Python lo envía a la Casa Blanca de la Ciberseguridad (la base de datos NIST v2 de EE.UU.). Si la versión del software cruzado tiene una debilidad, se la baja, y mete todo el paquete ordenado en tu Base de Datos Firebase. La pantalla simplemente hace preguntas a Firebase y, ¡Boom! te dibuja las tarjetas solitas.

---

## 3. Botón "Escaneo Específico" (El modo Francotirador)
Aquí el proceso es lineal. No hay orquestador (no participa n8n) porque no hay paralelismo. Tú escribes expresamente "192.168.18.33" en un cuadro.  La web le dice directamente a Python que mande a Nmap a auditar esa pura IP. Todo el sistema se congela unos 10 segundos, obtiene la info directa de EE.UU., la guarda en la nube y te la devuelve en la pantalla de inmediato como si fuese el ticket de un supermercado.

---

## 4. Preguntas Fáciles que te puede hacer el Jurado

**Jurado:** *¿Por qué dicen que hay que presionar el botón "Publish" en n8n?*
**Tú:** Porque n8n levanta compuertas llamadas Webhooks. Si no "publico" el flujo, esa compuerta de acceso web tira error 404 porque no existe para el mundo exterior. Al publicar, se abre un puerto de escucha persistente para nuestro backend en Python.

**Jurado:** *¿Cómo es posible que tu programa sepa que mi equipo es un Huawei Samsung si solo conectas por WiFi?*
**Tú:** Porque el sistema realiza "MAC Vendor Fingerprinting". Cuando interceptamos sus paquetes en una red local con Nmap (`-PR`), todas las tarjetas de red físicas mundiales queman los primeros 3 bloques de su dirección (OUI) para indicar qué fabricante las hizo. Yo cruzo mis datos con la lista de la Asociación IEEE mundial.

**Jurado:** *¿Por qué un teléfono me sale como MAC Desconocida con este formato aleatorio `5A:36:3E...` en vez de salir "Samsung"?*
**Tú:** Porque mi escáner descubrió que el smartphone activó algo llamado "MAC Randomization". Android o iOS falsifican su identidad constantemente por privacidad para que los centros comerciales no los rastreen o auditen. La MAC mostrada (`5A...`) es temporal, por lo que matemáticamente es imposible de rastrear globalmente, ¡así que nosotros la detectamos por descarte!

**Jurado:** *¿Por qué utilizaste Firestore y no una base relacional como MySQL?*
**Tú:** Porque los escaneos de Vulnerabilidades de Nmap regresan objetos caóticos o árboles con tamaños de información distintos. Guardar árboles JSON anidados de forma ágil que crecen dependiendo el resultado del scan, es el caso de uso perfecto para bases documentales (NoSQL).
