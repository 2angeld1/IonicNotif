"""
BusinessService — Asistente de Negocios para Kitchy.
Caitlyn consulta el costeo real de un producto en Kitchy y usa
Gemini Flash para dar un consejo estratégico sobre precios y rentabilidad.
"""
import os
import httpx
import google.generativeai as genai
from typing import Optional

class BusinessService:
    """Servicio que analiza la rentabilidad de productos usando los datos de Kitchy."""
    
    _model = None
    KITCHY_URL = os.getenv("KITCHY_API_URL", "http://localhost:5000/api")

    SYSTEM_PROMPT = (
        "Eres Caitlyn, la consultora de negocios experta y proactiva de Kitchy. "
        "Tu misión es ayudar al dueño de un restaurante/barbería a tomar mejores decisiones financieras. "
        "Recibirás un JSON con el DESGLOSE DE COSTOS reales de un producto (insumos, precio actual, margen). "
        "REGLAS DE ORO:\n"
        "1. Sé amigable, profesional y directa. Habla como una socia estratégica.\n"
        "2. Analiza si el margen actual es saludable (Ideal: >60%).\n"
        "3. Si el margen es bajo, sugiere aumentar el precio basándote en las sugerencias del JSON.\n"
        "4. Si hay algún insumo que pese mucho en el costo, menciónalo.\n"
        "5. No respondas con JSON, responde con un mensaje humano, motivador y con datos claros.\n"
        "6. Mantén la respuesta corta y accionable (máximo 2 párrafos).\n"
    )

    @classmethod
    def _get_model(cls):
        """Inicializa el modelo de Gemini."""
        if cls._model is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no configurada")
            genai.configure(api_key=api_key)
            cls._model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
        return cls._model

    @classmethod
    async def get_advice(cls, product_name: str, token: str) -> dict:
        """
        Consulta Kitchy, pregunta a Gemini y devuelve el consejo.
        """
        try:
            # 1. Consultar a Kitchy (El Motor de Datos)
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{cls.KITCHY_URL}/agente/costeo/{product_name}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Caitlyn: 'Lo siento Angel, no encontré el producto {product_name} en tu menú de Kitchy.'",
                        "error": "not_found"
                    }
                
                costing_data = response.json()
            
            # 2. Consultar a Gemini (El Cerebro)
            model = cls._get_model()
            prompt = (
                f"Aquí tienes los datos de {product_name}:\n{costing_data}\n\n"
                "¿Qué consejo le darías al dueño?"
            )
            
            ai_response = model.generate_content([cls.SYSTEM_PROMPT, prompt])
            advice_text = ai_response.text.strip()

            return {
                "success": True,
                "message": advice_text,
                "data": costing_data
            }

        except Exception as e:
            print(f"💥 BusinessService error: {e}")
            return {
                "success": False,
                "message": "Caitlyn: 'Hubo un error al conectar con mis motores de análisis financiero.'",
                "error": str(e)
            }

    @classmethod
    async def get_dashboard_summary(cls, alerts: list) -> dict:
        """
        Genera un resumen proactivo de tablero (Dashboard) cuando hay productos fuera de rentabilidad.
        """
        try:
            if not alerts:
                return {"success": True, "message": "¡Todo excelente Angel! Tus márgenes están impecables."}
            
            model = cls._get_model()
            prompt = (
                f"Angel, el usuario, tiene estos {len(alerts)} productos por debajo de su margen objetivo. Algunos son: {[a.get('nombre') for a in alerts[:2]]}.\n\n"
                "Instrucciones ESTRICTAS para Caitlyn:\n"
                "- Escribe UN SOLO PÁRRAFO de MÁXIMO 2 ORACIONES (menos de 20 palabras).\n"
                "- Sé empática, rápida y al grano.\n"
                "- Ejemplo del tono: 'Angel, tienes 3 productos (como la Hamburguesa) perdiendo dinero. Confirma abajo y yo actualizaré los precios para recuperar tu rentabilidad.'\n"
                "- No des explicaciones largas ni uses viñetas."
            )
            
            ai_response = model.generate_content([cls.SYSTEM_PROMPT, prompt])
            advice_text = ai_response.text.strip()
            
            return {
                "success": True,
                "message": advice_text
            }
        except Exception as e:
            print(f"💥 BusinesService Dashboard Error: {e}")
            return {
                "success": False,
                "message": f"Caitlyn dice: 'Tengo los números, pero mi módulo de voz falló. Revisa abajo los detalles. ERROR: {e}'"
            }
