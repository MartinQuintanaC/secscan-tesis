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

    def get_all_devices(self):
        docs = self.db.collection("devices").stream()
        return [doc.to_dict() for doc in docs]

    def get_all_vulnerabilities(self):
        docs = self.db.collection("vulnerabilities").stream()
        vulns = [doc.to_dict() for doc in docs]
        vulns.sort(key=lambda x: x.get("score", 0), reverse=True)
        return vulns

    def run_db_test(self):
        self.db.collection("tests").add({
            "origen": "FastAPI Modular",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "mensaje": "Arquitectura Modular funcionando."
        })
