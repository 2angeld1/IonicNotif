
import requests
from bs4 import BeautifulSoup
import json

class DirectScraperService:
    """
    Servicio para dar un 'flashazo' directo a webs conocidas de Panamá.
    Evita usar Google Search si podemos ir directo a la fuente.
    """
    
    SOURCES = {
        'FUEL': 'https://www.acodeco.gob.pa/inicio/estadisticas-precios/precios-2/',
        'MERCA': 'https://www.telemetro.com/precios-merca-panama-a4237',
        'ACODECO': 'https://www.acodeco.gob.pa/inicio/estadisticas-precios/precios-2/'
    }

    @classmethod
    def get_page_content(cls, tipo: str):
        url = cls.SOURCES.get(tipo)
        if not url:
            return None
            
        print(f"📸 [DIRECT-SCRAPER] Dando un flashazo a: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            if response.status_code != 200:
                print(f"⚠️ [DIRECT-SCRAPER] Error de acceso: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Si es ACODECO, buscamos específicamente links a PDFs
            pdf_links = []
            if tipo == 'ACODECO' or tipo == 'FUEL':
                for a in soup.find_all('a', href=True):
                    if a['href'].endswith('.pdf'):
                        pdf_links.append(a['href'])
            
            # Limpiamos el HTML para el texto
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text(separator=' ', strip=True)
            
            # Devolvemos texto + links a PDFs para que Gemini decida
            return {
                "text": text[:5000],
                "pdf_links": pdf_links[:5] # Los 5 más recientes
            }
            
        except Exception as e:
            print(f"❌ [DIRECT-SCRAPER ERROR]: {e}")
            return None

    @classmethod
    def fetch_custom_url(cls, url: str):
        """Dada una URL aprendida, intenta extraer su texto."""
        print(f"📸 [DIRECT-SCRAPER] Flashazo a URL personalizada: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
                
            return soup.get_text(separator=' ', strip=True)[:8000]
        except:
            return None

    @classmethod
    def download_file(cls, url: str):
        """Descarga un archivo (PDF) y devuelve sus bytes."""
        print(f"📥 [DIRECT-SCRAPER] Descargando archivo: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, timeout=20, verify=False)
            if response.status_code == 200:
                return response.content
            return None
        except:
            return None

    @classmethod
    def extract_text_from_pdf(cls, pdf_bytes: bytes) -> str:
        """Extrae texto de un PDF localmente usando pdfplumber."""
        import io
        import pdfplumber
        
        print("📖 [DIRECT-SCRAPER] Extrayendo texto del PDF localmente...")
        full_text = ""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            return full_text
        except Exception as e:
            print(f"❌ [DIRECT-SCRAPER] Error extrayendo texto local: {e}")
            return ""
