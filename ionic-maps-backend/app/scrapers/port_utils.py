"""
Utilidades de limpieza y extracción de nombres de puertos.
Separa la lógica de texto de la lógica de scraping.
"""
import re
import unicodedata


def extraer_busqueda(texto: str, usar_locode: bool = True) -> str:
    """
    Extrae el término óptimo de búsqueda para una naviera.
    
    Estrategia:
        - MSC (usar_locode=True):  Prioriza LOCODE (ej: PACFZ)
        - Maersk (usar_locode=False): Usa nombre + país (ej: "Cristobal Panama")
    
    Args:
        texto: Texto completo del puerto (ej: "Cristóbal / Colón, Panama (PACFZ)")
        usar_locode: Si True, intenta extraer el código LOCODE primero
    
    Returns:
        Término limpio para escribir en el buscador de la naviera
    """
    # Quitar tildes y acentos
    limpio = "".join(
        c for c in unicodedata.normalize('NFKD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    
    # 1) LOCODE si el sitio lo soporta (ej: PACFZ, CNSHA)
    if usar_locode:
        match = re.search(r"\(([A-Z]{5})\)", texto)
        if match:
            return match.group(1)
    
    # 2) Nombre principal (antes de la primera coma o "/")
    nombre = limpio.split(',')[0].split('/')[0].split('(')[0].strip()
    nombre = re.sub(r"[^a-zA-Z0-9 ]", "", nombre).strip()
    
    # 3) Contexto geográfico: último segmento tras coma (país o región)
    contexto = ""
    if "," in limpio:
        ultimo = limpio.split(',')[-1].split('(')[0].strip()
        ultimo = re.sub(r"[^a-zA-Z ]", "", ultimo).strip()
        if ultimo and ultimo.lower() != nombre.lower():
            contexto = ultimo
    
    return f"{nombre} {contexto}".strip() if contexto else nombre


def detectar_sitio(url: str) -> str:
    """Extrae el nombre del sitio de la URL."""
    if "maersk" in url:
        return "maersk"
    elif "msc" in url:
        return "msc"
    elif "searates" in url:
        return "searates"
    return "general"


def sitio_soporta_locode(url: str) -> bool:
    """Determina si el sitio soporta búsqueda por LOCODE."""
    return "msc" in url
