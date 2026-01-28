import json
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

def train_brain():
    print("🧠 Entrenando a Calitin...")
    
    # 1. Cargar datos
    with open('app/ai/dataset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    texts = [item['text'] for item in data]
    intents = [item['intent'] for item in data]
    
    # 2. Crear Pipeline (Vectorizador + Clasificador)
    # CountVectorizer convierte texto a números
    # MultinomialNB es excelente para clasificación de texto con pocos datos
    model = make_pipeline(CountVectorizer(), MultinomialNB())
    
    # 3. Entrenar
    model.fit(texts, intents)
    
    # 4. Guardar el cerebro (.pkl)
    with open('app/ai/brain.pkl', 'wb') as f:
        pickle.dump(model, f)
        
    print(f"✅ Entrenamiento completado con {len(texts)} ejemplos.")
    print("💾 Cerebro guardado en 'app/ai/brain.pkl'")

if __name__ == "__main__":
    train_brain()
