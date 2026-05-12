import httpx
import asyncio
import time
import json
import re
from pathlib import Path

class HiveService:
    BASE_URL = "http://localhost:8787/api"
    SESSION_ID = "caitlyn_session_v4"
    # La ruta se calculará dinámicamente con get_parts_dir()

    @classmethod
    def get_parts_dir(cls) -> Path:
        """Calcula la ruta de disco para la sesión actual."""
        return Path.home() / ".hive" / "queen" / "session" / cls.SESSION_ID / "conversations" / "parts"

    @classmethod
    def _read_messages_from_disk(cls) -> list[dict]:
        """Lee los mensajes directamente desde disco."""
        messages = []
        parts_dir = cls.get_parts_dir()
        if not parts_dir.exists():
            return messages
        
        try:
            files = sorted(parts_dir.iterdir())
            for part_file in files:
                if part_file.suffix != ".json":
                    continue
                try:
                    part = json.loads(part_file.read_text(encoding="utf-8"))
                    messages.append(part)
                except (json.JSONDecodeError, OSError):
                    continue
        except Exception as e:
            print(f"⚠️ Error leyendo disco: {e}")
            
        return messages

    @classmethod
    def _beautify_response(cls, text: str) -> str:
        """Limpia el formato Markdown y hace la respuesta más humana."""
        if not text:
            return ""
        
        # 1. Quitar negritas (**texto**)
        text = text.replace("**", "")
        # 2. Quitar puntos de lista (*)
        text = re.sub(r'^\s*[\*\-]\s*', '• ', text, flags=re.MULTILINE)
        # 3. Quitar asteriscos sueltos que queden
        text = text.replace("*", "")
        # 4. Limpiar espacios extra
        text = text.strip()
        
        return text

    @classmethod
    async def get_response(cls, text: str) -> str:
        """
        Envía un mensaje a Hive y retorna la respuesta embellecida.
        """
        async with httpx.AsyncClient(timeout=150.0) as client:
            try:
                # 1. Asegurar sesión
                session_url = f"{cls.BASE_URL}/sessions/{cls.SESSION_ID}"
                resp = await client.get(session_url)
                
                if resp.status_code == 404:
                    print(f"🆕 Creando sesión de Hive ({cls.SESSION_ID})...")
                    await client.post(f"{cls.BASE_URL}/sessions", json={
                        "session_id": cls.SESSION_ID,
                        "initial_prompt": (
                            "Eres Caitlyn, la interfaz de voz de una app de mapas. "
                            "Misión: Responde siempre de forma amigable y natural en español. "
                            "Tu objetivo es ayudar al usuario con datos reales de clima y rutas. "
                            "REGLA DE ORO: Siempre usa tus herramientas MCP de 'ionic-notif' para favoritos, clima e incidencias. "
                            "Cuando menciones paradas o destinos en una ruta, SIEMPRE añade sus coordenadas al final "
                            "en formato (lat, lng), por ejemplo: '(8.98, -79.51)'. Es vital para que el GPS las trace."
                        )
                    })
                    await asyncio.sleep(2)

                # 2. Conteo inicial en disco
                initial_count = len(cls._read_messages_from_disk())

                # 3. Enviar mensaje con HINT para potenciar el uso de tools
                print(f"📤 Delegando a Hive: '{text[:50]}...'")
                chat_resp = await client.post(
                    f"{cls.BASE_URL}/sessions/{cls.SESSION_ID}/chat",
                    json={"message": (
                        f"{text}\n\n"
                        "(HINT: Si vas a trazar una ruta con paradas, usa 'set_active_navigation' con TODA la lista "
                        "de coordenadas [origen, parada1, ..., destino]. Si menciono 'casa', búscala en favoritos.)"
                    )}
                )
                
                if chat_resp.status_code != 200:
                    return f"Caitlyn: 'Hive tuvo un pequeño problema técnico. ¿Lo intentamos de nuevo?'"

                # 4. Polling esperando respuesta real
                start_time = time.time()
                timeout_limit = 120
                base_count = initial_count + 1 
                
                while time.time() - start_time < timeout_limit:
                    await asyncio.sleep(1)
                    current_messages = cls._read_messages_from_disk()
                    
                    if len(current_messages) > base_count:
                        nuevos = current_messages[base_count:]
                        
                        for msg in reversed(nuevos):
                            role = msg.get("role")
                            content = msg.get("content", "").strip()
                            
                            if role == "assistant" and content:
                                # Filtrar mensajes técnicos
                                filler = ["no prose", "proceeding with tools", "no text generated"]
                                if not any(f in content.lower() for f in filler):
                                    # ✨ EMBELLECER RESPUESTA ✨
                                    final_text = cls._beautify_response(content)
                                    
                                    # 🔍 BUSCAR TOOL CALLS DE NAVEGACIÓN
                                    locations = []
                                    for m in current_messages[base_count:]:
                                        if m.get("role") == "assistant" and "tool_calls" in m:
                                            for tc in m["tool_calls"]:
                                                func = tc.get("function", {})
                                                if func.get("name") == "set_active_navigation":
                                                    try:
                                                        args = json.loads(func.get("arguments", "{}"))
                                                        stops_str = args.get("stops_json", "[]")
                                                        locations = json.loads(stops_str)
                                                        print(f"📍 Rutas extraídas de tool_call: {len(locations)} puntos")
                                                    except:
                                                        pass

                                    print(f"✅ Respuesta capturada.")
                                    return {
                                        "message": final_text,
                                        "locations": locations
                                    }
                
                return "Caitlyn: 'Hive está analizando los datos todavía. Dame un segundito y vuelve a preguntarme.'"

            except Exception as e:
                print(f"💥 Error en HiveService: {e}")
                return "Caitlyn: 'Parece que perdí la señal con mis motores de IA. ¿Verificas la terminal?'"
