import os
import json
import base64
import google.generativeai as genai
import cohere
from PIL import Image
import io
from app.config import get_settings, GEMINI_MODELS, COHERE_MODELS

class ScraperAIService:
    """
    Servicio de Inteligencia Artificial para el Scraper de Logística.
    Balancea la carga:
    - Gemini: Para procesamiento Visual (Set-of-Mark).
    - Cohere: Para procesamiento de Texto (Extracción de JSON).
    Aplica el patrón de Cascada de Modelos (si uno falla, intenta con el siguiente).
    """

    @classmethod
    def _init_gemini(cls):
        settings = get_settings()
        if not settings.muelle_gemini_api_key:
            raise ValueError("No se encontró MUELLE_GEMINI_API_KEY en .env")
        genai.configure(api_key=settings.muelle_gemini_api_key)

    @classmethod
    def _init_cohere(cls):
        settings = get_settings()
        if not settings.cohere_api_key:
            raise ValueError("No se encontró COHERE_API_KEY en .env")
        return cohere.ClientV2(api_key=settings.cohere_api_key)

    @classmethod
    async def get_som_target(cls, screenshot_bytes: bytes, instructions: str) -> dict:
        """
        Envía la captura de pantalla con las etiquetas numéricas a Gemini.
        Pide que identifique qué ID corresponde a la instrucción dada.
        Retorna un dict, ej: {"origen": 15, "destino": 22, "buscar": 45} o el ID del elemento buscado.
        """
        cls._init_gemini()
        img = Image.open(io.BytesIO(screenshot_bytes))

        prompt = f"""
        Eres un agente experto en navegación web.
        La imagen adjunta es una interfaz de logística donde todos los elementos interactivos tienen una etiqueta roja con un número de ID.
        
        INSTRUCCIONES:
        {instructions}
        
        Responde ÚNICAMENTE con un JSON válido, sin Markdown, ni bloques ```json.
        """

        for model_name in GEMINI_MODELS:
            print(f"🤖 [ScraperAI - Gemini] Intentando con modelo: {model_name}")
            try:
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async([prompt, img])
                
                text = response.text.strip()
                # Limpieza por si Gemini insiste en poner markdown
                if text.startswith("```json"):
                    text = text.replace("```json", "", 1)
                if text.endswith("```"):
                    text = text[:-3]
                
                result_json = json.loads(text.strip())
                print(f"✅ [ScraperAI - Gemini] Éxito con {model_name}")
                return result_json
                
            except Exception as e:
                print(f"⚠️ [ScraperAI - Gemini] Falló {model_name}: {str(e)}")
                continue
                
        raise Exception("❌ Todos los modelos de Gemini fallaron en el escaneo visual.")

    @classmethod
    async def extract_schedules_json(cls, raw_text: str) -> list:
        """
        Envía el texto sucio de los resultados a Cohere.
        Extrae un JSON limpio con los itinerarios.
        """
        co_client = cls._init_cohere()
        
        prompt = f"""
        Eres un extractor experto de datos logísticos.
        A continuación te doy el texto extraído de una web de resultados de itinerarios de barcos.
        
        TEXTO BRUTO:
        \"\"\"
        {raw_text}
        \"\"\"
        
        Tu tarea: Extrae todos los itinerarios encontrados.
        Devuelve ÚNICAMENTE un array JSON válido, donde cada objeto tenga esta estructura (usa null si un dato no está):
        [
          {{
            "vessel": "Nombre del barco",
            "voyage": "Número de viaje",
            "departure_date": "Fecha de salida",
            "arrival_date": "Fecha de llegada",
            "transit_time": "Tiempo de tránsito (ej: '14 days')",
            "origin": "Puerto de origen",
            "destination": "Puerto de destino"
          }}
        ]
        
        No agregues texto introductorio, solo el JSON puro.
        """

        for model_name in COHERE_MODELS:
            print(f"🤖 [ScraperAI - Cohere] Intentando con modelo: {model_name}")
            try:
                # Usar ClientV2 para soporte de chat
                response = co_client.chat(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                
                text = response.message.content[0].text.strip()
                if text.startswith("```json"):
                    text = text.replace("```json", "", 1)
                if text.endswith("```"):
                    text = text[:-3]
                    
                result_json = json.loads(text.strip())
                print(f"✅ [ScraperAI - Cohere] Éxito con {model_name}")
                return result_json
                
            except Exception as e:
                print(f"⚠️ [ScraperAI - Cohere] Falló {model_name}: {str(e)}")
                continue
                
        raise Exception("❌ Todos los modelos de Cohere fallaron en la extracción de texto.")
