from core.firebase_client import FirebaseDB
import datetime

class DatabaseService:
    def __init__(self):
        self.db = FirebaseDB().get_db()

    def get_historial_doc(self, id_unico: str):
        return self.db.collection("historial").document(id_unico).get()

    def save_historial_doc(self, id_unico: str, data: dict):
        self.db.collection("historial").document(id_unico).set(data)

    def save_device(self, ip: str, document: dict):
        self.db.collection("devices").document(ip).set(document)

    def save_vulnerability(self, cve_id: str, data: dict):
        self.db.collection("vulnerabilities").document(cve_id).set(data)

    def clear_devices(self):
        """Limpia todos los dispositivos del escaneo anterior (estado actual)."""
        docs = self.db.collection("devices").stream()
        for doc in docs:
            doc.reference.delete()
        print("🧹 Colección 'devices' limpiada para nuevo escaneo.")

    def clear_vulnerabilities(self):
        """Limpia las vulnerabilidades del escaneo anterior."""
        docs = self.db.collection("vulnerabilities").stream()
        for doc in docs:
            doc.reference.delete()
        print("🧹 Colección 'vulnerabilities' limpiada para nuevo escaneo.")

    def get_all_devices(self):
        try:
            docs = self.db.collection("devices").stream()
            devices = [doc.to_dict() for doc in docs]
            if not devices:
                print("⚠️ Colección 'devices' vacía. Se recreará con el próximo escaneo.")
            return devices
        except Exception as e:
            print(f"❌ Error al leer 'devices': {e}. Retornando lista vacía.")
            return []

    def get_all_vulnerabilities(self):
        try:
            docs = self.db.collection("vulnerabilities").stream()
            vulns = [doc.to_dict() for doc in docs]
            vulns.sort(key=lambda x: x.get("score", 0), reverse=True)
            return vulns
        except Exception as e:
            print(f"❌ Error al leer 'vulnerabilities': {e}. Retornando lista vacía.")
            return []

    def run_db_test(self):
        self.db.collection("tests").add({
            "origen": "FastAPI Modular",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "mensaje": "Arquitectura Modular funcionando."
        })
