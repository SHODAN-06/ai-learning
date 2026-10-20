import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from ai_json_service import AIJsonService
# Импортируем инструменты нашей базы данных
from database import engine, Base, BusinessIdeaModel, get_db

# Автоматически создаем таблицы в базе данных при запуске
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Startup Generator API + SQL Database",
    description="Коммерческий бэкенд с постоянным хранением данных в SQL",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_service = AIJsonService()

@app.get("/")
def read_root():
    return {"status": "online", "database": "connected"}

# ОБНОВЛЕННЫЙ ЭНДПОИНТ ГЕНЕРАЦИИ (Теперь с сохранением в БД)
@app.get("/api/v1/generate-idea")
def get_business_idea(topic: str, db: Session = Depends(get_db)):
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Параметр 'topic' не может быть пустым")
    
    # 1. Генерируем структурированный JSON через ИИ Сбера
    result = ai_service.generate_structured_idea(topic)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result)
        
    # 2. Переводим список шагов в одну строку, чтобы сохранить в SQLite (так как SQLite не умеет хранить списки напрямую)
    steps_str = "||".join(result["steps"])
    
    # 3. Создаем объект записи для нашей SQL-таблицы
    db_idea = BusinessIdeaModel(
        topic=topic,
        title=result["title"],
        concept=result["concept"],
        target_audience=result["target_audience"],
        start_capital_rub=result["start_capital_rub"],
        monetization=result["monetization"],
        steps=steps_str
    )
    
    # 4. Сохраняем запись в базу данных
    db.add(db_idea)
    db.commit()
    db.refresh(db_idea) # Обновляем объект, чтобы получить его новый ID из базы
    
    print(f"[База Данных] Идея '{result['title']}' успешно сохранена в SQL под ID: {db_idea.id}")
    
    return result

# 🔥 НОВЫЙ ЭНДПОИНТ: Выгрузка всей истории из базы данных
@app.get("/api/v1/history")
def get_all_saved_ideas(db: Session = Depends(get_db)):
    """Возвращает список всех когда-либо сгенерированных идей из базы данных"""
    ideas = db.query(BusinessIdeaModel).all()
    
    formatted_history = []
    for idea in ideas:
        # Превращаем строку шагов обратно в красивый список Python
        steps_list = idea.steps.split("||") if idea.steps else []
        
        formatted_history.append({
            "id": idea.id,
            "topic": idea.topic,
            "title": idea.title,
            "concept": idea.concept,
            "target_audience": idea.target_audience,
            "start_capital_rub": idea.start_capital_rub,
            "monetization": idea.monetization,
            "steps": steps_list
        })
        
    return {"total_records": len(formatted_history), "history": formatted_history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
