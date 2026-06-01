import requests
import os

class SegipService:

    BASE_URL = os.getenv(
        "SEGIP_URL",
        "http://segip:5001"
    )

    HEADERS = {
        "Authorization": "Bearer TSE-SECRET-KEY-2025"
    }

    @staticmethod
    def verificar_ci(ci):

        response = requests.get(
            f"{SegipService.BASE_URL}/ciudadano/{ci}",
            headers=SegipService.HEADERS
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    @staticmethod
    def obtener_ciudadanos():

        response = requests.get(
            f"{SegipService.BASE_URL}/ciudadanos",
            headers=SegipService.HEADERS
        )
        response.raise_for_status()
        return response.json()