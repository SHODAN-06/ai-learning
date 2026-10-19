import os
import json  # Библиотека для работы с JSON-файлами
from dotenv import load_dotenv
from gigachat import GigaChat

load_dotenv()

class AIAssistant:
    def __init__(self, name: str, model_version: str = "GigaChat-3-Ultra", filename: str = "history.json"):
        self.name = name
        self.model = model_version
        self.filename = filename  # Имя файла для сохранения логов
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        
        if not self.credentials:
            raise ValueError("Ошибка: Токен GIGACHAT_CREDENTIALS не найден в файле .env!")
        
        # ЗАГРУЗКА ИЗ ФАЙЛА: При старте пытаемся прочитать старую историю
        self.history = self.load_history_from_file()

    def load_history_from_file(self):
        """Метод для загрузки истории из JSON-файла при запуске программы"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except Exception as e:
                print(f"[Система] Ошибка чтения файла истории: {e}. Создаем новую историю.")
                return []
        return []

    def save_history_to_file(self):
        """Метод для сохранения всей истории в файл JSON"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                # ensure_ascii=False сохраняет русский текст читаемым, а не в виде кодов \u0430
                json.dump(self.history, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Система] Не удалось сохранить историю в файл: {e}")

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
                        "temperature": 0.8
                    }
                )
                ai_response = response.choices[0].message.content
            
            # Добавляем запись в память
            self.history.append({"query": user_query, "response": ai_response})
            
            # ЗАПИСЬ НА ДИСК: Сразу сохраняем обновленный список в файл
            self.save_history_to_file()
            
            return ai_response

        except ValueError as error:
            return f"Ошибка валидации: {error}"
        except Exception as e:
            return f"Произошла ошибка при обращении к API ИИ: {e}"

    def show_history(self):
        print(f"\n--- История запросов (Всего записей: {len(self.history)}) ---")
        if not self.history:
            print("История пуста.")
        for index, item in enumerate(self.history, 1):
            short_resp = item['response'][:60].replace('\n', ' ') + "..."
            print(f"{index}. Вопрос: {item['query']} | Ответ: {short_resp}")


if __name__ == "__main__":
    my_bot = AIAssistant(name="GigaAssistant")
    
    print("=== Интерактивный ИИ-Ассистент с логированием в файл запущен! ===")
    print("Вы можете писать ему любые вопросы. Для выхода введите слово: выход")
    
    while True:
        user_text = input("\nВаш запрос к ИИ -> ")
        
        if user_text.strip().lower() == "выход":
            print("\nДо встречи! Программа завершена.")
            break
            
        response = my_bot.send_request(user_text)
        print(f"\n[Ответ ИИ]:\n{response}")
        
        my_bot.show_history()
