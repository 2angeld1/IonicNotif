import os
import io
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, List, Tuple
from app.database import get_database
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from app.models.schemas import (
    PredictionFeatures, 
    PredictionResult, 
    WeatherCondition,
    Trip
)

# Directorio para guardar modelos
MODEL_DIR = "app/ml_models"
MODEL_PATH = os.path.join(MODEL_DIR, "route_predictor.joblib")
ENCODERS_PATH = os.path.join(MODEL_DIR, "encoders.joblib")


class MLService:
    """Servicio de Machine Learning para predicción de tiempos de ruta"""
    
    model: Optional[GradientBoostingRegressor] = None
    weather_encoder: Optional[LabelEncoder] = None
    is_trained: bool = False
    
    # Factores heurísticos (usados cuando no hay modelo entrenado)
    WEATHER_FACTORS = {
        WeatherCondition.CLEAR: 1.0,
        WeatherCondition.CLOUDS: 1.0,
        WeatherCondition.DRIZZLE: 1.1,
        WeatherCondition.RAIN: 1.25,
        WeatherCondition.THUNDERSTORM: 1.4,
        WeatherCondition.SNOW: 1.5,
        WeatherCondition.MIST: 1.15,
        WeatherCondition.FOG: 1.3,
    }
    
    # Factores por hora (hora pico)
    HOUR_FACTORS = {
        # Madrugada
        0: 0.85, 1: 0.8, 2: 0.8, 3: 0.8, 4: 0.85, 5: 0.9,
        # Mañana rush
        6: 1.1, 7: 1.3, 8: 1.4, 9: 1.25, 10: 1.1, 11: 1.05,
        # Mediodía
        12: 1.1, 13: 1.05, 14: 1.0, 15: 1.0, 16: 1.1,
        # Tarde rush
        17: 1.35, 18: 1.4, 19: 1.3, 20: 1.15, 21: 1.05,
        # Noche
        22: 0.95, 23: 0.9,
    }
    
    INCIDENT_SEVERITY_FACTORS = {
        "low": 1.05,
        "medium": 1.15,
        "high": 1.3,
        "critical": 1.5,
    }
    
    @classmethod
    async def load_model(cls):
        """Cargar modelo guardado desde MongoDB"""
        try:
            db = get_database()
            model_doc = await db.models.find_one({"name": "route_predictor"})
            
            if model_doc:
                # Cargar modelo desde binario
                model_buffer = io.BytesIO(model_doc["model"])
                cls.model = joblib.load(model_buffer)
                
                # Cargar encoders si existen
                if "encoders" in model_doc and model_doc["encoders"]:
                    encoder_buffer = io.BytesIO(model_doc["encoders"])
                    cls.weather_encoder = joblib.load(encoder_buffer)
                
                cls.is_trained = True
                print("✅ Modelo ML cargado desde MongoDB correctamente")
            else:
                # Fallback: intentar cargar archivo local (para desarrollo)
                if os.path.exists(MODEL_PATH):
                    cls.model = joblib.load(MODEL_PATH)
                    cls.weather_encoder = joblib.load(ENCODERS_PATH)
                    cls.is_trained = True
                    print("✅ Modelo ML cargado desde archivo local")
                else:
                    print("⚠️ No hay modelo entrenado en DB ni local. Usando heurísticas.")
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
    
    @classmethod
    async def train_model(cls, trips: List[dict]) -> dict:
        """Entrenar modelo con datos de viajes históricos"""
        if len(trips) < 10:
            return {
                "success": False,
                "message": f"Se necesitan al menos 10 viajes para entrenar. Tienes {len(trips)}.",
                "trips_count": len(trips)
            }
        
        try:
            # Preparar datos
            df = pd.DataFrame(trips)
            
            # Features
            features = [
                'distance', 'estimated_duration', 'hour', 'day_of_week',
                'is_weekend', 'is_holiday', 'had_incidents'
            ]
            
            # Encodear clima si existe
            if 'weather_condition' in df.columns and df['weather_condition'].notna().any():
                cls.weather_encoder = LabelEncoder()
                df['weather_encoded'] = cls.weather_encoder.fit_transform(
                    df['weather_condition'].fillna('clear')
                )
                features.append('weather_encoded')
            
            # Agregar temperatura si existe
            if 'temperature' in df.columns:
                df['temperature'] = df['temperature'].fillna(25.0)
                features.append('temperature')
            
            X = df[features].values
            
            # Target: ratio real vs estimado (qué tanto se desvía)
            y = df['actual_duration'].values / df['estimated_duration'].values
            
            # Entrenar modelo
            cls.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            cls.model.fit(X, y)
            cls.is_trained = True
            
            # Guardar en MongoDB para persistencia en la nube
            db = get_database()
            model_buffer = io.BytesIO()
            joblib.dump(cls.model, model_buffer)
            
            encoder_buffer = io.BytesIO()
            if cls.weather_encoder:
                joblib.dump(cls.weather_encoder, encoder_buffer)
            
            await db.models.update_one(
                {"name": "route_predictor"},
                {
                    "$set": {
                        "model": model_buffer.getvalue(),
                        "encoders": encoder_buffer.getvalue() if cls.weather_encoder else None,
                        "updated_at": datetime.now()
                    }
                },
                upsert=True
            )
            
            # Guardar copia local por si acaso
            os.makedirs(MODEL_DIR, exist_ok=True)
            joblib.dump(cls.model, MODEL_PATH)
            if cls.weather_encoder:
                joblib.dump(cls.weather_encoder, ENCODERS_PATH)
            
            # Calcular métricas
            predictions = cls.model.predict(X)
            mae = np.mean(np.abs(predictions - y))
            
            return {
                "success": True,
                "message": "Modelo entrenado exitosamente",
                "trips_count": len(trips),
                "mae": float(mae),
                "feature_importance": dict(zip(
                    features,
                    [float(x) for x in cls.model.feature_importances_]
                ))
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error entrenando modelo: {str(e)}",
                "trips_count": len(trips)
            }
    
    @classmethod
    def predict(
        cls,
        base_duration: float,
        distance: float,
        weather_condition: str = "clear",
        temperature: float = 25.0,
        hour: Optional[int] = None,
        day_of_week: Optional[int] = None,
        is_holiday: bool = False,
        incident_count: int = 0,
        incident_severities: List[str] = []
    ) -> PredictionResult:
        """Predecir tiempo de viaje ajustado"""
        
        now = datetime.now()
        if hour is None:
            hour = now.hour
        if day_of_week is None:
            day_of_week = now.weekday()
        
        is_weekend = day_of_week >= 5
        factors_applied = {}
        
        if cls.is_trained and cls.model is not None:
            # Usar modelo ML
            try:
                features = [
                    distance,
                    base_duration,
                    hour,
                    day_of_week,
                    int(is_weekend),
                    int(is_holiday),
                    int(incident_count > 0)
                ]
                
                if cls.weather_encoder:
                    try:
                        weather_encoded = cls.weather_encoder.transform([weather_condition])[0]
                    except:
                        weather_encoded = 0
                    features.append(weather_encoded)
                
                features.append(temperature)
                
                adjustment_factor = float(cls.model.predict([features])[0])
                confidence = 0.8  # Confianza del modelo
                factors_applied["ml_model"] = adjustment_factor
                
            except Exception as e:
                print(f"Error en predicción ML: {e}")
                adjustment_factor, confidence, factors_applied = cls._heuristic_prediction(
                    hour, weather_condition, is_weekend, is_holiday,
                    incident_count, incident_severities
                )
        else:
            # Usar heurísticas
            adjustment_factor, confidence, factors_applied = cls._heuristic_prediction(
                hour, weather_condition, is_weekend, is_holiday,
                incident_count, incident_severities
            )
        
        predicted_duration = base_duration * adjustment_factor
        
        return PredictionResult(
            predicted_duration=predicted_duration,
            base_duration=base_duration,
            adjustment_factor=adjustment_factor,
            confidence=confidence,
            factors_applied=factors_applied
        )
    
    @classmethod
    def _heuristic_prediction(
        cls,
        hour: int,
        weather_condition: str,
        is_weekend: bool,
        is_holiday: bool,
        incident_count: int,
        incident_severities: List[str]
    ) -> Tuple[float, float, dict]:
        """Predicción basada en heurísticas cuando no hay modelo"""
        
        factors = {}
        total_factor = 1.0
        
        # Factor por hora
        hour_factor = cls.HOUR_FACTORS.get(hour, 1.0)
        if is_weekend:
            hour_factor = 1.0 + (hour_factor - 1.0) * 0.5  # Reducir efecto en fin de semana
        if is_holiday:
            hour_factor = 0.9  # Menos tráfico en festivos
        factors["hour"] = hour_factor
        total_factor *= hour_factor
        
        # Factor por clima
        try:
            weather_enum = WeatherCondition(weather_condition)
            weather_factor = cls.WEATHER_FACTORS.get(weather_enum, 1.0)
        except:
            weather_factor = 1.0
        factors["weather"] = weather_factor
        total_factor *= weather_factor
        
        # Factor por incidencias
        if incident_count > 0:
            incident_factor = 1.0
            for severity in incident_severities:
                incident_factor *= cls.INCIDENT_SEVERITY_FACTORS.get(severity, 1.05)
            incident_factor = min(incident_factor, 2.0)  # Limitar a 2x
            factors["incidents"] = incident_factor
            total_factor *= incident_factor
        
        return total_factor, 0.5, factors  # 0.5 confianza para heurísticas
