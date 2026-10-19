import json
import os
import time

class AIStorage:
    def __init__(self, filename: str = "history.json"):
        self.filename = filename
        # Загружаем старую историю при старте, если файл существует
        self.history = self.load_history_from_file()

    def load_history_from_file(self):
        """Загрузка истории из файла JSON"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as file:
                    return json.load(file)
            except Exception as e:
                print(f"[Хранилище] Ошибка чтения файла истории: {e}")
                return []
        return []

    def save_log(self, user_query: str, ai_response: str, tokens_used: int, model_name: str):
        """Метод для добавления новой записи и сохранения её на жесткий диск"""
        # Структурируем лог как в вашем исходном коде
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_name": model_name,
            "query": user_query,
            "response": ai_response,
            "tokens_used": tokens_used
        }
        
        # Добавляем в список памяти
        self.history.append(log_entry)
        
        # Записываем обновленный список в файл
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self.history, file, ensure_ascii=False, indent=4)
            print("[Хранилище] Запись успешно сохранена в файл history.json!")
        except Exception as e:
            print(f"[Хранилище] Ошибка при сохранении файла: {e}")

    def show_history(self):
        """Вывод истории в консоль"""
        print(f"\n--- История запросов (Всего записей: {len(self.history)}) ---")
        if not self.history:
            print("История пуста.")
        for index, item in enumerate(self.history, 1):
            short_resp = item['response'][:50].replace('\n', ' ') + "..."
            print(f"{index}. [{item['timestamp']}] Вопрос: {item['query']} | Токены: {item['tokens_used']} | Ответ: {short_resp}")
