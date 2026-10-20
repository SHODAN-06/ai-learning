from pydantic import BaseModel, Field
from typing import List

# Описываем структуру, которую ИИ ОБЯЗАН будет вернуть
class BusinessIdeaSchema(BaseModel):
    title: str = Field(description="Краткое, броское название бизнес-идеи на русском языке")
    concept: str = Field(description="Подробное описание сути концепции бизнеса")
    target_audience: str = Field(description="Целевая аудитория этого бизнеса в Москве")
    start_capital_rub: int = Field(description="Ориентировочный стартовый капитал в рублях (только число)")
    monetization: str = Field(description="Как именно бизнес будет зарабатывать деньги")
    steps: List[str] = Field(description="Список из 3-4 последовательных шагов для запуска этого бизнеса")
