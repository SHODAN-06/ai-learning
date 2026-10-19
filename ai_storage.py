import json
import os
import time

class AdvancedAssistant:
    def __init__(self, name: str):
        self.name = name
        self.file_name = "history.json"
        # Загружаем старую историю из файла при старте, если файл существует
        self.history = self.load_history_from_file()

    # Меток для загрузки данных из файла
    def load_history_from_file(self):
        if os.path.exists(self.file_name):
            with open(self.file_name, "r", encoding="utf-8") as file:
                # json.load превращает текст из файла обратно в список словарей Python
                return json.load(file)
        return [] # Если файла нет, возвращаем пустой список

    def send_request(self, user_query: str):
        print(f"\n[{self.name}] имитирует запрос к API...")
        time.sleep(0.5)

        # Имитируем реальный сложный ответ от ИИ-сервера (это СЛОВАРЬ)
        raw_api_response = {
            "status": "success",
            "meta_data": {
                "model_name": "GigaChat Pro-2026",
                "tokens_used": 142
            },
            "choices": [
                {
                    "message": f"Ответ на тему '{user_query}' успешно сгенерирован."
                }
            ]
        }

        # Ваша задача: вытащить данные из сложной структуры словаря
        ai_text = raw_api_response["choices"][0]["message"]
        tokens = raw_api_response["meta_data"]["tokens_used"]

        # Добавляем в историю
        self.history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": user_query,
            "response": ai_text,
            "tokens": tokens
        })

        # Сохраняем обновленную историю в файл
        self.save_history_to_file()
        return ai_text

    # Метод для сохранения в файл
    def save_history_to_file(self):
        with open(self.file_name, "w", encoding="utf-8") as file:
            # json.dump записывает список словарей в файл в красивом читаемом виде (indent=4)
            json.dump(self.history, file, ensure_ascii=False, indent=4)
        print("История успешно сохранена в файл history.json!")

# --- ПРОВЕРКА ---
if __name__ == "__main__":
    bot = AdvancedAssistant("AI-Broker")
    
    # Сделайте тест: запустите программу несколько раз с разными вопросами!
    user_input = input("Введите ваш вопрос для ИИ: ")
    answer = bot.send_request(user_input)
    print(f"ИИ ответил: {answer}")
