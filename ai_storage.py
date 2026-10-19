import json
import os
import time

class AIStorage:
    def __init__(self, filename: str = "history.json", html_filename: str = "history.html"):
        self.filename = filename
        self.html_filename = html_filename
        self.history = self.load_history_from_file()

    def load_history_from_file(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as file:
                    return json.load(file)
            except Exception as e:
                print(f"[Хранилище] Ошибка чтения файла истории: {e}")
                return []
        return []

    def save_log(self, user_query: str, ai_response: str, tokens_used: int, model_name: str, category: str = "Общее", sentiment: str = "Нейтральный"):
        price_per_token = 1.2 / 1000
        cost_rub = round(tokens_used * price_per_token, 4)

        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_name": model_name,
            "query": user_query,
            "response": ai_response,
            "tokens_used": tokens_used,
            "cost_rub": cost_rub,
            "category": category,      # Новое поле
            "sentiment": sentiment     # Новое поле
        }
        
        self.history.append(log_entry)
        
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self.history, file, ensure_ascii=False, indent=4)
            print(f"[Хранилище] Запись сохранена! Категория: {category} | Тональность: {sentiment}")
            
            self.generate_html_report()
            
        except Exception as e:
            print(f"[Хранилище] Ошибка при сохранении файла: {e}")

    def generate_html_report(self):
        html_content = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>История запросов ИИ Ассистента</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background-color: #f5f7fb; color: #333; }
                h2 { color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                th, td { padding: 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }
                th { background-color: #2563eb; color: white; font-weight: 600; }
                tr:hover { background-color: #f8fafc; }
                .badge { background-color: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
                .tag-cat { background-color: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }
                .tag-sent { background-color: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }
                .cost { color: #16a34a; font-weight: bold; }
                pre { white-space: pre-wrap; font-family: inherit; margin: 0; }
            </style>
        </head>
        <body>
            <h2>📊 Расширенная панель аналитики логов ИИ</h2>
            <table>
                <tr>
                    <th>Время</th>
                    <th>Модель</th>
                    <th>Категория</th>
                    <th>Тональность</th>
                    <th>Ваш запрос</th>
                    <th>Ответ ИИ</th>
                    <th>Токены</th>
                    <th>Стоимость</th>
                </tr>
        """
        
        for item in self.history:
            cost = item.get('cost_rub', 0.0)
            html_content += f"""
                <tr>
                    <td>{item.get('timestamp', '---')}</td>
                    <td><span class="badge">{item.get('model_name', 'GigaChat')}</span></td>
                    <td><span class="tag-cat">{item.get('category', 'Общее')}</span></td>
                    <td><span class="tag-sent">{item.get('sentiment', 'Нейтральный')}</span></td>
                    <td><b>{item.get('query', '---')}</b></td>
                    <td><pre>{item.get('response', '---')}</pre></td>
                    <td>{item.get('tokens_used', 0)}</td>
                    <td><span class="cost">{cost} ₽</span></td>
                </tr>
            """
            
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(self.html_filename, "w", encoding="utf-8") as file:
            file.write(html_content)

    def show_history(self):
        print(f"\n--- История запросов (Всего записей: {len(self.history)}) ---")
        if not self.history:
            print("История пуста.")
        for index, item in enumerate(self.history, 1):
            short_resp = item['response'][:40].replace('\n', ' ') + "..."
            print(f"{index}. [{item.get('timestamp', 'Ранее')}] Отвечено.")
