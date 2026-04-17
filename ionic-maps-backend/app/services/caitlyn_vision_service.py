import os
import json
from typing import Optional, List, Dict
from app.database import get_database
from rapidfuzz import process, fuzz
import cv2
import numpy as np
import base64
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    print("⚠️ EasyOCR (o torch) no está disponible. El escaneo local estará deshabilitado.")
    EASYOCR_AVAILABLE = False
except Exception as e:
    print(f"⚠️ Error cargando EasyOCR (DLL Crash?): {str(e)}")
    EASYOCR_AVAILABLE = False
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
        if not EASYOCR_AVAILABLE:
            return None
            
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
    def _preprocess_for_ocr(cls, img):
        """
        Preprocesamiento agresivo de imagen para maximizar calidad del OCR.
        1. Escala de grises
        2. Reducción de ruido (bilateral filter — preserva bordes de texto)
        3. CLAHE (contraste adaptativo local) — rescata texto desvanecido
        4. Umbral adaptativo (binarización) — separa tinta del fondo
        5. Limpieza morfológica — elimina puntos y manchas residuales
        """
        # 1. Escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Reducción de ruido conservando bordes
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # 3. CLAHE — hiper-contraste adaptativo local
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # 4. Umbral adaptativo (funciona mejor que Otsu en tickets con fondo no uniforme)
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 10
        )

        # 5. Limpieza morfológica — quitar puntos y manchas pequeñas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        return cleaned

    @classmethod
    def _extract_products_from_text(cls, full_text: str) -> list:
        """
        Intenta parsear líneas de productos desde el texto crudo del OCR.
        Busca patrones como: NOMBRE_PRODUCTO  PRECIO (ej: 'Pollo Asado 7.50')
        """
        import re
        productos = []

        # Patron 1: nombre seguido de un precio al final de la línea
        # Ej: "ARROZ GRANO LARGO 5LB   3.49"  o  "Coca Cola 600ml $1.25"
        pattern = re.compile(
            r'([A-Za-záéíóúñÁÉÍÓÚÑ][A-Za-záéíóúñÁÉÍÓÚÑ0-9\s\.\-/]+?)\s+'
            r'\$?\s*(\d+[.,]\d{2})\s*$',
            re.MULTILINE
        )

        for match in pattern.finditer(full_text):
            nombre = match.group(1).strip()
            precio_str = match.group(2).replace(',', '.')

            # Filtrar items basura (muy cortos o que son solo números)
            if len(nombre) < 3 or nombre.replace(' ', '').isdigit():
                continue

            try:
                precio = float(precio_str)
                if 0.01 <= precio <= 9999:  # Rango razonable
                    productos.append({
                        "nombre": nombre,
                        "cantidad": 1,
                        "unidad": "und",
                        "precioUnitario": precio,
                        "categoriaSugerida": "ingrediente",
                        "precioReventaSugerido": None
                    })
            except ValueError:
                continue

        return productos

    @classmethod
    async def blind_scan_invoice(cls, base64_image: str) -> Dict:
        """
        MODO SUPERVIVENCIA: Lee toda la foto cuando Gemini falla.
        Aplica preprocesamiento de imagen antes del OCR para máxima calidad.
        Busca RUC, Totales y Nombres de forma ciega.
        """
        img = cls._base64_to_cv2(base64_image)
        reader = cls._get_reader()

        if reader is None:
            return {
                "success": False,
                "metodo": "blind_local_scan",
                "productos": [],
                "fiscal": {},
                "error": "EasyOCR no está disponible en este servidor."
            }

        # Preprocesar la imagen para mejorar la calidad del OCR
        processed = cls._preprocess_for_ocr(img)

        print(f"🔬 Caitlyn Vision: Imagen preprocesada ({processed.shape[1]}x{processed.shape[0]}px)")

        # Leer el texto de la imagen procesada con parámetros optimizados
        text_data = reader.readtext(
            processed,
            detail=0,
            paragraph=True,         # Agrupa texto en párrafos lógicos
            contrast_ths=0.3,       # Umbral de contraste más agresivo
            adjust_contrast=0.7,    # Ajuste de contraste EasyOCR
            width_ths=0.7,          # Ancho mínimo para agrupar
        )
        full_text = "\n".join(text_data)

        print(f"🕵️‍♀️ Caitlyn 'Escaneo Ciego' detectó: {full_text[:150]}...")

        # Lógica de extracción básica por Regex
        import re
        ruc_match = re.search(r'R\.?U\.?C\.?[:\s]*([0-9][\d\-\.]+)', full_text, re.IGNORECASE)
        total_match = re.search(r'TOTAL[:\s]*\$?\s*([\d]+[.,]\d{2})', full_text, re.IGNORECASE)
        subtotal_match = re.search(r'SUB\s*TOTAL[:\s]*\$?\s*([\d]+[.,]\d{2})', full_text, re.IGNORECASE)
        itbms_match = re.search(r'I\.?T\.?B\.?M\.?S\.?[:\s]*\$?\s*([\d]+[.,]\d{2})', full_text, re.IGNORECASE)

        # Intentar extraer productos del texto
        productos = cls._extract_products_from_text(full_text)
        print(f"📦 Caitlyn extrajo {len(productos)} productos del escaneo ciego.")

        return {
            "success": True,
            "metodo": "blind_local_scan",
            "full_text_detected": full_text,
            "productos": productos,
            "total_detectados": len(productos),
            "fiscal": {
                "ruc": ruc_match.group(1) if ruc_match else None,
                "total": total_match.group(1) if total_match else None,
                "subtotal": subtotal_match.group(1) if subtotal_match else None,
                "itbms": itbms_match.group(1) if itbms_match else None,
                "proveedor": "Desconocido (Escaneo Local)"
            },
            "error_fallback": "Gemini no respondió, activamos escaneo local de emergencia."
        }

