# Guía de Instalación en un Nuevo Computador (SecScan)

Como tu proyecto ya está en GitHub, moverlo a otra PC es muy sencillo. Sigue estos pasos exactos para que todo funcione a la primera:

---

## 1. Requisitos Previos (Instalar en la nueva PC)
Primero, asegúrate de que la nueva computadora tenga estas 3 herramientas:
*   **Git:** Para bajar el código ([Descargar aquí](https://git-scm.com/)).
*   **Python (3.10 o superior):** Para el Backend. Al instalarlo, marca la casilla que dice **"Add Python to PATH"**.
*   **Node.js (v18 o superior):** Para el Frontend y n8n ([Descargar aquí](https://nodejs.org/)).

---

## 2. Bajar el Código
Abre una terminal (PowerShell o CMD) y escribe:
```powershell
cd Desktop
git clone https://github.com/MartinQuintanaC/secscan-tesis.git
cd secscan-tesis
```

---

## 3. Configurar el Backend (Cerebro)
```powershell
cd backend
# Crear el entorno virtual
python -m venv venv
# Activar el entorno
.\venv\Scripts\activate
# Instalar las librerías
pip install -r requirements.txt
```

> [!IMPORTANT]
> **Paso Secreto (Credenciales):** Por seguridad, el archivo `firebase_admin.json` **no está en GitHub**. Tienes que copiar ese archivo manualmente de tu computadora actual a la carpeta `backend` de la nueva PC. Si no lo haces, el programa no podrá conectarse a la base de datos.

---

## 4. Configurar el Frontend (Interfaz)
Abre otra terminal en la carpeta principal del proyecto:
```powershell
cd frontend
npm install
```

---

## 5. El Orquestador (n8n)
En una tercera terminal, ejecuta:
```powershell
npx n8n
```
Si es la primera vez en esa PC, te pedirá permiso para instalarlo; dile que **"y"** (sí).
Una vez que inicie, haz lo siguiente:
1. Abre tu navegador y ve a `http://localhost:5678`.
2. Configura tu cuenta local (pon cualquier correo y contraseña, es solo para ti).
3. En el menú, ve a **Workflows** y haz clic en **Import from File**.
4. Selecciona el archivo `workflow_secscan_n8n.json` que viene incluido en la carpeta del proyecto.
5. Arriba a la derecha, pon el switch en **Active** (Verde).

---

## 6. ¡El Toque Maestro! (Motor Nmap)
¡No instales Nmap a mano!
1. Inicia tu backend (`uvicorn main:app --reload`).
2. Entra a tu Dashboard en `http://localhost:5173`.
3. El sistema detectará que la PC es nueva y te mostrará el aviso de **"Motor Nmap Ausente"**.
4. ¡Dale click al botón **Instalar Automáticamente** que programamos hoy y deja que SecScan se configure solo!

---

## Resumen de inicio diario
Una vez instalado todo, para usarlo cada día solo necesitas correr estos 3 comandos en terminales separadas:
1. `npx n8n`
2. `cd backend; .\venv\Scripts\uvicorn app:app --reload`
3. `cd frontend; npm run dev`
