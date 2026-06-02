import requests
import os

class SegipService:
    
    def __init__(self):
        self.base_url = os.getenv(
            "SEGIP_URL",
            "http://segip:5001"
        )
        self.api_key = os.getenv(
            "SGIP_API_KEY",
            "TSE-SECRET-KEY-2025 "
        )
        
        self.headers = {
        "Autorizacion" : f"Bearer {self.api_key}"
        }

    def obtener_cuidano(self, ci:str) -> dict | None:
        try:
            response = requests.get(
                f"{self.base_url}/cuidadano/{ci}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get("valido"):
                return None
            
            return data
        except Exception as e:
            print(f"[SEGIP] ERROR obteniendo cuidadano: {e}")
            return None
        
        
        
    def obtener_cuidadanos(self) -> list:
        try:
            response = requests.get(
                f"{self.base_url}/cuidadanos",
                headers=self.headers,
                timeout=20
            )
            
            if response.status_code !=200:
                return []
            return response.json()
        except Exception as e:
            print(f"[SEGIP] Error obteniendo cuidadanos: {e}")
            return []