"""
InvoiceService — Procesamiento de facturas con Gemini Flash.
Caitlyn recibe la imagen base64, la envía a Gemini y devuelve
una lista estructurada de productos detectados.
"""
import os
import json
import base64
import re
import google.generativeai as genai
from typing import Optional


class InvoiceService:
    """Servicio dedicado a la extracción de productos desde imágenes de facturas."""
    
    _model = None

    SYSTEM_PROMPT = (
        "Eres un asistente de inventario de restaurante. "
        "Recibirás la imagen de una factura o ticket de compra. "
        "Tu tarea es extraer TODOS los productos listados con su cantidad, unidad, nombre y precio unitario. "
        "Responde ÚNICAMENTE con un JSON array válido, sin texto adicional, sin markdown, sin backticks. "
        "Cada elemento del array debe tener esta estructura exacta:\n"
        '{"nombre": "string", "cantidad": number, "unidad": "string", "precioUnitario": number}\n\n'
        "Reglas:\n"
        "- Si la unidad no es clara, usa 'unidades'.\n"
        "- Si el precio unitario no es visible pero hay un total y cantidad, calcula el unitario.\n"
        "- El nombre debe ser descriptivo pero corto (ej: 'Aceite de oliva 1L', 'Tomate cherry').\n"
        "- No incluyas impuestos, totales ni información del negocio.\n"
        "- Si no puedes leer algún campo, usa null.\n"
        "- SIEMPRE responde con el JSON array, incluso si está vacío: []\n"
    )

    @classmethod
    def _get_model(cls):
        """Inicializa el modelo de Gemini de forma lazy."""
        if cls._model is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en .env")
            
            genai.configure(api_key=api_key)
            cls._model = genai.GenerativeModel("gemini-2.0-flash")
            print("🤖 InvoiceService: Gemini Flash inicializado.")
        return cls._model

    @classmethod
    def _parse_base64_image(cls, image_data: str) -> tuple[bytes, str]:
        """
        Extrae los bytes y el mime type de un string base64.
        Soporta formatos: 'data:image/jpeg;base64,...' o base64 puro.
        """
        if image_data.startswith("data:"):
            # Formato data URI
            header, encoded = image_data.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]
        else:
            # Base64 puro, asumimos JPEG
            encoded = image_data
            mime_type = "image/jpeg"
        
        image_bytes = base64.b64decode(encoded)
        return image_bytes, mime_type

    @classmethod
    async def process_invoice(cls, image_base64: str) -> dict:
        """
        Procesa una imagen de factura y extrae los productos.
        
        Args:
            image_base64: Imagen en formato base64 (con o sin data URI prefix)
            
        Returns:
            dict con 'productos' (lista) y 'raw_response' (texto crudo de Gemini)
        """
        try:
            model = cls._get_model()
            image_bytes, mime_type = cls._parse_base64_image(image_base64)
            
            print(f"📸 InvoiceService: Procesando imagen ({len(image_bytes)} bytes, {mime_type})")
            
            # Construir el contenido multimodal para Gemini
            response = model.generate_content([
                cls.SYSTEM_PROMPT,
                {
                    "mime_type": mime_type,
                    "data": image_bytes
                }
            ])
            
            raw_text = response.text.strip()
            print(f"📝 Gemini respondió: {raw_text[:200]}...")
            
            # Parsear la respuesta JSON
            productos = cls._parse_response(raw_text)
            
            return {
                "success": True,
                "productos": productos,
                "total_detectados": len(productos),
                "raw_response": raw_text
            }
            
        except ValueError as e:
            print(f"⚠️ InvoiceService config error: {e}")
            return {
                "success": False,
                "productos": [],
                "total_detectados": 0,
                "error": str(e)
            }
        except Exception as e:
            print(f"💥 InvoiceService error: {e}")
            return {
                "success": False,
                "productos": [],
                "total_detectados": 0,
                "error": f"Error procesando factura: {str(e)}"
            }

    @classmethod
    def _parse_response(cls, raw_text: str) -> list:
        """
        Intenta parsear la respuesta de Gemini como JSON.
        Maneja casos donde Gemini envuelve el JSON en markdown.
        """
        # Intentar parseo directo
        try:
            result = json.loads(raw_text)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        
        # Intentar extraer JSON de bloques de código markdown
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1).strip())
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass
        
        # Intentar encontrar un array JSON en cualquier parte del texto
        array_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if array_match:
            try:
                result = json.loads(array_match.group(0))
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass
        
        print(f"⚠️ No se pudo parsear la respuesta de Gemini como JSON")
        return []
