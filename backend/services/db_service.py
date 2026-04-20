from core.firebase_client import FirebaseDB
import datetime

class DatabaseService:
    def __init__(self):
        self.db = FirebaseDB().get_db()

    def _get_user_ref(self, user_id: str):
        """Obtiene referencia a la colección del usuario."""
        if not user_id:
            user_id = "anonymous"
        return self.db.collection("users").document(user_id)

    # ==================== MÉTODOS CON USER_ID ====================
    
    def get_historial_doc(self, id_unico: str, user_id: str = ""):
        user_ref = self._get_user_ref(user_id)
        return user_ref.collection("historial").document(id_unico).get()

    def save_historial_doc(self, id_unico: str, data: dict, user_id: str = ""):
        user_ref = self._get_user_ref(user_id)
        user_ref.collection("historial").document(id_unico).set(data)

    def save_device(self, ip: str, document: dict, user_id: str = ""):
        user_ref = self._get_user_ref(user_id)
        user_ref.collection("devices").document(ip).set(document)

    def save_vulnerability(self, cve_id: str, data: dict, user_id: str = ""):
        user_ref = self._get_user_ref(user_id)
        user_ref.collection("vulnerabilities").document(cve_id).set(data)

    def clear_devices(self, user_id: str = ""):
        """Limpia los dispositivos del usuario."""
        user_ref = self._get_user_ref(user_id)
        docs = user_ref.collection("devices").stream()
        for doc in docs:
            doc.reference.delete()
        print(f"[DB] Dispositivos de {user_id} limpiados.")

    def clear_vulnerabilities(self, user_id: str = ""):
        """Limpia las vulnerabilidades del usuario."""
        user_ref = self._get_user_ref(user_id)
        docs = user_ref.collection("vulnerabilities").stream()
        for doc in docs:
            doc.reference.delete()
        print(f"[DB] Vulnerabilidades de {user_id} limpiadas.")

    def get_all_devices(self, user_id: str = ""):
        try:
            user_ref = self._get_user_ref(user_id)
            docs = user_ref.collection("devices").stream()
            devices = [doc.to_dict() for doc in docs]
            return devices
        except Exception as e:
            print(f"[DB] Error al leer devices: {e}")
            return []

    def get_all_vulnerabilities(self, user_id: str = ""):
        try:
            user_ref = self._get_user_ref(user_id)
            docs = user_ref.collection("vulnerabilities").stream()
            vulns = [doc.to_dict() for doc in docs]
            vulns.sort(key=lambda x: x.get("score", 0), reverse=True)
            return vulns
        except Exception as e:
            print(f"[DB] Error al leer vulns: {e}")
            return []

    # ==================== MÉTODOS LEGACY (sin user_id) ====================
    # Mantenidos para compatibilidad hacia atrás
    
    def get_historial_doc_legacy(self, id_unico: str):
        return self.db.collection("historial").document(id_unico).get()

    def save_historial_doc_legacy(self, id_unico: str, data: dict):
        self.db.collection("historial").document(id_unico).set(data)

    def save_device_legacy(self, ip: str, document: dict):
        self.db.collection("devices").document(ip).set(document)

    def save_vulnerability_legacy(self, cve_id: str, data: dict):
        self.db.collection("vulnerabilities").document(cve_id).set(data)

    def clear_devices_legacy(self):
        docs = self.db.collection("devices").stream()
        for doc in docs:
            doc.reference.delete()
        print("[DB] Colección 'devices' limpiada.")

    def clear_vulnerabilities_legacy(self):
        docs = self.db.collection("vulnerabilities").stream()
        for doc in docs:
            doc.reference.delete()
        print("[DB] Colección 'vulnerabilities' limpiada.")

    def get_all_devices_legacy(self):
        try:
            docs = self.db.collection("devices").stream()
            return [doc.to_dict() for doc in docs]
        except:
            return []

    def get_all_vulnerabilities_legacy(self):
        try:
            docs = self.db.collection("vulnerabilities").stream()
            vulns = [doc.to_dict() for doc in docs]
            vulns.sort(key=lambda x: x.get("score", 0), reverse=True)
            return vulns
        except:
            return []

    def run_db_test(self):
        self.db.collection("tests").add({
            "origen": "FastAPI Modular",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "mensaje": "Arquitectura Modular funcionando."
        })

    # ==================== MÉTODOS DE IDEMPOTENCIA ====================
    
    def scan_exists(self, user_id: str, scan_id: str) -> bool:
        """Check if scan_id already processed (prevents duplicates)."""
        user_ref = self._get_user_ref(user_id)
        doc = user_ref.collection("scans").document(scan_id).get()
        return doc.exists
    
    def mark_scan_processed(self, user_id: str, scan_id: str, ip: str = ""):
        """Mark scan as processed for idempotency."""
        user_ref = self._get_user_ref(user_id)
        user_ref.collection("scans").document(scan_id).set({
            "status": "processed",
            "ip": ip,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }, merge=True)

    def update_scan_metadata(self, user_id: str, scan_id: str, metadata: dict):
        """Actualiza los metadatos de un escaneo (ej. conteos, finalización)."""
        user_ref = self._get_user_ref(user_id)
        user_ref.collection("scans").document(scan_id).set(metadata, merge=True)

    def increment_vulnerabilities(self, user_id: str, scan_id: str, amount: int):
        """Incrementa atómicamente el contador de vulnerabilidades de un escaneo."""
        from firebase_admin import firestore
        if amount > 0:
            user_ref = self._get_user_ref(user_id)
            user_ref.collection("scans").document(scan_id).set({
                "vulnerabilidades_found": firestore.Increment(amount)
            }, merge=True)

    def increment_devices(self, user_id: str, scan_id: str, amount: int = 1):
        """Incrementa atómicamente el contador de dispositivos de un escaneo."""
        from firebase_admin import firestore
        user_ref = self._get_user_ref(user_id)
        user_ref.collection("scans").document(scan_id).set({
            "devices_found": firestore.Increment(amount)
        }, merge=True)

    def create_user_profile(self, user_id: str, email: str = ""):
        """Create user profile when they first login."""
        user_ref = self._get_user_ref(user_id)
        user_ref.collection("profile").document("data").set({
            "createdAt": datetime.datetime.utcnow().isoformat(),
            "email": email,
            "status": "active"
        })

    def save_scan_device(self, user_id: str, scan_id: str, ip: str, data: dict):
        """Saves a device inside a specific scan session."""
        user_ref = self._get_user_ref(user_id)
        user_ref.collection("scans").document(scan_id).collection("devices").document(ip).set(data)

    def get_user_scans(self, user_id: str):
        """Devuelve el historial de escaneos del usuario."""
        try:
            user_ref = self._get_user_ref(user_id)
            docs = user_ref.collection("scans").order_by("timestamp", direction="DESCENDING").stream()
            scans = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                scans.append(data)
            return scans
        except Exception as e:
            print(f"[DB] Error al leer historial de escaneos: {e}")
            return []

    def get_scan_details(self, user_id: str, scan_id: str):
        """Devuelve los metadatos de un escaneo en particular."""
        try:
            user_ref = self._get_user_ref(user_id)
            doc = user_ref.collection("scans").document(scan_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            return None
        except Exception as e:
            print(f"[DB] Error al leer detalles del escaneo: {e}")
            return None

    def get_scan_devices(self, user_id: str, scan_id: str):
        """Devuelve todos los dispositivos de un escaneo en particular."""
        try:
            user_ref = self._get_user_ref(user_id)
            docs = user_ref.collection("scans").document(scan_id).collection("devices").stream()
            devices = [doc.to_dict() for doc in docs]
            return devices
        except Exception as e:
            print(f"[DB] Error al leer dispositivos del escaneo: {e}")
            return []
