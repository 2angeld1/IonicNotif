"""
VentasNotebookService — Procesamiento de hojas de ventas manuscritas (cuadernos).
Caitlyn recibe la imagen base64 del cuaderno, la envía a Gemini y devuelve
una lista estructurada de ventas detectadas para importar al POS.
"""
import os
import json
import base64
import re
from google import genai
from google.genai import types
from typing import Optional, List, Dict
from app.config import GEMINI_MODELS

class VentasNotebookService:
    """Servicio dedicado a la extracción de ventas desde fotos de cuadernos o libretas."""
    
    _client = None

    SYSTEM_PROMPT = (
        "Eres Caitlyn, un asistente de inteligencia artificial para negocios. "
        "Recibirás una imagen de una hoja de cuaderno, libreta o papel donde se anotaron ventas a mano. "
        "Tu tarea es extraer cada venta individual detectada. "
        "REGLA DE ORO: Si no puedes leer algo con claridad, usa tu mejor juicio basado en el contexto del negocio. "
        "Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin bloques de código markdown. "
        "La estructura debe ser exactamente esta:\n"
        "{\n"
        '  "ventas": [\n'
        '    {\n'
        '      "cliente": "string (nombre del cliente o \"Venta General\")", \n'
        '      "items": [\n'
        '        {\n'
        '          "nombre": "string", \n'
        '          "cantidad": number, \n'
        '          "precio": number\n'
        '        }\n'
        '      ],\n'
        '      "total": number,\n'
        '      "fecha": "ISO string o null",\n'
        '      "metodoPago": "string (efectivo | ach | tarjeta | ippp | null)"\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "REGLAS DE EXTRACCIÓN:\n"
        "- A menudo los nombres de productos están abreviados (ej: 'Pol' para Pollo). Intenta normalizarlos.\n"
        "- BUSCA MÉTODOS DE PAGO: Identifica palabras clave como 'ef'/'cash' (efectivo), 'ach'/'yap'/'yappy' (ach), 'tar'/'targs' (tarjeta), 'ippp' (punto de pago).\n"
        "- Si solo hay un precio total por venta, pon el item como 'Consumo' o el nombre más probable.\n"
        "- Si detectas una fecha en la hoja, aplícala a las ventas de esa sección.\n"
        "- Responde en español con tildes reales (UTF-8).\n"
    )

    @classmethod
    def _get_client(cls):
        """Inicializa el cliente de Gemini de forma lazy."""
        if cls._client is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en .env")
            
            cls._client = genai.Client(api_key=api_key)
            print("🤖 VentasNotebookService: Cliente GenAI inicializado.")
        return cls._client

    @classmethod
    def _parse_base64_image(cls, image_data: str) -> tuple[bytes, str]:
        """Extrae los bytes y el mime type de un string base64."""
        if image_data.startswith("data:"):
            header, encoded = image_data.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]
        else:
            encoded = image_data
            mime_type = "image/jpeg"
        
        image_bytes = base64.b64decode(encoded)
        return image_bytes, mime_type

    @classmethod
    async def process_notebook(cls, image_data: str) -> dict:
        """
        Toma una foto de una hoja de ventas de cuaderno (base64 o URL) y extrae las ventas.
        """
        try:
            client = cls._get_client()
            
            # Detectar si es URL (de Cloudinary u otro) o Base64
            if image_data.startswith("http"):
                import httpx
                print(f"🌐 VentasNotebookService: Descargando imagen desde URL...")
                async with httpx.AsyncClient() as httpx_client:
                    resp = await httpx_client.get(image_data)
                    image_bytes = resp.content
                    mime_type = resp.headers.get("Content-Type", "image/jpeg")
            else:
                image_bytes, mime_type = cls._parse_base64_image(image_data)
            
            print(f"📖 VentasNotebookService: Procesando cuaderno ({len(image_bytes)} bytes) con {mime_type}")
            
            # Usar el mismo modelo que InvoiceService
            response = await client.aio.models.generate_content(
                model=GEMINI_MODELS[0],
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ],
                config=types.GenerateContentConfig(
                    system_instruction=cls.SYSTEM_PROMPT,
                )
            )
            
            raw_text = response.text.strip()
            extracted_data = cls._parse_response(raw_text)
            
            ventas = extracted_data.get("ventas", []) if isinstance(extracted_data, dict) else []
            
            return {
                "success": True,
                "ventas": ventas,
                "total_detectadas": len(ventas),
                "mensaje": f"Se detectaron {len(ventas)} ventas en el cuaderno."
            }

        except Exception as e:
            print(f"🚨 Error Crítico en VentasNotebookService: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "ventas": [],
                "total_detectadas": 0,
                "error": f"IA Error: {str(e)}"
            }

    @classmethod
    def _parse_response(cls, raw_text: str) -> dict:
        """Intenta parsear la respuesta de Gemini como JSON."""
        # Limpieza de posibles bloques markdown
        clean_text = raw_text
        if "```" in raw_text:
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_text, re.DOTALL)
            if match:
                clean_text = match.group(1)
        
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            # Intento desesperado: buscar el primer { y el último }
            start = clean_text.find('{')
            end = clean_text.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(clean_text[start:end+1])
                except:
                    pass
            print(f"⚠️ No se pudo parsear JSON del cuaderno: {raw_text[:100]}...")
            return {"ventas": []}
