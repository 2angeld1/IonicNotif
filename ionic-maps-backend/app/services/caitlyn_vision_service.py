import os
import json
from typing import Optional, List, Dict
from app.database import get_database
from rapidfuzz import process, fuzz
import cv2
import numpy as np
import base64
import easyocr
from datetime import datetime

class CaitlynVisionService:
    """
    Servicio 'Caitlyn Vision' para el escaneo inteligente y autónomo de facturas.
    Gestiona la colección 'caitlyn_vision' en MongoDB para layouts y alias.
    """
    
    COLLECTION_NAME = "caitlyn_vision"
    _reader = None

    @classmethod
    def _get_reader(cls):
        """Inicialización perezosa de EasyOCR (en español e inglés)"""
        if cls._reader is None:
            # Optimizamos para CPU si no hay GPU disponible
            cls._reader = easyocr.Reader(['es', 'en'], gpu=False)
        return cls._reader

    @classmethod
    def _base64_to_cv2(cls, b64_string: str):
        """Convierte un base64 a una imagen de OpenCV"""
        if "," in b64_string:
            b64_string = b64_string.split(",")[1]
        img_data = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    @classmethod
    async def get_layout_by_ruc(cls, ruc: str) -> Optional[Dict]:
        """
        Busca si Caitlyn ya conoce el formato (layout) de este RUC.
        """
        db = get_database(get_settings().kitchy_database_name)
        layout = await db[cls.COLLECTION_NAME].find_one({
            "type": "invoice_layout", 
            "ruc": ruc
        })
        return layout

    @classmethod
    async def save_layout(cls, ruc: str, provider: str, layout_map: Dict):
        """
        Guarda un nuevo mapa de factura en la memoria visual de Caitlyn.
        """
        db = get_database(get_settings().kitchy_database_name)
        await db[cls.COLLECTION_NAME].update_one(
            {"type": "invoice_layout", "ruc": ruc},
            {
                "$set": {
                    "provider_name": provider,
                    "layout_map": layout_map,
                    "updated_at": datetime.utcnow().isoformat()
                }
            },
            upsert=True
        )

    @classmethod
    async def match_product_alias(cls, invoice_text: str, inventory_items: List[Dict], negocio_id: str = "global") -> Optional[str]:
        """
        Usa lógica difusa (Fuzzy Matching) para encontrar el producto en el inventario.
        Si Caitlyn ya aprendió un alias antes para este negocio, lo usa directamente.
        """
        db = get_database(get_settings().kitchy_database_name)
        
        # 1. Buscar en la memoria de alias aprendidos (Segmentado por Negocio)
        alias_doc = await db[cls.COLLECTION_NAME].find_one({
            "type": "product_alias",
            "invoice_text": invoice_text,
            "negocio_id": negocio_id
        })
        
        if alias_doc:
            return alias_doc["product_id"]

        # 2. Si no hay alias, usar RapidFuzz para adivinar el mejor match
        # inventory_items debe ser una lista de dicts con 'nombre' e '_id'
        choices = [item["nombre"] for item in inventory_items]
        if not choices:
            return None

        match = process.extractOne(invoice_text, choices, scorer=fuzz.WRatio)
        
        if match and match[1] > 85: # 85% de confianza mínima
            matched_name = match[0]
            # Encontrar el ID original
            for item in inventory_items:
                if item["nombre"] == matched_name:
                    return str(item["_id"])
        
        return None

    @classmethod
    async def learn_alias(cls, invoice_text: str, product_id: str, negocio_id: str = "global"):
        """
        Guarda un nuevo apodo de producto para no preguntar la próxima vez.
        Segmentado por negocio para evitar conflictos de IDs.
        """
        db = get_database(get_settings().kitchy_database_name)
        await db[cls.COLLECTION_NAME].update_one(
            {"type": "product_alias", "invoice_text": invoice_text, "negocio_id": negocio_id},
            {"$set": {"product_id": str(product_id), "updated_at": datetime.utcnow().isoformat()}},
            upsert=True
        )

    @classmethod
    async def process_invoice_locally(cls, base64_image: str, layout_map: Dict) -> Dict:
        """
        Lee una factura usando un mapa de coordenadas guardado, sin usar Gemini.
        """
        img = cls._base64_to_cv2(base64_image)
        h, w, _ = img.shape
        reader = cls._get_reader()
        
        results = {
            "productos": [],
            "fiscal": {},
            "success": True,
            "metodo": "local_vision"
        }

        # 1. Extraer Datos Fiscales (RUC, Total, Fecha)
        for key, box in layout_map.get("fiscal_boxes", {}).items():
            # Convertir coordenadas relativas (0-1) a píxeles
            x1, y1 = int(box['x1'] * w), int(box['y1'] * h)
            x2, y2 = int(box['x2'] * w), int(box['y2'] * h)
            
            roi = img[y1:y2, x1:x2]
            if roi.size == 0: continue
            
            text_results = reader.readtext(roi, detail=0)
            results["fiscal"][key] = " ".join(text_results)

        # 2. Extraer Filas de Productos
        # Este es un ejemplo simplificado: asume que conocemos el área de la tabla
        table_box = layout_map.get("table_area")
        if table_box:
            tx1, ty1 = int(table_box['x1'] * w), int(table_box['y1'] * h)
            tx2, ty2 = int(table_box['x2'] * w), int(table_box['y2'] * h)
            table_roi = img[ty1:ty2, tx1:tx2]
            
            # Leer toda la tabla de un golpe (EasyOCR es bueno en esto)
            table_data = reader.readtext(table_roi)
            # Aquí iría lógica de agrupación por líneas Y/X para reconstruir filas
            # ... (implementación compleja de reconstrucción de tabla)
            
        return results

    @classmethod
    async def blind_scan_invoice(cls, base64_image: str) -> Dict:
        """
        MODO SUPERVIVENCIA: Lee toda la foto cuando Gemini falla.
        Busca RUC, Totales y Nombres de forma ciega.
        """
        img = cls._base64_to_cv2(base64_image)
        reader = cls._get_reader()
        
        # Leer todo el texto de la imagen (Esto toma un poco más de tiempo)
        text_data = reader.readtext(img, detail=0)
        full_text = " ".join(text_data)
        
        print(f"🕵️‍♀️ Caitlyn 'Escaneo Ciego' detectó: {full_text[:100]}...")

        # Lógica de extracción básica por Regex (Intentar recuperar algo útil)
        import re
        ruc_match = re.search(r'RUC[:\s]*([\d-]+)', full_text, re.IGNORECASE)
        total_match = re.search(r'TOTAL[:\s]*\$?\s*([\d,.]+)', full_text, re.IGNORECASE)

        return {
            "success": True,
            "metodo": "blind_local_scan",
            "full_text_detected": full_text,
            "productos": [], # En modo ciego es difícil separar productos sin el mapa
            "fiscal": {
                "ruc": ruc_match.group(1) if ruc_match else None,
                "total": total_match.group(1) if total_match else None,
                "proveedor": "Desconocido (Escaneo Local)"
            },
            "error_fallback": "Gemini no respondió, activamos escaneo local de emergencia."
        }
