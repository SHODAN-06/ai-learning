import os
from dotenv import load_dotenv
from gigachat import GigaChat

# ИМПОРТ: Подключаем наше новое модульное хранилище из соседнего файла!
from ai_storage import AIStorage

load_dotenv()

class AIAssistant:
    def __init__(self, name: str, model_version: str = "GigaChat-3-Ultra"):
        self.name = name
        self.model = model_version
        
        # Создаем объект хранилища внутри нашего ассистента
        self.storage = AIStorage()
        
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not self.credentials:
            raise ValueError("Ошибка: Токен GIGACHAT_CREDENTIALS не найден в файле .env!")

    def send_request(self, user_query: str):
        print(f"\n[{self.name}] отправляет запрос в реальную нейросеть {self.model}...")
        try:
            if not user_query.strip():
                raise ValueError("Запрос не может быть пустым!")
            
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat(
                    {
                        "model": self.model,
                        "messages": [{"role": "user", "content": user_query}],
                        "temperature": 0.7
                    }
                )
                
                # 1. Вытаскиваем реальный текст ответа
                ai_response = response.choices[0].message.content
                
                # 2. Вытаскиваем реальное количество потраченных токенов из ответа Сбера!
                tokens_used = response.usage.total_tokens
            
            # МОДУЛЬНОСТЬ: Передаем всю рутину сохранения в наш отдельный файл ai_storage.py
            self.storage.save_log(
                user_query=user_query, 
                ai_response=ai_response, 
                tokens_used=tokens_used, 
                model_name=self.model
            )
            
            return ai_response

        except ValueError as error:
            return f"Ошибка валидации: {error}"
        except Exception as e:
            return f"Произошла ошибка при обращении к API ИИ: {e}"


if __name__ == "__main__":
    my_bot = AIAssistant(name="GigaAssistant")
    
    print("=== Модульный ИИ-Ассистент запущен! ===")
    print("Вы можете писать ему любые вопросы. Для выхода введите слово: выход")
    
    while True:
        user_text = input("\nВаш запрос к ИИ -> ")
        
        if user_text.strip().lower() == "выход":
            print("\nДо встречи! Программа завершена.")
            break
            
        response = my_bot.send_request(user_text)
        print(f"\n[Ответ ИИ]:\n{response}")
        
        # Показываем историю, дергая метод из хранилища
        my_bot.storage.show_history()
