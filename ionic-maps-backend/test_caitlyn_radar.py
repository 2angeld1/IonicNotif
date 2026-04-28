
import asyncio
import os
from dotenv import load_dotenv

# Cargamos entorno ANTES de importar servicios
load_dotenv()

from app.services.market_service import MarketService
from app.database import connect_to_mongo, close_mongo_connection
import json

async def test_radar():
    print("🚀 Probando el Nuevo Radar de Caitlyn (Flashazo + Caché + Fallback)")
    print("="*60)
    
    # Conectamos a Mongo para que el caché funcione
    await connect_to_mongo()
    
    tipos = ['ACODECO', 'FUEL', 'MERCA']
    
    for tipo in tipos:
        print(f"\n📡 Iniciando escaneo de {tipo}...")
        try:
            result = await MarketService.parse_market_image(tipo)
            
            if result['success']:
                print(f"✅ Éxito usando método: {result['metodo']}")
                print(f"📊 Datos extraídos: {json.dumps(result['data'], indent=2)}")
            else:
                print(f"❌ Falló el escaneo de {tipo}: {result.get('error')}")
                print(f"📝 Detalle: {result.get('detalle')}")
        except Exception as e:
            print(f"💥 Error inesperado: {e}")
        
        print("-" * 40)
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_radar())
