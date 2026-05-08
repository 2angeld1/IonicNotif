import easyocr
import os
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    _reader = None

    @classmethod
    def get_reader(cls):
        """Inicializa el lector de EasyOCR (Singleton)"""
        if cls._reader is None:
            logger.info("🧠 Inicializando EasyOCR (Modo CPU)...")
            # Usamos gpu=False para máxima compatibilidad en entornos virtualizados
            cls._reader = easyocr.Reader(['en', 'es'], gpu=False)
        return cls._reader

    @classmethod
    def extract_text_from_image(cls, image_path: str):
        """Extrae el texto de una imagen dada su ruta"""
        if not os.path.exists(image_path):
            logger.error(f"❌ Imagen no encontrada en: {image_path}")
            return None

        try:
            reader = cls.get_reader()
            logger.info(f"🔍 Escaneando imagen con EasyOCR: {image_path}")
            
            # detail=0 devuelve solo el texto, lo cual es más fácil para procesar inicialmente
            results = reader.readtext(image_path, detail=0)
            
            logger.info(f"✅ OCR completado. Se detectaron {len(results)} bloques de texto.")
            return results
        except Exception as e:
            logger.error(f"❌ Error durante el proceso de OCR: {e}")
            return None

    @classmethod
    def parse_itineraries(cls, text_blocks: list):
        """
        Lógica inicial para intentar estructurar los datos extraídos.
        Busca patrones comunes en SeaRates (Fechas, Navieras, Precios).
        """
        if not text_blocks:
            return []

        # Por ahora devolvemos el texto limpio, pero aquí es donde
        # pondremos expresiones regulares para extraer la tabla real.
        # Caitlyn usará este output para 'pensar'.
        return text_blocks
