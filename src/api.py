import pickle
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from logger import Logger

SHOW_LOG = True

# Настройка логгера
logger = Logger(SHOW_LOG).get_logger(__name__)

# Загружаем модель
model_path = os.path.join(os.getcwd(), "models", "model.pkl")
try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Модель загружена из {model_path}")
except FileNotFoundError:
    logger.error(f"Модель не найдена по пути {model_path}")
    model = None

# Создаём приложение FastAPI
app = FastAPI(
    title="ImageNet Classifier API",
    description="API для классификации изображений (модель RandomForest)",
    version="1.0.0"
)


# Описываем формат входных данных
class ImageRequest(BaseModel):
    """Формат запроса для предсказания"""
    pixels: List[float]  # список из 2352 чисел (28x28x3)


class ImageResponse(BaseModel):
    """Формат ответа"""
    prediction: int
    class_name: str
    confidence: float  # уверенность модели (не точная, примерная)


# Словарь для преобразования ID класса в название (если знаешь названия)
CLASS_NAMES = {
    0: "class_0",
    1: "class_1",
}


@app.get("/")
def root():
    """Проверка, что API работает"""
    return {
        "message": "ImageNet Classifier API is running",
        "status": "healthy",
        "model_loaded": model is not None
    }


@app.get("/health")
def health():
    """Health check для Docker"""
    return {"status": "ok"}


@app.post("/predict", response_model=ImageResponse)
def predict(request: ImageRequest):
    """Предсказание класса изображения"""
    if model is None:
        raise HTTPException(status_code=500, detail="Модель не загружена")
    
    # Проверяем размер входных данных
    if len(request.pixels) != 2352:
        raise HTTPException(
            status_code=400,
            detail=f"Ожидается 2352 пикселей, получено {len(request.pixels)}"
        )
    
    try:
        # Преобразуем в numpy массив и делаем предсказание
        input_array = np.array([request.pixels])
        prediction = model.predict(input_array)[0]
        
        # Получаем вероятности (для RandomForest есть predict_proba)
        try:
            probabilities = model.predict_proba(input_array)[0]
            confidence = float(max(probabilities))
        except:
            confidence = 0.5  # если нет predict_proba
        
        # Получаем название класса
        class_name = CLASS_NAMES.get(prediction, f"class_{prediction}")
        
        logger.info(f"Предсказание: класс {prediction} ({class_name}), уверенность: {confidence:.3f}")
        
        return ImageResponse(
            prediction=int(prediction),
            class_name=class_name,
            confidence=confidence
        )
    
    except Exception as e:
        logger.error(f"Ошибка при предсказании: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
def info():
    """Информация о модели"""
    return {
        "model_type": "RandomForestClassifier",
        "input_shape": 2352,
        "num_classes": 2,
        "classes": CLASS_NAMES
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)