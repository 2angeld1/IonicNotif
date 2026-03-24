"""
InvoiceService — Procesamiento de facturas con Gemini Flash.
Caitlyn recibe la imagen base64, la envía a Gemini y devuelve
una lista estructurada de productos detectados.
"""
import os
import json
import base64
import re
from google import genai
from google.genai import types
from typing import Optional
from app.services.caitlyn_vision_service import CaitlynVisionService


class InvoiceService:
    """Servicio dedicado a la extracción de productos desde imágenes de facturas."""
    
    _client = None

    SYSTEM_PROMPT = (
        "Eres un asistente de contabilidad e inventario para restaurantes en Panamá. "
        "Recibirás una imagen. PRIMERA REGLA: Verifica si la imagen es realmente una factura, recibo o ticket de compra. "
        "Si NO es una factura (ej. una persona, paisaje, objeto random, etc.), responde EXACTAMENTE y ÚNICAMENTE con este JSON: "
        '{"error": "not_an_invoice"}\n\n'
        "Si SÍ es una factura, extrae la información fiscal y TODOS los productos listados. "
        "Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin markdown. "
        "La estructura debe ser exactamente esta:\n"
        "{\n"
        '  "fiscal": {\n'
        '    "proveedor": "string o null",\n'
        '    "ruc": "string o null (formato RUC de Panamá)",\n'
        '    "dv": "string o null (dígito verificador)",\n'
        '    "nroFactura": "string o null",\n'
        '    "fecha": "ISO date string o null (obligatorio si es visible)",\n'
        '    "receptor": "string o null (ej: Consumidor Final, el nombre de un negocio, etc.)",\n'
        '    "subtotal": number,\n'
        '    "itbms": number (7% típicamente),\n'
        '    "total": number\n'
        "  },\n"
        '  "productos": [\n'
        '    {\n'
        '      "nombre": "string", \n'
        '      "cantidad": number, \n'
        '      "unidad": "string (ej: Caja, Bolsa, lb, ud)", \n'
        '      "unidadesPorEmpaque": number (ej: si es Caja x 12, pon 12. Por defecto 1),\n'
        '      "precioUnitario": number (el precio del empaque total segun factura)\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "Reglas:\n"
        "- Si el nombre indica un pack o contenido (ej: 'Sodas x 12', 'Pack 6uds', 'Caja 24'), extrae el número en 'unidadesPorEmpaque'.\n"
        "- Si la unidad no es clara, usa 'unidades'.\n"
        "- Si el precio unitario no es visible pero hay un total y cantidad, calcula el unitario.\n"
        "- El nombre del producto debe ser descriptivo pero corto.\n"
        "- El campo 'itbms' es el impuesto (7%). Si no está desglosado pero el total es mayor al subtotal, calcúlalo.\n"
        "- IMPORTANTE: Responde en español y usa tildes reales (UTF-8). NO uses códigos de escape como \\u00f3.\n"
        "- Si no puedes leer algún campo físico o fiscal, usa null.\n"
    )

    @classmethod
    def _get_client(cls):
        """Inicializa el cliente de Gemini de forma lazy."""
        if cls._client is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en .env")
            
            cls._client = genai.Client(api_key=api_key)
            print("🤖 InvoiceService: Cliente GenAI inicializado.")
        return cls._client

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
            # 1. ¿Conocemos esta factura? (Búsqueda rápida de RUC/Layout)
            # Nota: Aquí podríamos implementar una detección rápida de RUC con EasyOCR antes de ir a Gemini
            # Por ahora, simulamos la búsqueda por RUC si el cliente lo envía o si lo detectamos.
            
            client = cls._get_client()
            image_bytes, mime_type = cls._parse_base64_image(image_base64)
            
            print(f"📸 InvoiceService: Procesando imagen ({len(image_bytes)} bytes, {mime_type})")
            
            # --- Lógica Híbrida: Consultar memoria visual primero ---
            # (En una versión pro, aquí llamaríamos a CaitlynVisionService.scan_for_ruc)
            
            # 2. Llamada a Gemini (El "Mentor")
            response = await client.aio.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ],
                config=types.GenerateContentConfig(
                    system_instruction=cls.SYSTEM_PROMPT,
                )
            )
            
            raw_text = response.text.strip()
            extracted_data = cls._parse_response(raw_text)
            
            if isinstance(extracted_data, dict) and extracted_data.get("error") == "not_an_invoice":
                return {
                    "success": False,
                    "productos": [],
                    "total_detectados": 0,
                    "error": "La imagen proporcionada no parece ser una factura válida."
                }
            
            productos = extracted_data.get("productos", []) if isinstance(extracted_data, dict) else extracted_data
            fiscal = extracted_data.get("fiscal", {}) if isinstance(extracted_data, dict) else {}
            
            # 💡 APRENDIZAJE: Si Gemini detectó un RUC, guardamos el "Aviso" para Caitlyn Vision
            ruc = fiscal.get("ruc")
            if ruc:
                print(f"🎓 Caitlyn aprendiendo nuevo layout para RUC: {ruc}")
                # Aquí guardaríamos el layout map en la tabla caitlyn_vision
                # await CaitlynVisionService.save_layout(ruc, fiscal.get("proveedor"), ...)

            return {
                "success": True,
                "productos": productos,
                "fiscal": fiscal,
                "total_detectados": len(productos),
                "metodo": "gemini_mentor" # Para saber que usamos la IA esta vez
            }

        except Exception as e:
            print(f"🚨 Gemini de parranda (Error): {e}. Activando MODO SUPERVIVENCIA...")
            # Si Gemini falla, vamos al plan de emergencia local
            try:
                emergency_result = await CaitlynVisionService.blind_scan_invoice(image_base64)
                return emergency_result
            except Exception as local_err:
                print(f"💥 Error total (Falla Gemini y Falla Local): {local_err}")
                return {
                    "success": False,
                    "productos": [],
                    "total_detectados": 0,
                    "error": f"Error total en procesamiento: {str(local_err)}"
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
    def _parse_response(cls, raw_text: str) -> list | dict:
        """
        Intenta parsear la respuesta de Gemini como JSON.
        Maneja casos donde Gemini envuelve el JSON en markdown y detecta errores.
        """
        # Intentar parseo directo
        try:
            result = json.loads(raw_text)
            if isinstance(result, (list, dict)):
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
                elif isinstance(result, dict) and "error" in result:
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
