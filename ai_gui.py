import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

# Импортируем нашего живого ассистента из первого файла
from ai_assistant import AIAssistant

class AIAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GigaAssistant — Интерфейс управления ИИ")
        self.root.geometry("650x550")
        self.root.configure(background="#f5f7fb")

        # Инициализируем нашего ИИ-бота (он сам подтянет ключи и хранилище)
        try:
            self.bot = AIAssistant(name="GigaAssistant")
        except Exception as e:
            messagebox.showerror("Ошибка инициализации", f"Не удалось запустить ИИ: {e}")
            self.root.destroy()
            return

        # --- СОЗДАНИЕ ЭЛЕМЕНТОВ ИНТЕРФЕЙСА (ВИДЖЕТОВ) ---
        
        # 1. Заголовок
        self.title_label = tk.Label(
            root, text="🤖 Персональный AI-Ассистент", 
            font=("Segoe UI", 16, "bold"), fg="#1e3a8a", bg="#f5f7fb"
        )
        self.title_label.pack(pady=10)

        # 2. Поле ввода вопроса
        self.input_label = tk.Label(root, text="Введите ваш запрос:", font=("Segoe UI", 10), bg="#f5f7fb")
        self.input_label.pack(anchor="w", padx=20)
        
        self.entry_query = tk.Entry(root, font=("Segoe UI", 11), width=65)
        self.entry_query.pack(pady=5, padx=20)
        # Позволяет отправлять запрос по нажатию клавиши Enter
        self.entry_query.bind("<Return>", lambda event: self.start_request_thread())

        # 3. Кнопка отправки
        self.btn_send = tk.Button(
            root, text="Отправить запрос в ИИ", font=("Segoe UI", 10, "bold"),
            bg="#2563eb", fg="white", activebackground="#1d4ed8", activeforeground="white",
            width=25, command=self.start_request_thread
        )
        self.btn_send.pack(pady=10)

        # 4. Большое поле для вывода ответа ИИ
        self.output_label = tk.Label(root, text="Ответ искусственного интеллекта:", font=("Segoe UI", 10), bg="#f5f7fb")
        self.output_label.pack(anchor="w", padx=20)

        self.txt_response = scrolledtext.ScrolledText(
            root, width=70, height=15, font=("Segoe UI", 10), 
            wrap=tk.WORD, bg="white", bd=1, relief="solid"
        )
        self.txt_response.pack(pady=5, padx=20)

        # 5. Статусная строка снизу (Счетчик денег и токенов)
        self.status_label = tk.Label(
            root, text="Система готова к работе | Запросов в сессии: 0", 
            font=("Segoe UI", 9, "italic"), fg="#555", bg="#f5f7fb"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def start_request_thread(self):
        """Запуск запроса в отдельном потоке, чтобы окно программы не зависало во время ответа ИИ"""
        user_query = self.entry_query.get().strip()
        if not user_query:
            messagebox.showwarning("Внимание", "Запрос не может быть пустым!")
            return

        # Блокируем кнопку на время запроса, чтобы пользователь не спамил кликами
        self.btn_send.config(state=tk.DISABLED, text="ИИ думает...")
        self.txt_response.delete("1.0", tk.END)
        self.txt_response.insert(tk.END, "Отправка запроса на сервер Сбера, пожалуйста, подождите...\n")

        # Запуск многопоточности (Threading) — это стандарт для GUI-приложений
        thread = threading.Thread(target=self.process_ai_request, args=(user_query,))
        thread.start()

    def process_ai_request(self, query):
        """Метод выполняется в фоне: берет ответ от ИИ и обновляет окно"""
        # Делаем реальный запрос через наш старый класс AIAssistant
        response = self.bot.send_request(query)

        # Очищаем поле вывода и вставляем свежий ответ от ИИ
        self.txt_response.delete("1.0", tk.END)
        self.txt_response.insert(tk.END, response)

        # Очищаем поле ввода для следующего вопроса
        self.entry_query.delete(0, tk.END)

        # Обновляем статусную строчку (берем последние данные из нашего файла ai_storage)
        if self.bot.storage.history:
            last_log = self.bot.storage.history[-1]
            total_queries = len(self.bot.storage.history)
            cost = last_log.get('cost_rub', 0.0)
            tokens = last_log.get('tokens_used', 0)
            
            status_text = f"Всего запросов: {total_queries} | Последний запрос: {tokens} токенов ({cost} ₽)"
            self.status_label.config(text=status_text)

        # Возвращаем кнопку в рабочее состояние
        self.btn_send.config(state=tk.NORMAL, text="Отправить запрос в ИИ")


# --- БЛОК ЗАПУСКА ОКНА ---
if __name__ == "__main__":
    window = tk.Tk()
    app = AIAppGUI(window)
    window.mainloop() # Запуск бесконечного цикла отрисовки окна Windows
