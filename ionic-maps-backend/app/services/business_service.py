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
        "Eres Caitlyn, la consultora de negocios proactiva de Kitchy en Panamá. "
        "Tu misión es ayudar al dueño a tomar mejores decisiones financieras. "
        "Recibirás un ANALISIS LOCAL (Panamá) y datos del NEGOCIO (Costos, Margen, Ventas). "
        "REGLAS DE ORO:\n"
        "1. Sé amigable y directa. Habla como una socia estratégica de confianza.\n"
        "2. ANALIZA EL MARGEN: Si es < 60%, advierte que la rentabilidad está en riesgo.\n"
        "3. USA EL CONTEXTO: Si mi ANALISIS LOCAL indica alza en gasolina o Merca Panamá, úsalo para justificar cambios de precio.\n"
        "4. No respondas con JSON. Da un consejo humano, claro y con DATOS REALES del JSON.\n"
        "5. Sé proactiva: Si hay lluvia, recomienda delivery. Si hay costos altos, recomienda ajustar precios.\n"
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
    def analyze_market_impact(cls, market_context: dict, business_data: dict) -> str:
        """
        RAZONAMIENTO LOCAL: Caitlyn predice el impacto sin usar tokens de Gemini.
        """
        analysis = []
        
        # 1. Análisis de Combustible (SNE Panamá)
        fuel = market_context.get('FUEL', {})
        if fuel.get('octane95', 0) > 1.10:
            analysis.append(f"⛽ Gasolina a ${fuel.get('octane95')}: Sube tus costos de envío en un 5-8%.")

        # 2. Análisis de Merca Panamá vs Ingredientes
        merca = market_context.get('MERCA', {}).get('vegetales', {})
        ingredientes = business_data.get('ingredientes', [])
        for ing in ingredientes:
            name = ing.get('nombre', '').lower()
            if 'cebolla' in name and merca.get('cebolla', 0) > 0.80:
                analysis.append("🧅 Cebolla cara en Merca: Tu plato de cebolla tiene margen bajo ahora.")

        # 3. Análisis de Clima (PROACTIVO 5 DÍAS)
        weather_context = market_context.get('WEATHER', {})
        forecast = weather_context.get('forecast', [])
        
        rainy_days = [d for d in forecast if d.get('lluviaProb', 0) > 60]
        if rainy_days:
            show_dates = []
            for d in rainy_days:
                if len(show_dates) < 2:
                    show_dates.append(str(d.get('fecha')))
            dates_str = ", ".join(show_dates)
            analysis.append(f"🌧️ Pronóstico de Lluvia: Se esperan lluvias fuertes para {dates_str}. Planifica promociones de delivery para esos días.")
        elif forecast:
            analysis.append("☀️ Clima favorable para los próximos días. Buen momento para eventos en mesa.")

        return "\n".join(analysis) if analysis else "Mercado estable."

    @classmethod
    async def get_strategic_advice(cls, payload: dict) -> dict:
        """
        CONSEJO ESTRATÉGICO: Une los puntos entre costos y Panamá.
        """
        try:
            product_name = payload.get('product_name', 'tus productos')
            market_context = payload.get('market_context', {})
            business_data = payload.get('business_data', {})

            # 1. Análisis frío de Caitlyn
            caitlyn_insight = cls.analyze_market_impact(market_context, business_data)

            # 2. IA para la Voz y el Consejo Final
            advice_text = ""
            try:
                model = cls._get_model()
                prompt = (
                    f"Angel tiene este producto: {product_name}.\n"
                    f"DATOS RELEVANTES: {business_data}\n"
                    f"CONTEXTO PANAMÁ HOY: {caitlyn_insight}\n\n"
                    "Genera el consejo de socia estratégica."
                )
                
                ai_response = model.generate_content([cls.SYSTEM_PROMPT, prompt])
                advice_text = ai_response.text.strip()
            except Exception as e:
                # FALLBACK Proactivo: Caitlyn usa su propio razonamiento si la IA falla.
                print(f"⚠️ Alerta: Usando razonamiento local de Caitlyn (Gemini offline).")
                advice_text = (
                    f"Hola Angel, por ahora no puedo contactar con la central, pero he analizado tus números "
                    f"y la realidad del país: \n\n{caitlyn_insight}\n\n"
                    "Te sugiero revisar tus precios pronto."
                )
            
            return {
                "success": True,
                "message": advice_text,
                "caitlyn_reasoning": caitlyn_insight # Esto lo usaremos para el Punto 1
            }
        except Exception as e:
            return {"success": False, "message": "Error estratégico", "error": str(e)}

    @classmethod
    async def get_advice(cls, product_name: str, token: str) -> dict:
        # Mantenemos este por compatibilidad LEGACY si se llama desde otros sitios
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(f"{cls.KITCHY_URL}/agente/costeo/{product_name}", headers=headers)
                if response.status_code != 200:
                    return {"success": False, "message": "Producto no encontrado."}
                costing_data = response.json()
            
            model = cls._get_model()
            prompt = f"Datos de {product_name}:\n{costing_data}\nConsejo pro?"
            ai_response = model.generate_content([cls.SYSTEM_PROMPT, prompt])
            return {"success": True, "message": ai_response.text.strip(), "data": costing_data}
        except Exception as e:
            return {"success": False, "message": "Error", "error": str(e)}

    @classmethod
    async def get_dashboard_summary(cls, alerts: list) -> dict:
        # Resumen proactivo de Dashboard (Simplificado)
        try:
            if not alerts:
                return {"success": True, "message": "¡Todo excelente! Márgenes saludables."}
            model = cls._get_model()
            prompt = f"Tengo {len(alerts)} alertas de rentabilidad. Haz un resumen rápido de impacto."
            ai_response = model.generate_content([cls.SYSTEM_PROMPT, prompt])
            return {"success": True, "message": ai_response.text.strip()}
        except Exception as e:
            return {"success": False, "message": "Error", "error": str(e)}
