"""
BusinessService — Asistente de Negocios para Kitchy.
Caitlyn consulta el costeo real de un producto en Kitchy y usa
Gemini Flash para dar un consejo estratégico sobre precios y rentabilidad.
"""
import os
import httpx
import google.generativeai as genai
import json
import math
from typing import Optional

class BusinessService:
    """Servicio que analiza la rentabilidad de productos usando los datos de Kitchy."""
    
    _model = None
    KITCHY_URL = os.getenv("KITCHY_API_URL", "http://localhost:5000/api")

    SYSTEM_PROMPT = (
        "Eres Caitlyn, la consultora de negocios proactiva de Kitchy en Panamá. "
        "REGLAS DE ORO (TRABAJO PARA DUEÑOS OCUPADOS):\n"
        "1. BREVEDAD EXTREMA: Tu respuesta DEBE ser de máximo 2 o 3 frases cortas. ⚡\n"
        "2. PUNCHY & EMOJIS: Usa 1 o 2 emojis. Ve directo al grano sin introducciones.\n"
        "3. ACCIÓN INMEDIATA: Dime qué hacer (ej: 'Sube $0.50 a la Hamburguesa, el costo del pan subió').\n"
        "4. SIN RELLENO: No menciones leyes o informes generales si no afectan directamente al dueño hoy.\n"
        "5. Sé amigable pero ejecutiva. Habla como una socia que tiene 10 segundos para dar un consejo. 🤝\n"
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

            # 🛠 DEBUG (Angel): Verificar si el scraper llega al cerebro
            print(f"\n🧠 [CAITLYN] Recibiendo petición estratégica para: {product_name}")
            print(f"📈 Fuentes de Mercado: {list(market_context.keys()) if market_context else 'VACÍO ⚠️'}")
            if market_context and 'FUEL' in market_context:
                print(f"⛽ Gasolina 95: ${market_context['FUEL'].get('octane95', 'N/A')}")
            if market_context and 'MERCA' in market_context:
                print(f"🌽 Merca Panamá: {len(market_context['MERCA'].get('vegetales', {}))} items detectados")

            # 1. Análisis frío de Caitlyn
            caitlyn_insight = cls.analyze_market_impact(market_context, business_data)

            # 2. IA para la Voz y el Consejo Final
            advice_text = ""
            try:
                model = cls._get_model()
                
                # Forzar a la IA a que use el precio matematicamente correcto calculado por el backend si existe.
                precio_target_str = ""
                if business_data and business_data.get('precioTargetMatematico'):
                    precio_target_str = f"PRECIO OBJETIVO MATEMÁTICO: ${business_data.get('precioTargetMatematico')}. DEBES USAR O MENCIONAR EXACTAMENTE ESTE PRECIO O APROXIMADO EN TU CONSEJO.\n"

                prompt = (
                    f"Angel tiene este producto: {product_name}.\n"
                    f"DATOS RELEVANTES: {business_data}\n"
                    f"{precio_target_str}"
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
    async def suggest_recipe(cls, dish_name: str, inventory_list: list, serving_size: Optional[str] = None, market_context: dict = None, target_margin: int = 65) -> dict:
        """
        Actúa como un Chef Ejecutivo. Recibe un plato y sugiere una receta.
        Calcula el costo real de producción usando el inventario local, precios de mercado o estimaciones de IA.
        """
        # Formatear inventario con stock y COSTO
        inv_text = "\n".join([f"- {i.get('nombre')} (ID: {i.get('_id')}, Unidad: {i.get('unidad')}, Costo: ${i.get('costoUnitario', 0)}, Stock: {i.get('cantidad')})" for i in inventory_list])
        
        # Contexto de mercado para la IA
        merca_context = market_context.get('MERCA', {}) if market_context else {}
        
        prompt = (
            f"Eres un Chef Ejecutivo experto en Panamá. El plato es: '{dish_name}'.\n"
            f"TAMAÑO DE LA PORCIÓN: {serving_size if serving_size else '1 unidad por defecto'}.\n\n"
            f"DATOS DISPONIBLES:\n"
            f"1. INVENTARIO LOCAL:\n{inv_text}\n\n"
            f"2. PRECIOS DE MERCADO (PANAMÁ):\n{json.dumps(merca_context, indent=2)}\n\n"
            f"Sugiere los ingredientes necesarios para este plato respetando el TAMAÑO DE LA PORCIÓN.\n"
            f"REGLAS CRÍTICAS:\n"
            f"1. SOBRE UNIDADES EN 'unidades': \n"
            f"   - Si el costo es ALTO (>$10): Es un bulto industrial. Usa proporciones reales para UNA PORCIÓN (ej: Pasta 100g = 0.01 si el bulto es de 10kg).\n"
            f"   - PESOS ESTÁNDAR POR PORCIÓN: Carne (150g), Pasta (100-150g), Queso (50-80g), Vegetales (50g).\n"
            f"   - NUNCA pidas más del 10% de un bulto industrial para una sola ración.\n"
            f"2. Si un ingrediente NO está en el inventario local, búscalo en los PRECIOS DE MERCADO.\n"
            f"3. Si TAMPOCO está en los precios de mercado, USA TU CONOCIMIENTO para ESTIMAR el precio en Panamá.\n"
            f"4. Devuelve ÚNICAMENTE un JSON con esta estructura:\n"
            "   {\"ingredientes\": [{\"nombre\": \"string\", \"cantidad\": float, \"unidad\": \"string\", \"inventario\": \"ID_o_null\", \"costo_estimado\": float}]}\n"
        )

        try:
            model = cls._get_model()
            # Volvemos al método síncrono que es más estable en este entorno
            response = model.generate_content([cls.SYSTEM_PROMPT, prompt])
            raw_text = response.text.strip()
            
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()

            print(f"DEBUG: Texto crudo de la IA: {raw_text[:100]}...")
            recipe_data = json.loads(raw_text)
            
            # Validación robusta del formato
            if isinstance(recipe_data, list):
                recipe_ingredients = recipe_data
            elif isinstance(recipe_data, dict):
                recipe_ingredients = recipe_data.get('ingredientes', recipe_data.get('recipe', []))
            else:
                recipe_ingredients = []

            if not recipe_ingredients:
                 print("⚠️ Caitlyn no devolvió una lista de ingredientes válida.")
                 return { "success": False, "error": "Formato de receta inválido" }

            # CÁLCULO MATEMÁTICO REALISTA (Caitlyn 🧠 + Mercado ⚖️ + IA Estimate 🔮)
            costo_total = 0.0
            print(f"\n🔬 [CAITLYN] Calculando PRECIADO REAL: {dish_name}")
            
            for ing in recipe_ingredients:
                # Fallback de nombre para evitar None
                nombre_ing = ing.get('nombre') or ing.get('insumo') or ing.get('item') or "Insumo Desconocido"
                ing['nombre'] = nombre_ing # Normalizar para el front
                
                inv_id = ing.get('inventario')
                try:
                    c = float(ing.get('cantidad', 0))
                except (ValueError, TypeError):
                    c = 0.0
                
                ing_u = str(ing.get('unidad', '')).lower()
                inv_item = next((i for i in inventory_list if str(i.get('_id')) == str(inv_id)), None)
                subtotal = 0.0

                if inv_item:
                    costo_u = float(inv_item.get('costoUnitario', 0))
                    inv_u = str(inv_item.get('unidad', 'unidades')).lower()
                    
                    # --- LÓGICA DE CONVERSIÓN DE SEGURIDAD ---
                    if ing_u in ['gramos', 'gr', 'g', 'ml']:
                        if inv_u in ['kg', 'litros', 'l']:
                            c = c / 1000
                        elif inv_u == 'lb':
                            c = c / 453.59
                        elif inv_u == 'unidades' and costo_u > 10:
                            c = c / 1000
                    
                    elif ing_u == 'unidades' and inv_u == 'unidades' and costo_u > 10 and c >= 1.0:
                        c = c / 1000 
                    
                    subtotal = c * costo_u
                    print(f"   ✅ {nombre_ing}: {round(c, 4)} {inv_u} x ${costo_u} (Inv) = ${round(subtotal, 4)}")
                
                # 2. Si no hay item, intentar MERCADO (Merca o ACODECO)
                elif market_context and nombre_ing != "Insumo Desconocido":
                    nombre_search = nombre_ing.lower().strip()
                    
                    # Orígenes de datos
                    merca_veg = market_context.get('MERCA', {}).get('vegetales', {})
                    merca_carn = market_context.get('MERCA', {}).get('carnes', {})
                    acodeco = market_context.get('ACODECO', {}).get('controlPrecios', {})
                    
                    # Búsqueda prioritaria (ACODECO -> MERCA)
                    costo_m = None
                    
                    # 2.1 ACODECO
                    if nombre_search:
                        key_a = next((k for k in acodeco if k.lower() in nombre_search or nombre_search in k.lower()), None)
                        if key_a:
                            costo_m = acodeco.get(key_a)

                    # 2.2 MERCA PANAMÁ
                    if not costo_m and nombre_search:
                        key_m = next((k for k in merca_veg if k.lower() in nombre_search or nombre_search in k.lower()), None)
                        if not key_m:
                            key_m = next((k for k in merca_carn if k.lower() in nombre_search or nombre_search in k.lower()), None)
                        
                        if key_m:
                            costo_m = merca_veg.get(key_m) or merca_carn.get(key_m)

                    if costo_m:
                        costo_base = float(costo_m)
                        if ing_u in ['gramos', 'gr', 'g', 'ml']:
                            c = c / 453.59 # Convertimos gramos a Libras
                        subtotal = c * costo_base
                        print(f"   ⚖️ {nombre_ing}: {round(c, 4)} lb x ${costo_m} (Market) = ${round(subtotal, 4)}")
                    
                    # 3. FALLBACK: Estimación de la IA
                    elif ing.get('costo_estimado'):
                        costo_e = float(ing.get('costo_estimado'))
                        if ing_u in ['gramos', 'gr', 'g', 'ml']:
                            c = c / 453.59
                        subtotal = c * costo_e
                        print(f"   🔮 {nombre_ing}: {round(c, 4)} lb x ${ing.get('costo_estimado')} (IA Estimate) = ${round(subtotal, 4)}")
                
                # Fallback final
                if subtotal == 0 and ing.get('costo_estimado'):
                    costo_e = float(ing.get('costo_estimado', 0))
                    subtotal = c * costo_e
                    print(f"   🔮 {nombre_ing}: {round(c, 4)} x ${costo_e} (IA Fallback) = ${round(subtotal, 4)}")


                ing['costoSubtotal'] = round(subtotal, 2)
                costo_total += subtotal
            
            # Margen Dinámico (Precio = Costo / (1 - Margen/100))
            divisor = (100 - target_margin) / 100
            precio_sugerido = math.ceil(costo_total / divisor) if costo_total > 0 and divisor > 0 else 0
            
            print(f"📊 COSTO REAL PRODUCCIÓN: ${round(costo_total, 2)} (Margen Meta: {target_margin}%)")
            print(f"💰 PRECIO SUGERIDO: ${precio_sugerido}\n")

            return { 
                "success": True, 
                "recipe": recipe_ingredients,
                "costoTotal": round(float(costo_total), 2),
                "precioSugerido": int(precio_sugerido),
                "marginalidad": target_margin
            }
        except Exception as e:
            print(f"Error suggesting recipe: {e}")
            return { "success": False, "error": str(e) }

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

    _menu_patterns_cache = {}

    @classmethod
    async def suggest_menu_from_inventory(cls, inventory_list: list, target_margin: int = 65) -> dict:
        """
        Analiza el inventario y sugiere 3 platillos para maximizar rentabilidad o rotar inventario alto.
        Caitlyn usa memoria local para no llamar a Gemini si ya aprendió este patrón.
        """
        try:
            # 1. Caitlyn filtra el inventario localmente (heurística)
            valid_items = [i for i in inventory_list if float(i.get('cantidad', 0)) > 0]
            
            # Ordenamos por cantidad descendente para priorizar cosas con exceso de stock
            valid_items.sort(key=lambda x: float(x.get('cantidad', 0)), reverse=True)
            
            # Tomamos el TOP 5 para la "Firma de Memoria" (Pattern Hash)
            top_5_names = ",".join([i.get('nombre', '').lower().strip() for i in valid_items[:5]])
            pattern_signature = f"{top_5_names}_{target_margin}"

            # ¿Caitlyn ya aprendió esto?
            if pattern_signature in cls._menu_patterns_cache:
                print(f"🧠 [CAITLYN MEMORY] Recuperando receta desde la memoria cerebral para el patrón: {pattern_signature}")
                return {
                    "success": True,
                    "source": "CAITLYN_MEMORY",
                    "data": cls._menu_patterns_cache[pattern_signature],
                    "message": "Menú sugerido por Caitlyn (Aprendizaje Prevío)"
                }

            # Tomamos el TOP 20
            top_items = valid_items[:20]

            if not top_items:
                return {"success": False, "message": "Tu inventario está vacío o sin stock actualmente."}

            # 2. Si es nuevo, subimos a la capa de Inteligencia de Gemini (El Chef)
            print(f"👩‍🍳 [GEMINI CHEF] Analizando nuevo patrón de ingredientes para menú...")

            inv_text = "\n".join([f"- {i.get('nombre')} (ID: {str(i.get('_id'))}, Stock: {i.get('cantidad')} {i.get('unidad')}, Costo Unit: ${i.get('costoUnitario', 0)})" for i in top_items])

            prompt = (
                "Eres un Chef Ejecutivo e Ingeniero de Menú en Panamá.\n\n"
                f"El dueño del restaurante tiene ESTOS ingredientes disponibles o en exceso:\n{inv_text}\n\n"
                "=== TU MISIÓN ===\n"
                "Invéntate 3 opciones de platillos, bebidas o combos atractivos que se puedan preparar PRINCIPALMENTE con estos ingredientes. "
                "El objetivo es rotar este inventario rápido y lograr alta rentabilidad.\n"
                f"1. Para cada opción, sugiere cantidades lógicas.\n"
                f"2. Calcula el 'costo_total' sumando (cantidad * costo_unit).\n"
                f"3. Aplica un {target_margin}% de rentabilidad para dar el precio_recomendado.\n"
                "4. Responde ÚNICAMENTE en este JSON estricto (no uses markdown ni bloques ```json):\n"
                "{\n"
                "  \"sugerencias\": [\n"
                "    {\n"
                "      \"nombre_plato\": \"Nombre Comercial\",\n"
                "      \"descripcion\": \"Por qué es buena idea vender esto hoy.\",\n"
                "      \"costo_estimado\": 1.20,\n"
                "      \"precio_recomendado\": 3.50,\n"
                "      \"ingredientes_a_usar\": [\n"
                "        {\"nombre\": \"Nombre del insumo\", \"cantidad\": 1, \"unidad\": \"oz\", \"inventario\": \"ID_REAL_DEL_INVENTARIO_PROPORCIONADO\"}\n"
                "      ]\n"
                "    }\n"
                "  ]\n"
                "}"
            )

            model = cls._get_model()
            ai_response = model.generate_content([cls.SYSTEM_PROMPT, prompt])
            
            response_text = ai_response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(response_text)
            sugerencias = data.get("sugerencias", [])
            
            # 3. Caitlyn aprende este patrón y lo guarda en su Memoria (Local Cache)
            cls._menu_patterns_cache[pattern_signature] = sugerencias
            print(f"✅ [CAITLYN MEMORY] Nuevo patrón aprendido y guardado bajo la firma: {pattern_signature}")
            
            return {
                "success": True,
                "data": sugerencias,
                "message": "Menú inteligente generado con éxito"
            }
        except Exception as e:
            return {"success": False, "message": "Error al generar ideas", "error": str(e)}
