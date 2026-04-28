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
from app.config import GEMINI_MODELS


class InvoiceService:
    """Servicio dedicado a la extracción de productos desde imágenes de facturas."""
    
    _client = None

    SYSTEM_PROMPT = (
        "Eres Caitlyn, un asistente de contabilidad e inventario versátil para negocios en Panamá. "
        "Recibirás una imagen de una factura y el tipo de negocio ({negocio_tipo}). "
        "PRIMERA REGLA: Verifica si la imagen es realmente una factura, recibo o ticket de compra. "
        "Si NO es una factura, responde EXACTAMENTE: "
        '{{"error": "not_an_invoice"}}\n\n'
        "Si SÍ es una factura, extrae la información fiscal y TODOS los productos listados. "
        "Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin markdown. "
        "La estructura debe ser exactamente esta:\n"
        "{{\n"
        '  "fiscal": {{\n'
        '    "proveedor": "string", "ruc": "string", "dv": "string", "nroFactura": "string", '
        '    "fecha": "ISO string", "receptor": "string", "subtotal": number, "itbms": number, "total": number\n'
        '  }},\n'
        '  "productos": [\n'
        '    {{\n'
        '      "nombre": "string", \n'
        '      "cantidad": number, \n'
        '      "unidad": "string", \n'
        '      "unidadesPorEmpaque": number, \n'
        '      "precioUnitario": number, \n'
        '      "categoriaSugerida": "string (insumo | reventa | ingrediente | limpieza)", \n'
        '      "precioReventaSugerido": number | null\n'
        '    }}\n'
        '  ]\n'
        "}}\n\n"
        "REGLAS ESPECÍFICAS PARA {negocio_tipo}:\n"
        "- Si el tipo es 'BELLEZA':\n"
        "  * Identifica si el producto es un 'insumo' (ej: tinte, agua oxigenada, cera) o para 'reventa' (ej: shampoo 250ml, cremas de peinar).\n"
        "  * Si es 'reventa', sugiere un 'precioReventaSugerido' aplicando un margen del 65% sobre el precio unitario final.\n"
        "  * Si es 'insumo', usa null en 'precioReventaSugerido'.\n"
        "  * Las categorías sugeridas deben ser 'insumo' o 'reventa'.\n"
        "- Si el tipo es 'GASTRONOMIA' (default):\n"
        "  * Las categorías deben ser 'ingrediente', 'bebida', 'postre' o 'limpieza'.\n"
        "  * 'precioReventaSugerido' suele ser null a menos que sea un producto de reventa directa (ej: una soda de lata).\n\n"
        "Reglas Generales:\n"
        "- Si el nombre indica pack (ej: 'Sodas x 12'), extrae el número en 'unidadesPorEmpaque'.\n"
        "- Si no puedes leer algún campo, usa null.\n"
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
            print("🤖 InvoiceService: Cliente GenAI inicializado.")
        return cls._client

    @classmethod
    def _parse_base64_image(cls, image_data: str) -> tuple[bytes, str]:
        """
        Extrae los bytes y el mime type de un string base64.
        """
        if image_data.startswith("data:"):
            header, encoded = image_data.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]
        else:
            encoded = image_data
            mime_type = "image/jpeg"
        
        image_bytes = base64.b64decode(encoded)
        return image_bytes, mime_type

    # Cascada de modelos: estable → latest → preview → OCR local
    GEMINI_MODELS = GEMINI_MODELS

    @classmethod
    async def process_invoice(cls, image_base64: str, negocio_tipo: str = "GASTRONOMIA") -> dict:
        """
        Procesa una imagen de factura y extrae los productos segun el tipo de negocio.
        Intenta múltiples modelos en cascada si el primero falla.
        """
        try:
            client = cls._get_client()
            image_bytes, mime_type = cls._parse_base64_image(image_base64)
            
            # Personalizar el prompt segun el negocio
            system_instruction = cls.SYSTEM_PROMPT.format(negocio_tipo=negocio_tipo)
            
            print(f"📸 InvoiceService: Procesando factura de {negocio_tipo} ({len(image_bytes)} bytes)")
            
            # Intentar cada modelo en cascada
            last_error = None
            for model_name in cls.GEMINI_MODELS:
                try:
                    print(f"🤖 Intentando con modelo: {model_name}")
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                        )
                    )
                    
                    raw_text = response.text.strip()
                    
                    # Verificar que no sea una respuesta vacía o literal "error"
                    if not raw_text or raw_text == '"error"' or raw_text == 'error':
                        print(f"⚠️ Modelo {model_name} devolvió respuesta vacía o error genérico. Probando siguiente...")
                        last_error = f"Modelo {model_name} devolvió: {raw_text[:50] if raw_text else 'VACÍO'}"
                        continue
                    
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
                    
                    # Verificar que realmente extrajo productos
                    if not productos and isinstance(extracted_data, list):
                        productos = extracted_data
                    
                    if productos:
                        print(f"✅ Modelo {model_name} extrajo {len(productos)} productos exitosamente.")
                    
                    # 💡 APRENDIZAJE: Si Gemini detectó un RUC, guardamos el "Aviso" para Caitlyn Vision
                    ruc = fiscal.get("ruc")
                    if ruc:
                        print(f"🎓 Caitlyn aprendiendo nuevo layout para RUC: {ruc}")

                    return {
                        "success": True,
                        "productos": productos,
                        "fiscal": fiscal,
                        "total_detectados": len(productos),
                        "metodo": f"gemini_{model_name}"
                    }
                    
                except Exception as model_err:
                    print(f"⚠️ Modelo {model_name} falló: {model_err}")
                    last_error = str(model_err)
                    continue
            
            # Todos los modelos fallaron -> modo supervivencia
            print(f"🚨 Todos los modelos Gemini fallaron. Último error: {last_error}. Activando MODO SUPERVIVENCIA...")
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
            print(f"💥 InvoiceService error inesperado: {e}")
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
