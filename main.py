import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ai_json_service import AIJsonService
from database import engine, Base, BusinessIdeaModel, get_db

# Автоматически создаем таблицы в базе данных при запуске
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Startup Generator API + SQL Memory",
    description="Коммерческий Fullstack веб-сервер с контекстной памятью на базе SQL",
    version="1.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_service = AIJsonService()

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Раздает ваш красивый фронтенд-сайт"""
    try:
        with open("index.html", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "<h3>[Ошибка] Файл index.html не найден в корне папки проекта!</h3>"

@app.get("/api/v1/generate-idea")
def get_business_idea(topic: str, db: Session = Depends(get_db)):
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Параметр 'topic' не может быть пустым")
    
    # 1. Извлекаем из SQL последние 3 сохраненные идеи для формирования контекста ИИ
    ideas = db.query(BusinessIdeaModel).order_by(BusinessIdeaModel.id.desc()).limit(3).all()
    
    history_context = []
    # Разворачиваем список, чтобы хронология шла от старых к новым
    for idea in reversed(ideas):
        steps_list = idea.steps.split("||") if idea.steps else []
        history_context.append({
            "topic": idea.topic,
            "title": idea.title,
            "concept": idea.concept,
            "target_audience": idea.target_audience,
            "start_capital_rub": idea.start_capital_rub,
            "monetization": idea.monetization,
            "steps": steps_list
        })
        
    # 2. Генерируем новый ответ, передавая ИИ прошлую историю из базы данных
    result = ai_service.generate_structured_idea(topic, history_context=history_context)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result)
        
    # 3. Сохраняем свежую сгенерированную идею обратно в SQL-базу данных
    steps_str = "||".join(result["steps"])
    db_idea = BusinessIdeaModel(
        topic=topic,
        title=result["title"],
        concept=result["concept"],
        target_audience=result["target_audience"],
        start_capital_rub=result["start_capital_rub"],
        monetization=result["monetization"],
        steps=steps_str
    )
    
    db.add(db_idea)
    db.commit()
    db.refresh(db_idea)
    
    print(f"[База Данных] Новая идея успешно сохранена в SQL под ID: {db_idea.id}")
    return result

@app.get("/api/v1/history")
def get_all_saved_ideas(db: Session = Depends(get_db)):
    ideas = db.query(BusinessIdeaModel).all()
    formatted_history = []
    for idea in ideas:
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
    # 0.0.0.0 говорит серверу: "принимай запросы со всех устройств в локальной сети"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

