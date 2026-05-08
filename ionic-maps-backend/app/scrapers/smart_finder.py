"""
SmartFinder - Buscador inteligente de elementos web.
Usa una cadena de estrategias para encontrar campos sin hardcodear selectores.
Funciona con Shadow DOM, Web Components, y cualquier framework.
"""
import re
import asyncio


class SmartFinder:
    # Palabras clave para cada tipo de campo
    ORIGIN_WORDS = re.compile(r"origin|from|departure|salida|loading|pol|pickup|port.?load|ciudad|city|location", re.I)
    DEST_WORDS = re.compile(r"destination|to|arrival|llegada|discharge|pod|delivery|port.?dis|ciudad|city|location", re.I)
    SEARCH_WORDS = re.compile(r"search|find|buscar|submit|go|get|schedule|rate", re.I)

    # JavaScript que escanea TODO el DOM (incluyendo Shadow DOMs e IFRAMES)
    DOM_SCAN_JS = """() => {
        const results = [];
        function scan(root) {
            if (!root) return;
            
            // 1. Buscar inputs en este root
            const els = root.querySelectorAll('input:not([type="hidden"]), textarea, [role="combobox"], [role="searchbox"]');
            els.forEach(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                if (rect.width < 5 || rect.height < 5 || style.display === 'none' || style.visibility === 'hidden') return;
                
                let labelText = '';
                if (el.id) {
                    const lbl = (root.querySelector ? root : document).querySelector('label[for="' + el.id + '"]');
                    if (lbl) labelText = lbl.textContent.trim();
                }
                
                results.push({
                    placeholder: el.placeholder || el.getAttribute('placeholder') || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    id: el.id || '',
                    name: el.name || '',
                    role: el.getAttribute('role') || '',
                    labelText: labelText,
                    nearbyText: el.parentElement ? el.parentElement.textContent.substring(0, 100).trim() : '',
                    x: Math.round(rect.left + rect.width / 2),
                    y: Math.round(rect.top + rect.height / 2),
                });
            });

            // 2. Entrar en Shadow DOMs
            root.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot) scan(el.shadowRoot);
                // 3. Entrar en Iframes (si es el mismo origen)
                if (el.tagName === 'IFRAME') {
                    try { scan(el.contentDocument); } catch(e) {}
                }
            });
        }
        scan(document);
        return results;
    }"""

    @classmethod
    async def find_origin(cls, page):
        """Encuentra el campo de origen."""
        # Estrategia 1: Playwright semántico
        for method in [
            lambda: page.get_by_role("textbox", name=re.compile(r"origin|from|departure|salida", re.I)),
            lambda: page.get_by_placeholder(re.compile(r"origin|from|departure", re.I)),
        ]:
            try:
                loc = method()
                if await loc.first.is_visible(timeout=2000):
                    return loc.first
            except:
                continue

        return await cls._find_by_dom_scan(page, cls.ORIGIN_WORDS, index=0)

    @classmethod
    async def find_destination(cls, page, exclude_coords=None):
        """Encuentra el campo de destino, evitando las coordenadas del origen."""
        # Estrategia 1: Playwright semántico
        for method in [
            lambda: page.get_by_role("textbox", name=re.compile(r"destination|to|arrival|llegada", re.I)),
            lambda: page.get_by_placeholder(re.compile(r"destination|to|arrival", re.I)),
        ]:
            try:
                loc = method()
                if await loc.first.is_visible(timeout=2000):
                    # Verificar que no sea el mismo que el origen por posición
                    box = await loc.first.bounding_box()
                    if box and exclude_coords:
                        dist = abs(box['x'] + box['width']/2 - exclude_coords['x']) + abs(box['y'] + box['height']/2 - exclude_coords['y'])
                        if dist < 10: continue # Es el mismo
                    return loc.first
            except:
                continue

        return await cls._find_by_dom_scan(page, cls.DEST_WORDS, index=1, exclude_coords=exclude_coords)

    @classmethod
    async def find_date_input(cls, page):
        """Encuentra el campo de fecha."""
        date_words = ["date", "departure", "arrival", "fecha", "cuando"]
        for method in [
            lambda: page.get_by_role("textbox", name=re.compile(r"date|departure|arrival", re.I)),
            lambda: page.get_by_placeholder(re.compile(r"date|yyyy|mm|dd", re.I)),
        ]:
            try:
                loc = method()
                if await loc.first.is_visible(timeout=2000):
                    return loc.first
            except:
                continue
        return await cls._find_by_dom_scan(page, date_words, index=0)

    @classmethod
    async def detectar_formato_fecha(cls, date_input):
        """Intenta deducir el formato de fecha mirando el placeholder o atributos."""
        placeholder = await date_input.get_attribute("placeholder") or ""
        placeholder = placeholder.lower()
        
        if "dd" in placeholder and "mm" in placeholder and "yyyy" in placeholder:
            # Detectar separador
            sep = "/" if "/" in placeholder else "-"
            # Detectar orden
            parts = placeholder.split(sep)
            return {"sep": sep, "order": [p[0] for p in parts if p]} # e.g. ['m', 'd', 'y']
        
        # Default inteligente si no hay placeholder
        return None

    @classmethod
    async def find_search_button(cls, page):
        """Encuentra el botón de búsqueda de itinerarios, evitando el buscador global."""
        # Palabras más específicas primero
        for method in [
            lambda: page.locator('button:has-text("Search a schedule")'),
            lambda: page.locator('button:has-text("Find a schedule")'),
            lambda: page.locator('.mc-button:has-text("search")'), 
            lambda: page.locator('button[data-test="search-button"]'), # Maersk específico
            lambda: page.locator('#search-button'),
            lambda: page.locator('.msc-button:has-text("search")').last, 
            lambda: page.locator('main button:has-text("search")'), 
            lambda: page.locator('button[type="submit"]:has-text("search")'),
        ]:
            try:
                loc = method()
                if await loc.first.is_visible(timeout=2000):
                    return loc.first
            except:
                continue
        
        # Fallback: buscar cualquier botón con "search" pero que NO esté en el header
        try:
            btn = page.locator('button:not(header button):has-text("search")').first
            if await btn.is_visible(timeout=1000): return btn
        except: pass

        # Corregir: pasar regex, no lista
        pattern = re.compile(r"schedule|search|find", re.I)
        return await cls._find_by_dom_scan(page, pattern, index=0)

    @classmethod
    async def _find_by_dom_scan(cls, page, keywords_pattern, index=0, exclude_coords=None):
        try:
            inputs = await page.evaluate(cls.DOM_SCAN_JS)
            if not inputs: return None

            # Si nos pasan una lista, la convertimos a regex
            if isinstance(keywords_pattern, list):
                keywords_pattern = re.compile("|".join(keywords_pattern), re.I)

            # Filtrar por excluidos
            if exclude_coords:
                inputs = [inp for inp in inputs if abs(inp['x'] - exclude_coords['x']) + abs(inp['y'] - exclude_coords['y']) > 20]

            # Puntuar cada input
            scored = []
            for inp in inputs:
                text_blob = f"{inp['placeholder']} {inp['ariaLabel']} {inp['id']} {inp['name']} {inp['labelText']} {inp['nearbyText']}"
                matches = len(keywords_pattern.findall(text_blob))
                scored.append((matches, inp))

            scored.sort(key=lambda x: x[0], reverse=True)

            if scored and scored[0][0] > 0:
                best = scored[0][1]
            else:
                if index < len(inputs):
                    best = inputs[index]
                elif len(inputs) > 0:
                    best = inputs[-1]
                else:
                    return None

            await page.mouse.move(best['x'], best['y'])
            await page.mouse.click(best['x'], best['y'])
            await asyncio.sleep(0.3)

            if best['id']:
                return page.locator(f"#{best['id']}")
            return None

        except Exception as e:
            print(f"❌ [SmartFinder] Error en DOM scan: {e}")
            return None

    @classmethod
    async def smart_fill(cls, page, locator_or_none, text, delay=150):
        """
        Rellena un campo de forma inteligente.
        Retorna True si tuvo éxito, False si no.
        """
        if locator_or_none:
            try:
                # Si es un locator de Playwright
                await locator_or_none.scroll_into_view_if_needed()
                await locator_or_none.click(force=True, timeout=5000)
                await locator_or_none.fill("")
                await locator_or_none.press_sequentially(text, delay=delay)
                return True
            except:
                pass
        
        # Si llegamos aquí y no tenemos locator, es porque find_by_dom_scan ya hizo click por coordenadas
        # O porque find_by_dom_scan no encontró nada y devolvió None.
        # Solo escribimos si el click previo fue exitoso (esto lo controlamos en el caller o verificando focus)
        
        # Verificamos si hay algún elemento en focus
        has_focus = await page.evaluate("document.activeElement !== document.body")
        if has_focus:
            await page.keyboard.type(text, delay=delay)
            return True
        
        return False
