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
        
        # Список сообщений для удержания контекста диалога
        self.context_memory = []
        
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not self.credentials:
            raise ValueError("Ошибка: Токен GIGACHAT_CREDENTIALS не найден в файле .env!")

    def clear_session_memory(self):
        """Метод для очистки памяти текущего диалога"""
        self.context_memory = []
        print("[Система] Память текущей сессии успешно очищена.")

    def analyze_query(self, user_query: str):
        """Фоновый метод анализа категории и тональности"""
        try:
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                instruction = """
                Проанализируй текст пользователя. Определи категорию вопроса (выбери ОДНО из: Финансы, ИТ-разработка, Бизнес-идея, Юмор, Бытовой вопрос) 
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
                
                # ТУТ ИСПРАВЛЕНО (Добавлен индекс [0]):
                result = response.choices[0].message.content.strip()
                
                parts = result.split("|")
                cat = parts[0].strip() if len(parts) > 0 else "Общее"
                sent = parts[1].strip() if len(parts) > 1 else "Нейтральный"
                return cat, sent
        except Exception as e:
            print(f"[Система] Ошибка фонового анализа: {e}")
            return "Общее", "Нейтральный"

    def send_request(self, user_query: str):
        print(f"\n[{self.name}] отправляет запрос в реальную нейросеть {self.model} с учетом контекста...")
        try:
            if not user_query.strip():
                raise ValueError("Запрос не может быть пустым!")
            
            # 1. Фоновый анализ
            category, sentiment = self.analyze_query(user_query)
            
            # 2. Добавляем текущий вопрос пользователя в оперативную память контекста
            self.context_memory.append({"role": "user", "content": user_query})
            
            # Ограничиваем память последними 10 репликами, чтобы не тратить лишние токены
            if len(self.context_memory) > 10:
                self.context_memory = self.context_memory[-10:]
            
            # 3. Отправляем ВСЮ историю беседы на сервер Сбера
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat({
                    "model": self.model,
                    "messages": self.context_memory,
                    "temperature": 0.7
                })
                
                # ТУТ ТОЖЕ ИСПРАВЛЕНО (Добавлен индекс [0]):
                ai_response = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
            
            # 4. Добавляем ответ ИИ в память контекста
            self.context_memory.append({"role": "assistant", "content": ai_response})
            
            # 5. Сохраняем в постоянные логи на жесткий диск
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
            # Если произошла ошибка, удаляем последний вопрос из памяти, чтобы не ломать цепочку
            if self.context_memory and self.context_memory[-1]["role"] == "user":
                self.context_memory.pop()
            return f"Произошла ошибка при обращении к API ИИ: {e}"
