import os
import firebase_admin
from firebase_admin import credentials, firestore

class FirebaseDB:
    _instance = None
    
    def __new__(cls):
        # Patrón Singleton para mantener 1 sola tubería HTTPS hacia Google (Mejora Performance)
        if cls._instance is None:
            cls._instance = super(FirebaseDB, cls).__new__(cls)
            
            # Buscamos la ruta absoluta de nuestro archivo de llave para evitar errores de directorio
            ruta_actual = os.path.dirname(os.path.abspath(__file__))
            ruta_llave = os.path.join(ruta_actual, '..', 'firebase_admin.json')
            
            try:
                # Iniciamos Firebase (evitando reiniciarlo duplicado si FastAPI recarga la página)
                if not firebase_admin._apps:
                    cred = credentials.Certificate(ruta_llave)
                    firebase_admin.initialize_app(cred)
                cls._instance.db = firestore.client()
                print("🚀 Conexión a Firebase Firestore establecida con éxito.")
            except Exception as e:
                print(f"❌ Error al iniciar Firebase: {str(e)}")
                raise e
        return cls._instance

    def get_db(self):
        return self.db
