import os
from dotenv import load_dotenv
from gigachat import GigaChat
from ai_storage import AIStorage

load_dotenv()

class AIAssistant:
    def __init__(self, name: str, model_version: str = "GigaChat-3-Ultra"):
        self.name = name
        self.model = model_version
        self.storage = AIStorage()
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not self.credentials:
            raise ValueError("Ошибка: Токен GIGACHAT_CREDENTIALS не найден в файле .env!")

    def analyze_query(self, user_query: str):
        """Служебный скрытый метод: ИИ анализирует категорию и тональность вопроса"""
        try:
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                instruction = """
                Проанализируй текст пользователя. Определи категорию вопроса (выбери ОДНО из: Биткойн/Финансы, ИТ-разработка, Бизнес-идея, Юмор, Бытовой вопрос) 
                и тональность текста (выбери ОДНО из: Позитивный, Нейтральный, Раздраженный).
                Ответь строго в формате: Категория | Тональность. Никаких других слов не пиши!
                """
                response = giga.chat({
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": instruction},
                        {"role": "user", "content": user_query}
                    ],
                    "temperature": 0.1
                })
                result = response.choices[0].message.content.strip()
                # Разделяем ответ по черте '|'
                parts = result.split("|")
                cat = parts[0].strip() if len(parts) > 0 else "Общее"
                sent = parts[1].strip() if len(parts) > 1 else "Нейтральный"
                return cat, sent
        except Exception:
            return "Общее", "Нейтральный"

    def send_request(self, user_query: str):
        print(f"\n[{self.name}] отправляет запрос в реальную нейросеть {self.model}...")
        try:
            if not user_query.strip():
                raise ValueError("Запрос не может быть пустым!")
            
            # Шаг 1: Фоновая аналитика вопроса
            category, sentiment = self.analyze_query(user_query)
            
            # Шаг 2: Основной запрос ответа
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat({
                    "model": self.model,
                    "messages": [{"role": "user", "content": user_query}],
                    "temperature": 0.7
                })
                ai_response = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
            
            # Сохраняем расширенные логи со служебными тегами
            self.storage.save_log(
                user_query=user_query, 
                ai_response=ai_response, 
                tokens_used=tokens_used, 
                model_name=self.model,
                category=category,
                sentiment=sentiment
            )
            
            return ai_response

        except ValueError as error:
            return f"Ошибка валидации: {error}"
        except Exception as e:
            return f"Произошла ошибка при обращении к API ИИ: {e}"

if __name__ == "__main__":
    # Для консольного теста
    my_bot = AIAssistant(name="GigaAssistant")
    my_bot.send_request("Придумай смешной анекдот про сисадмина")
