"""
BusinessService — Asistente de Negocios para Kitchy.
Caitlyn consulta el costeo real de un producto en Kitchy y usa
Cohere (Command R) para dar un consejo estratégico sobre precios y rentabilidad.
"""
import json
import re
from datetime import datetime
import os
import httpx
import cohere
from app.database import get_database
from app.config import get_settings, GEMINI_MODELS, COHERE_MODELS
import math
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types

class BusinessService:
    """Servicio que analiza la rentabilidad de productos usando los datos de Kitchy."""
    
    _client = None
    _gemini_client = None
    KITCHY_URL = os.getenv("KITCHY_API_URL", "http://localhost:5000/api")
    
    # 🧠 Memoria Cerebral de Caitlyn (Caché local para aprendizaje evolutivo)
    _advice_cache = {}
    _recipe_cache = {}
    _menu_patterns_cache = {}

    SYSTEM_PROMPT = (
        "Eres Caitlyn, la socia y amiga estratégica de Kitchy en Panamá. "
        "REGLAS DE ORO:\n"
        "1. PERSONALIDAD: Sé super amigable, cercana y natural (nada de sonar como un robot ejecutivo). Habla como una socia que de verdad quiere ver el negocio crecer. 🤝\n"
        "2. ESTILO: Texto fluido, sencillo y directo. NUNCA uses corchetes, signos de suma o etiquetas de estructura.\n"
        "3. CONTENIDO: Explícame de forma relajada el PORQUÉ (costos/mercado) y dame el consejo del precio. \n"
        "4. BREVEDAD: Máximo 3 o 4 frases con un toque de buena vibra y emojis. ✨🚀\n"
    )
    
    @classmethod
    def _get_gemini_client(cls):
        """Inicializa el cliente de Gemini de forma lazy."""
        if cls._gemini_client is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no configurada")
            cls._gemini_client = genai.Client(api_key=api_key)
        return cls._gemini_client

    @classmethod
    def _get_client(cls):
        """Inicializa el cliente asíncrono de Cohere desde configuración global."""
        if cls._client is None:
            from app.config import get_settings
            settings = get_settings()
            api_key = settings.cohere_api_key
            if not api_key:
                # Fallback final a os.getenv
                api_key = os.getenv("COHERE_API_KEY", "")
            
            if not api_key:
                raise ValueError("COHERE_API_KEY no configurada en .env o settings")
            cls._client = cohere.AsyncClient(api_key=api_key)
        return cls._client

    @classmethod
    async def get_kitchy_context(cls, negocio_id: str = None) -> dict:
        """
        🕵️‍♀️ CAPACIDAD AUTÓNOMA: Caitlyn mira directamente las colecciones de Kitchy.
        Útil para auditoría de movimientos, contexto de mercado y memorias.
        """
        db = get_database(get_settings().kitchy_database_name)
        context = {
            "market": {},
            "audit": {"movimientos": [], "total_mermas": 0},
            "history": {"recetas_previas": []}
        }

        try:
            # 1. Recuperar Contextos de Mercado (Merca, ACODECO, Fuel, Weather)
            market_types = ['FUEL', 'MERCA', 'ACODECO', 'WEATHER']
            for m_type in market_types:
                last_entry = await db["marketcontexts"].find_one(
                    {"tipo": m_type}, 
                    sort=[("fecha", -1)]
                )
                if last_entry:
                    context["market"][m_type] = last_entry.get("data")

            # 2. Auditoría de Movimientos (Si tenemos el Negocio)
            if negocio_id:
                # MongoDB motor requiere ObjectId si se guardó como tal, 
                # pero Kitchy suele usar strings o ObjectIds según el driver.
                # Intentamos búsqueda flexible.
                try:
                    from bson import ObjectId
                    n_id = ObjectId(negocio_id) if len(negocio_id) == 24 else negocio_id
                except:
                    n_id = negocio_id

                movs_cursor = db["movimientoinventarios"].find(
                    {"negocioId": n_id}, 
                    sort=[("createdAt", -1)]
                ).limit(20)
                
                movs = await movs_cursor.to_list(length=20)
                context["audit"]["movimientos"] = movs
                context["audit"]["total_mermas"] = len([m for m in movs if m.get("tipo") == "merma"])

                # 3. Recetas Sugeridas Previas
                recipes_cursor = db["recetasugeridas"].find(
                    {"negocioId": n_id},
                    sort=[("createdAt", -1)]
                ).limit(5)
                context["history"]["recetas_previas"] = await recipes_cursor.to_list(length=5)

            return context
        except Exception as e:
            print(f"⚠️ Error en mirada autónoma de Caitlyn: {e}")
            return context

    @classmethod
    def extract_market_patterns(cls, market_context: dict, business_data: dict) -> tuple[list, str]:
        """
        ANALÍTICA DE PATRONES: Caitlyn extrae etiquetas lógicas de la situación actual.
        Retorna (lista_de_patrones, resumen_texto).
        """
        patterns = []
        insights = []
        
        # 1. Patrón Combustible ⛽
        fuel = market_context.get('FUEL', {})
        if fuel:
            gas95 = float(fuel.get('octane95', 0))
            if gas95 > 1.10:
                patterns.append("FUEL_HIGH")
                insights.append("Logística costosa por combustible alto.")
            else:
                patterns.append("FUEL_STABLE")
        
        # 2. Patrón Merca Panamá 🌽
        merca = market_context.get('MERCA', {}).get('vegetales', {})
        if merca:
            patterns.append(f"MERCA_ACTIVE_{len(merca)}")
            insights.append(f"Abastecimiento de Merca Panamá activo ({len(merca)} items frescos).")
        
        # 3. Patrón Clima 🌧️
        weather = market_context.get('WEATHER', {})
        if weather:
            is_rain = "rain" in str(weather.get('description', '')).lower()
            if is_rain:
                patterns.append("WEATHER_RAINY")
                insights.append("Día lluvioso en Panamá: ¡Oportunidad para delivery!")
            else:
                patterns.append("WEATHER_CLEAR")
                insights.append("Día despejado: ¡Ideal para visitas en local!")
        
        # 4. Patrón de Inventario y Ventas Internas 📊
        if business_data:
            qty = float(business_data.get('cantidad', 0))
            sales = int(business_data.get('ventas30Dias', 0))
            
            if qty > 50:
                patterns.append("INVENTORY_EXCESS")
                if sales < 5:
                    patterns.append("LOW_SALES_VELOCITY")
                    insights.append("Ojo: Tienes mucho stock y pocas ventas de este producto este mes (Rotación Baja).")
                else:
                    insights.append("Inventario alto pero con movimiento saludable.")
            elif qty < 10 and qty > 0:
                patterns.append("INVENTORY_LOW")
                insights.append("Poco stock disponible: ¡Momento de reabastecer antes que se acabe!")
            
            if sales > 50:
                patterns.append("BEST_SELLER")
                insights.append("¡Este producto es una estrella! Se vende muy bien.")

        # 5. Patrón de Auditoría Operativa (Mermas/Escapes) 🕵️‍♂️
        audit = business_data.get('audit_movimientos')
        if audit:
            mermas = audit.get('mermas', 0)
            if mermas > 0:
                patterns.append("WASTE_DETECTED")
                insights.append(f"He detectado {mermas} registros de mermas/pérdidas. ¡Hay que cuidar los insumos!")
            if audit.get('total_cantidad_merma', 0) > 10:
                 patterns.append("HIGH_WASTE_DETECTED")
                 insights.append("¡Alerta de Desperdicio! La cantidad de pérdida es significativa este mes.")

        return patterns, " ".join(insights)

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
            user_name = payload.get('user_name', 'Socio/a')
            market_context = payload.get('market_context', {})
            business_data = payload.get('business_data', {})

            # 🛠 DEBUG (Angel): Verificar si el scraper llega al cerebro
            print(f"\n🧠 [CAITLYN] Recibiendo petición estratégica para: {product_name}")
            print(f"📈 Fuentes de Mercado: {list(market_context.keys()) if market_context else 'VACÍO ⚠️'}")
            if market_context and 'FUEL' in market_context:
                print(f"⛽ Gasolina 95: ${market_context['FUEL'].get('octane95', 'N/A')}")
            if market_context and 'MERCA' in market_context:
                print(f"🌽 Merca Panamá: {len(market_context['MERCA'].get('vegetales', {}))} items detectados")

            # 🧠 PERCEPCIÓN: Extraer patrones del mercado de Panamá hoy
            patterns, caitlyn_insight = cls.extract_market_patterns(market_context, business_data)

            # 🧠 ¿Caitlyn ya aprendió un patrón similar para ESTE producto? (Pattern Recognition)
            knowledge_col = get_database(get_settings().kitchy_database_name)["caitlyn_knowledge"]
            
            negocio_id = payload.get("negocio_id", "global")
            # Normalizar el nombre para evitar variaciones por mayúsculas
            name_clean = str(product_name).lower().strip().replace(" ", "_")
            pattern_signature = f"{negocio_id}-{name_clean}-" + "-".join(sorted(patterns))
            
            # Buscar si el PATRÓN ya tiene una respuesta efectiva
            query = {
                "pattern_signature": pattern_signature,
                "type": "strategic_advice"
            }
            
            past_pattern = await knowledge_col.find_one(query)
            
            if past_pattern:
                print(f"🧠 [CAITLYN PATTERN] Reconociendo sabiduría por analogía: {pattern_signature}")
                # Adaptar el consejo al producto actual (cambiar nombre si es necesario)
                advice_adapted = past_pattern["advice_text"]
                return {
                    "success": True,
                    "message": advice_adapted,
                    "caitlyn_reasoning": f"He reconocido este patrón de mercado en Panamá: {patterns}. Aplicando sabiduría previa. ✨"
                }

            # 3. IA para la Voz y el Consejo Final (Si no hay patrón previo)
            advice_text = ""
            try:
                client = cls._get_client()
                
                # Forzar a la IA a que use el precio matematicamente correcto calculado por el backend si existe.
                precio_target_str = ""
                if business_data and business_data.get('precioTargetMatematico'):
                    precio_target_str = f"PRECIO OBJETIVO MATEMÁTICO: ${business_data.get('precioTargetMatematico')}. DEBES USAR O MENCIONAR EXACTAMENTE ESTE PRECIO O APROXIMADO EN TU CONSEJO.\n"

                prompt = (
                    f"{user_name} tiene este producto: {product_name}.\n"
                    f"DATOS DE COSTO INTERNO (Kitchy): {business_data}\n"
                    f"{precio_target_str}"
                    f"CONTEXTO REAL DE PANAMÁ (Scrapers): {market_context}\n"
                    f"CONSEJO DE CAITLYN: {caitlyn_insight}\n\n"
                    "TU TAREA: Genera un consejo amigable e inteligente. "
                    "REGLA DE ORO: ¡Menciona DATOS REALES de los precios enviados arriba! "
                    "(Ejemplo: 'La gasolina está en $1.14' o 'El costo de tus ingredientes suma $X'). "
                    "No inventes datos, usa los que te pasé. Si el precio sugerido matemático es mayor al actual, sugiérelo con tacto."
                )
                
                ai_response = await client.chat(
                    model=COHERE_MODELS[1], # Usamos Command-R (08-2024) para estrategia
                    message=prompt,
                    preamble=cls.SYSTEM_PROMPT,
                )
                advice_text = ai_response.text.strip()
                
                # 🧠 APRENDIZAJE ETERNO: Guardar el PATRÓN en MongoDB
                await knowledge_col.insert_one({
                    "product_name": product_name,
                    "pattern_signature": pattern_signature,
                    "patterns": patterns,
                    "advice_text": advice_text,
                    "caitlyn_insight": caitlyn_insight,
                    "created_at": datetime.now().timestamp(),
                    "type": "strategic_advice"
                })
                print(f"🏺 [CAITLYN PATTERN] Nuevo patrón sellado en MongoDB: {pattern_signature}")

            except Exception as e:
                # FALLBACK Proactivo: Caitlyn usa su propio razonamiento si la IA de red falla.
                print(f"❌ [CAITLYN ERROR ESTRATÉGICO]: {str(e)}")
                advice_text = (
                    f"Hola {user_name}, parece que hay un retraso en la conexión con la central de IA, "
                    f"pero basándome en mi análisis local de Panamá: \n\n{caitlyn_insight}\n\n"
                    "¡Mi recomendación es que tomes acción sobre estos puntos lo antes posible! ⚡"
                )
            
            return {
                "success": True,
                "message": advice_text,
                "caitlyn_reasoning": caitlyn_insight # Esto lo usaremos para el Punto 1
            }
        except Exception as e:
            return {"success": False, "message": "Error estratégico", "error": str(e)}

    @classmethod
    async def suggest_recipe(cls, dish_name: str, inventory_list: list, serving_size: Optional[str] = None, market_context: dict = None, target_margin: int = 65, negocio_id: str = "global") -> dict:
        """
        Actúa como un Chef Ejecutivo. Recibe un plato y sugiere una receta.
        Calcula el costo real de producción usando el inventario local, precios de mercado o estimaciones de IA.
        """
        # Formatear inventario con stock y COSTO
        inv_text = "\n".join([f"- {i.get('nombre')} (ID: {i.get('_id')}, Unidad: {i.get('unidad')}, Costo: ${i.get('costoUnitario', 0)}, Stock: {i.get('cantidad')})" for i in inventory_list])
        
        # Contexto de mercado para la IA
        merca_context = market_context.get('MERCA', {}) if market_context else {}
        
        # 🧠 ¿Caitlyn ya conoce esta receta para este tamaño de porción?
        knowledge_col = get_database(get_settings().kitchy_database_name)["caitlyn_knowledge"]
        recipe_key = f"{negocio_id}_{dish_name}_{serving_size}_{len(inventory_list)}"
        
        past_recipe = await knowledge_col.find_one({"recipe_key": recipe_key, "type": "recipe_suggestion"})
        if past_recipe:
            print(f"🧠 [CAITLYN CHEF] Recuperando receta maestra de MongoDB para: {dish_name}")
            return {
                "success": True,
                "recipe": past_recipe["recipe"],
                "costoTotal": past_recipe["costo_total"],
                "precioSugerido": past_recipe["precio_sugerido"],
                "marginalidad": past_recipe["target_margin"],
                "source": "CAITLYN_MEMORY"
            }

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
            client = cls._get_client()
            response = await client.chat(
                model=COHERE_MODELS[1],
                message=prompt,
                preamble=cls.SYSTEM_PROMPT,
            )
            raw_text = response.text.strip()
            # Limpieza ultra-agresiva de JSON (Para dueños de restaurantes: no queremos basura de texto)
            if "{" in raw_text:
                raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]

            print(f"DEBUG: Texto limpio para JSON: {raw_text[:100]}...")
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

            # 🧠 APRENDIZAJE ETERNO: Guardar receta en MongoDB
            await knowledge_col.insert_one({
                "dish_name": dish_name,
                "recipe_key": recipe_key,
                "recipe": recipe_ingredients,
                "costo_total": round(float(costo_total), 2),
                "precio_sugerido": int(precio_sugerido),
                "target_margin": target_margin,
                "created_at": datetime.now().timestamp(),
                "type": "recipe_suggestion"
            })
            print(f"🏺 [CAITLYN CHEF] Receta de '{dish_name}' sellada en MongoDB.")

            return { 
                "success": True, 
                "recipe": recipe_ingredients,
                "costoTotal": round(float(costo_total), 2),
                "precioSugerido": int(precio_sugerido),
                "marginalidad": target_margin
            }
        except Exception as e:
            print(f"❌ [CAITLYN ERROR - RECIPE]: {e}. Buscando alternativa...")
            # Fallback: Si no hay receta exacta, al menos intentamos ver si existe alguna con nombre parecido
            knowledge_col = get_database(get_settings().kitchy_database_name)["caitlyn_knowledge"]
            any_recipe = await knowledge_col.find_one(
                {"dish_name": {"$regex": dish_name, "$options": "i"}, "type": "recipe_suggestion"}
            )
            if any_recipe:
                return {
                    "success": True,
                    "recipe": any_recipe["recipe"],
                    "costoTotal": any_recipe["costo_total"],
                    "precioSugerido": any_recipe["precio_sugerido"],
                    "source": "CAITLYN_STALE_MEMORY",
                    "message": "Encontré una receta similar en mi memoria, ¡ojalá te sirva! ✨"
                }
            return { "success": False, "error": "Caitlyn no tiene esta receta en memoria y la IA no responde. Intentemos más tarde." }

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
            
            # Reemplazo total a la API de Cohere
            client = cls._get_client()
            prompt = f"Datos de {product_name}:\n{costing_data}\nConsejo pro?"
            ai_response = await client.chat(
                model=COHERE_MODELS[1],
                message=prompt,
                preamble=cls.SYSTEM_PROMPT,
            )
            return {"success": True, "message": ai_response.text.strip(), "data": costing_data}
        except Exception as e:
            return {"success": False, "message": "Error", "error": str(e)}

    @classmethod
    async def get_dashboard_summary(cls, alerts: list, negocio_id: str = "global", user_name: str = "Socio/a") -> dict:
        """
        Genera un resumen estratégico del pulso del negocio.
        Usa memoria persistente por Hash para evitar re-análisis innecesarios.
        """
        try:
            if not alerts:
                return {"success": True, "message": "¡Todo excelente! Tus productos mantienen márgenes saludables hoy. ✨"}

            # 🔐 FIRMA DE VALORES: Hash profundo de nombres, tipos, VALORES e ID NEGOCIO
            import hashlib
            alert_snapshot = "|".join(sorted([
                f"{a.get('productName') or 'item'}:{a.get('type')}:{a.get('margin', '')}:{a.get('currentCost', '')}" 
                for a in alerts
            ]))
            pattern_hash = hashlib.md5(f"dash_v6_{negocio_id}_{alert_snapshot}".encode()).hexdigest()

            # 🧠 ¿Caitlyn ya tiene este estado analizado en MongoDB?
            db = get_database(get_settings().kitchy_database_name)
            knowledge_col = db["caitlyn_knowledge"]
            
            past_summary = await knowledge_col.find_one({
                "pattern_signature": pattern_hash,
                "type": "dashboard_summary"
            })

            if past_summary:
                print(f"🧠 [CAITLYN DASHBOARD] Memoria instantánea: Análisis de impacto recuperado.")
                return {
                    "success": True, 
                    "message": past_summary["summary_text"],
                    "source": "CAITLYN_MEMORY_DB"
                }

            # 👩‍💻 CONSULTA A LA IA (Si no hay patrón previo o es nuevo)
            print(f"🧠 [GEMINI DASHBOARD] Analizando {len(alerts)} puntos críticos del negocio...")
            
            try:
                prompt = (
                    f"Eres la socia estratégica de {user_name} en Kitchy.\n"
                    f"Tienes estas {len(alerts)} alertas de rentabilidad:\n"
                    f"{json.dumps(alerts, indent=2)}\n\n"
                    "=== TU MISIÓN COMENTADA ===\n"
                    f"Analiza el impacto financiero real. Dile a {user_name} qué es lo más urgente y dale un consejo amigable pero profesional.\n"
                    "No des una respuesta genérica. Sé breve y usa emojis. ✨🚀"
                )
                
                client = cls._get_gemini_client()
                # Gemini 3.1 Flash-Lite para máxima velocidad y ahorro
                response = client.models.generate_content(
                    model=GEMINI_MODELS[0], # Usamos 2.5-flash
                    contents=prompt
                )
                
                summary_text = response.text.strip()
                
                if not summary_text or len(summary_text) < 10:
                    raise Exception("Respuesta vacía de Gemini")

            except Exception as ai_err:
                print(f"⚠️ IA de parranda: {ai_err}. Buscando memoria histórica...")
                last_any_summary = await knowledge_col.find_one(
                    {"type": "dashboard_summary"},
                    sort=[("created_at", -1)]
                )
                if last_any_summary:
                    return {
                        "success": True,
                        "message": last_any_summary["summary_text"] + "\n\n(Caitlyn: *Gemini está descansando, te muestro mi último análisis guardado.* 😴)",
                        "source": "CAITLYN_STALE_MEMORY"
                    }
                return {"success": True, "message": f"¡{user_name}! No pude contactar a Gemini. Revisa tus alertas abajo.", "source": "CAITLYN_FAILSAFE"}

            # 🧠 APRENDIZAJE ETERNO
            await knowledge_col.update_one(
                {"pattern_signature": pattern_hash, "type": "dashboard_summary"},
                {
                    "$set": {
                        "summary_text": summary_text,
                        "alerts_count": len(alerts),
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )
            print(f"🏺 [CAITLYN DASHBOARD] Nuevo patrón de alertas sellado.")

            return {
                "success": True, 
                "message": summary_text,
                "source": "GEMINI_AI"
            }
            
        except Exception as e:
            print(f"❌ [CAITLYN ERROR - DASHBOARD SUMMARY]: {str(e)}")
            return {
                "success": False, 
                "message": "Caitlyn está analizando los números a mano ahora mismo, pero tus márgenes siguen bajo vigilancia. 👀", 
                "error": str(e)
            }

    _menu_patterns_cache = {}

    @classmethod
    async def suggest_menu_from_inventory(cls, inventory_list: list, target_margin: int = 65, negocio_id: str = "global", user_name: str = "Socio/a") -> dict:
        """
        Analiza el inventario y sugiere 5 platillos para maximizar rentabilidad o rotar inventario alto.
        Caitlyn usa memoria persistente en MongoDB para no llamar a la IA si el patrón de inventario es similar.
        """
        try:
            # 1. Filtro de inventario
            valid_items = [i for i in inventory_list if float(i.get('cantidad', 0)) > 0]
            valid_items.sort(key=lambda x: float(x.get('cantidad', 0)), reverse=True)
            
            # 🔐 FIRMA DE INVENTARIO: Hash de nombres, cantidades y ID NEGOCIO
            import hashlib
            inv_snapshot = "|".join([f"{i.get('nombre')}:{i.get('cantidad')}" for i in valid_items[:15]])
            pattern_signature = hashlib.md5(f"menu_v3_{negocio_id}_{inv_snapshot}_{target_margin}".encode()).hexdigest()

            # 🧠 ¿Caitlyn ya aprendió este patrón exacto de inventario en MongoDB?
            db = get_database(get_settings().kitchy_database_name)
            knowledge_col = db["caitlyn_knowledge"]
            past_menu = await knowledge_col.find_one({"pattern_signature": pattern_signature, "type": "menu_suggestion"})
            
            if past_menu:
                print(f"🧠 [CAITLYN CHEF] Memoria instantánea: Huella de inventario idéntica.")
                return {
                    "success": True,
                    "source": "CAITLYN_MEMORY_DB",
                    "ideas": past_menu["suggestions"][:5], # Asegurar 5
                    "message": "Menú sugerido por Caitlyn (Aprendizaje Persistente)"
                }

            # Tomamos el TOP 20 para enviar a la IA
            top_items = valid_items[:20]
            if not top_items:
                return {"success": False, "message": "Tu inventario está vacío o sin stock actualmente."}

            print(f"👩‍🍳 [GEMINI CHEF] Analizando cambio en el inventario para nuevas ideas...")
            inv_text = "\n".join([f"- {i.get('nombre')} (Stock: {i.get('cantidad')} {i.get('unidad')}, Costo: ${i.get('costoUnitario', 0)})" for i in top_items])

            prompt = (
                f"Eres el Chef Ejecutivo Maestro de {user_name} en Kitchy Panamá.\n\n"
                f"El inventario ha cambiado. Aquí tienes los insumos top disponibles:\n{inv_text}\n\n"
                "=== TU MISIÓN COMPLETA ===\n"
                "Invéntate 5 opciones de platillos, bebidas o combos altamente rentables. "
                "El objetivo es rotar este inventario rápido y maximizar ganancias.\n"
                f"1. Hazlo para un margen del {target_margin}%.\n"
                "2. Responde ÚNICAMENTE en este JSON estricto (no uses markdown ni bloques ```json):\n"
                "{\n"
                "  \"sugerencias\": [\n"
                "    {\n"
                "      \"nombre_plato\": \"Nombre del Plato\",\n"
                "      \"descripcion\": \"Breve descripción estratégica\",\n"
                "      \"costo_estimado\": 1.50,\n"
                "      \"precio_recomendado\": 4.50,\n"
                "      \"ingredientes_a_usar\": [\n"
                "        {\"nombre\": \"Nombre\", \"cantidad\": 1, \"unidad\": \"oz\", \"inventario\": \"ID_REAL_SI_EXISTE\"}\n"
                "      ]\n"
                "    }\n"
                "  ]\n"
                "}"
            )

            client = cls._get_client()
            ai_response = await client.chat(
                model=COHERE_MODELS[1],
                message=prompt,
                preamble=cls.SYSTEM_PROMPT,
            )
            
            # Limpieza ultra-agresiva para evitar el error de 'Extra Data'
            raw_text = ai_response.text.strip()
            if "{" in raw_text:
                raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
            
            data = json.loads(raw_text)
            sugerencias = data.get("sugerencias", [])
            
            # 🧠 APRENDIZAJE ETERNO: Guardar ideas de menú en MongoDB
            if sugerencias:
                await knowledge_col.update_one(
                    {"pattern_signature": pattern_signature, "type": "menu_suggestion"},
                    {
                        "$set": {
                            "suggestions": sugerencias,
                            "last_updated": datetime.now()
                        }
                    },
                    upsert=True
                )
                print(f"✅ [CAITLYN IMMORTAL] Huella de menú guardada/actualizada.")
            
            return {
                "success": True,
                "ideas": sugerencias,
                "source": "GEMINI_CHEF_AI",
                "message": "Menú inteligente generado con éxito"
            }
        except Exception as e:
            print(f"❌ [CAITLYN ERROR - MENU IDEAS]: {str(e)}")
            # Fallback: Último menú generado exitosamente
            db = get_database(get_settings().kitchy_database_name)
            knowledge_col = db["caitlyn_knowledge"]
            last_menu = await knowledge_col.find_one(
                {"type": "menu_suggestion"},
                sort=[("last_updated", -1)]
            )
            if last_menu:
                return {
                    "success": True, 
                    "ideas": last_menu["suggestions"], 
                    "source": "CAITLYN_STALE_MEMORY",
                    "message": "Caitlyn está meditando, aquí tienes sus últimas ideas guardadas. 🧠"
                }
            return {"success": False, "ideas": [], "error": str(e)}
