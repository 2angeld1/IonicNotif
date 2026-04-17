import os
import json
import base64
from google import genai
from google.genai import types
from typing import List, Dict, Optional
from app.database import get_database
from app.config import get_settings

class ShoppingService:
    """
    Servicio 'Presupuestario' de Caitlyn.
    Relaciona listas de compras (voz, texto o foto) con estimaciones de precios en Panamá.
    """
    
    _client = None

    SYSTEM_PROMPT = (
        "Eres Caitlyn, la experta en presupuestos de Kitchy para el mercado de Panamá. "
        "Tu misión es convertir una lista de compras (que puede venir de voz, texto pegado o una foto) "
        "en un objeto JSON estructurado con nombres de productos, cantidades y PRECIOS ESTIMADOS. "
        "\n\n"
        "REGLAS DE PRECIOS EN PANAMÁ:\n"
        "- Conoces los precios promedio de supermercados como El Rey, Xtra, Riba Smith y Merca Panamá.\n"
        "- Si el usuario no especifica precio, ESTIMARLO basándote en el mercado actual panameño (USD).\n"
        "- Ejemplo: Leche (1L) ~$1.50 - $1.80, Pan molde grande ~$2.50, Queso prensado (lb) ~$3.50.\n"
        "- Devuelve siempre un JSON con esta estructura:\n"
        "{\n"
        '  "items": [\n'
        '    {\n'
        '      "nombre": "string",\n'
        '      "cantidad": number,\n'
        '      "unidad": "string (eg: ud, lb, kg, litro)",\n'
        '      "precioEstimado": number,\n'
        '      "esEstimado": true\n'
        '    }\n'
        '  ],\n'
        '  "totalEstimado": number\n'
        "}\n\n"
        "IMPORTANTE: Responde ÚNICAMENTE con el JSON. Usa español con tildes (UTF-8)."
    )

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            cls._client = genai.Client(api_key=api_key)
        return cls._client

    @classmethod
    async def parse_shopping_list(cls, text: Optional[str] = None, image_base64: Optional[str] = None) -> Dict:
        """
        Usa Gemini para parsear una lista y estimar precios.
        """
        client = cls._get_client()
        
        contents = []
        if image_base64:
            if "," in image_base64:
                header, encoded = image_base64.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
            else:
                encoded = image_base64
                mime_type = "image/jpeg"
            
            image_bytes = base64.b64decode(encoded)
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        
        if text:
            contents.append(text)

        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash", # Estable para producción
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=cls.SYSTEM_PROMPT,
                )
            )
            
            # Limpiar y parsear JSON
            raw_text = response.text.strip()
            # Quitar bloques de código si Gemini los pone
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            data = json.loads(raw_text)
            return {"success": True, "data": data}
        except Exception as e:
            print(f"Error en ShoppingService: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    async def save_historical_price(cls, item_name: str, price: float, negocio_id: str):
        """
        Guarda un precio real reportado para que Caitlyn aprenda.
        """
        db = get_database(get_settings().kitchy_database_name)
        await db["shopping_history"].update_one(
            {"item_name": item_name.lower(), "negocio_id": negocio_id},
            {
                "$set": {
                    "last_price": price,
                    "updated_at": os.times()[4] # timestamp aproximado
                },
                "$push": {
                    "history": {"price": price, "date": os.times()[4]}
                }
            },
            upsert=True
        )
