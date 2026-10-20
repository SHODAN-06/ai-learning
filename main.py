from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Импортируем наш ИИ-сервис структурированного вывода
from ai_json_service import AIJsonService

# Создаем приложение веб-сервера
app = FastAPI(
    title="AI Startup Generator API",
    description="Мощный бэкенд-сервис для генерации бизнес-идей на базе ИИ",
    version="1.0.0"
)

# Разрешаем запросы к нашему бэкенду с любых сайтов (настройка CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализируем наш ИИ-сервис
ai_service = AIJsonService()

# Описываем корневую страницу веб-сервера
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Бэкенд генератора стартапов успешно запущен. Перейдите на /docs для тестирования."
    }

# Создаем боевой веб-адрес (эндпоинт) для генерации бизнес-идей
@app.get("/api/v1/generate-idea")
def get_business_idea(topic: str):
    """
    Принимает query-параметр ?topic=...
    Возвращает готовый структурированный JSON от ИИ Сбера
    """
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Параметр 'topic' не может быть пустым")
    
    # Запускаем наш ИИ-бэкенд
    result = ai_service.generate_structured_idea(topic)
    
    # Если в процессе сборки произошла ошибка, возвращаем 500-й статус сервера
    if "error" in result:
        raise HTTPException(status_code=500, detail=result)
        
    return result

# Код для локального запуска внутри Python (удобно для дебага)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
