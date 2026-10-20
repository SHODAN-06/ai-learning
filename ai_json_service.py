import os
import json
from dotenv import load_dotenv
from gigachat import GigaChat
from schemas import BusinessIdeaSchema

load_dotenv()

class AIJsonService:
    def __init__(self, model_version: str = "GigaChat-3-Ultra"):
        self.model = model_version
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not self.credentials:
            raise ValueError("Ошибка: Токен GIGACHAT_CREDENTIALS не найден в .env!")

    def generate_structured_idea(self, industry_topic: str, history_context: list = None) -> dict:
        print(f"\n[AI-Бэкенд] Запрос темы: {industry_topic} с учетом SQL-памяти...")
        
        system_prompt = """
        Ты — опытный бизнес-аналитик. Ты должен придумать бизнес-идею для Москвы и вернуть её СТРОГО в формате JSON.
        Ты ОБЯЗАН использовать только следующие ключи:
        - title (название)
        - concept (описание сути бизнеса)
        - target_audience (целевая аудитория)
        - start_capital_rub (целое число стартового капитала)
        - monetization (как бизнес зарабатывает)
        - steps (список из 3-4 строк-шагов)

        Никакого другого текста, кроме чистого JSON, не пиши!
        """

        # Строим цепочку сообщений для ИИ Сбера
        messages = [{"role": "system", "content": system_prompt}]
        
        # Если в базе данных есть прошлая история, подмешиваем её в память ИИ
        if history_context:
            for item in history_context:
                messages.append({"role": "user", "content": f"Придумай стартап в сфере: {item['topic']}"})
                messages.append({"role": "assistant", "content": json.dumps(item, ensure_ascii=False)})
        
        # Добавляем текущий свежий вопрос пользователя
        messages.append({"role": "user", "content": f"Придумай стартап в сфере: {industry_topic}"})

        try:
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat({
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.5
                })
                
                raw_text = response.choices[0].message.content.strip()
                
                if raw_text.startswith("```json"):
                    raw_text = raw_text.replace("```json", "", 1)
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("```", 1)[0]
                raw_text = raw_text.strip()

                validated_data = BusinessIdeaSchema.model_validate_json(raw_text)
                return validated_data.model_dump()

        except Exception as e:
            return {"error": "Ошибка валидации структуры", "details": str(e)}
