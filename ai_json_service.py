import os
import json
from dotenv import load_dotenv
from gigachat import GigaChat

# Импортируем нашу схему данных
from schemas import BusinessIdeaSchema

load_dotenv()

class AIJsonService:
    def __init__(self, model_version: str = "GigaChat-3-Ultra"):
        self.model = model_version
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not self.credentials:
            raise ValueError("Ошибка: Токен GIGACHAT_CREDENTIALS не найден в .env!")

    def generate_structured_idea(self, industry_topic: str) -> dict:
        print(f"\n[AI-Бэкенд] Генерируем структурированную идею для индустрии: {industry_topic}...")
        
        # Жестко прописываем ключи, которые ИИ ОБЯЗАН использовать
        system_prompt = """
        Ты — опытный бизнес-аналитик. Ты должен придумать бизнес-идею и вернуть её СТРОГО в формате JSON.
        
        Ты ОБЯЗАН использовать только следующие ключи в JSON:
        - title (строка: название)
        - concept (строка: подробное описание сути бизнеса)
        - target_audience (строка: описание целевой аудитории)
        - start_capital_rub (целое число: стартовый капитал в рублях)
        - monetization (строка: как бизнес зарабатывает)
        - steps (список строк: 3-4 шага для запуска)

        Пример структуры ответа:
        {
            "title": "Название",
            "concept": "Описание",
            "target_audience": "Клиенты",
            "start_capital_rub": 500000,
            "monetization": "Подписка",
            "steps": ["Шаг 1", "Шаг 2"]
        }

        Никакого другого текста, кроме чистого JSON, не пиши! Не используй ключи вроде 'startup_name'.
        """

        try:
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat({
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Придумай стартап в сфере: {industry_topic}"}
                    ],
                    "temperature": 0.5 # Снизили температуру, чтобы ИИ меньше фантазировал с форматами
                })
                
                raw_text = response.choices[0].message.content.strip()
                
                # Очистка маркдауна
                if raw_text.startswith("```json"):
                    raw_text = raw_text.replace("```json", "", 1)
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("```", 1)[0]
                raw_text = raw_text.strip()

                # Валидация
                validated_data = BusinessIdeaSchema.model_validate_json(raw_text)
                return validated_data.model_dump()

        except Exception as e:
            # Если ИИ все же ошибся, бэкенд не должен падать. Выводим сырой текст для отладки
            return {"error": "Ошибка валидации структуры", "details": str(e), "raw_text": locals().get('raw_text', 'Нет данных')}

# --- ТЕСТ СЕРВИСА ---
if __name__ == "__main__":
    service = AIJsonService()
    # Тестируем генерацию идеи для сферы общепита (ресторанного бизнеса)
    result = service.generate_structured_idea("Ресторанный бизнес и доставка еды")
    
    print("\n====== РЕЗУЛЬТАТ СТРУКТУРИРОВАННОГО ВЫВОДА (JSON) ======")
    print(json.dumps(result, ensure_ascii=False, indent=4))
