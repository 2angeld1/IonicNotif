
from app.services.core.web_search_service import WebSearchService
import json

# 🎯 Aquí puedes cambiar lo que quieres que Caitlyn busque
query = "Merca Panama"

print(f"\n🕵️‍♂️ Caitlyn investigando en internet: '{query}'...")
print("-" * 50)

results = WebSearchService.search_panama_prices(query)

if results:
    print(f"✅ ¡Encontré {len(results)} fuentes relevantes!\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   🔗 {r['link']}")
        print(f"   📄 {r['snippet'][:150]}...")
        print("-" * 30)
else:
    print("\n❌ No pude encontrar resultados en este momento.")
    print("Tip: Prueba con palabras clave más cortas (ej: 'Gasolina Panama').")
