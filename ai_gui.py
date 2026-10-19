import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from ai_assistant import AIAssistant

class AIAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GigaAssistant — Диалоговая система с памятью")
        self.root.geometry("650x600")
        self.root.configure(background="#f5f7fb")

        try:
            self.bot = AIAssistant(name="GigaAssistant")
        except Exception as e:
            messagebox.showerror("Ошибка инициализации", f"Не удалось запустить ИИ: {e}")
            self.root.destroy()
            return

        # 1. Заголовок
        self.title_label = tk.Label(
            root, text="🤖 AI-Ассистент с контекстной памятью", 
            font=("Segoe UI", 15, "bold"), fg="#1e3a8a", bg="#f5f7fb"
        )
        self.title_label.pack(pady=10)

        # 2. Поле ввода вопроса
        self.input_label = tk.Label(root, text="Введите ваш запрос (ИИ помнит контекст общения):", font=("Segoe UI", 10), bg="#f5f7fb")
        self.input_label.pack(anchor="w", padx=20)
        
        self.entry_query = tk.Entry(root, font=("Segoe UI", 11), width=65)
        self.entry_query.pack(pady=5, padx=20)
        self.entry_query.bind("<Return>", lambda event: self.start_request_thread())

        # БЛОК КНОПОК: Разместим их в одну линию
        self.button_frame = tk.Frame(root, bg="#f5f7fb")
        self.button_frame.pack(pady=10)

        # 3. Кнопка отправки
        self.btn_send = tk.Button(
            self.button_frame, text="Отправить запрос", font=("Segoe UI", 10, "bold"),
            bg="#2563eb", fg="white", activebackground="#1d4ed8", activeforeground="white",
            width=22, command=self.start_request_thread
        )
        self.btn_send.pack(side=tk.LEFT, padx=5)

        # 4. ФИШКА: Кнопка сброса памяти сессии
        self.btn_clear = tk.Button(
            self.button_frame, text="🗑️ Сбросить контекст", font=("Segoe UI", 10),
            bg="#ef4444", fg="white", activebackground="#dc2626", activeforeground="white",
            width=22, command=self.clear_memory
        )
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        # 5. Поле вывода ответа ИИ
        self.output_label = tk.Label(root, text="История текущего диалога:", font=("Segoe UI", 10), bg="#f5f7fb")
        self.output_label.pack(anchor="w", padx=20)

        self.txt_response = scrolledtext.ScrolledText(
            root, width=70, height=18, font=("Segoe UI", 10), 
            wrap=tk.WORD, bg="white", bd=1, relief="solid"
        )
        self.txt_response.pack(pady=5, padx=20)

        # 6. Статусная строка
        self.status_label = tk.Label(
            root, text="Память чиста | Начните диалог с ИИ", 
            font=("Segoe UI", 9, "italic"), fg="#555", bg="#f5f7fb"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def clear_memory(self):
        """Очищаем оперативную память ассистента и интерфейс"""
        self.bot.clear_session_memory()
        self.txt_response.delete("1.0", tk.END)
        self.txt_response.insert(tk.END, "[Система] Контекст беседы стерт. ИИ вас больше ничего не помнит, можно начинать новую тему!\n")
        self.status_label.config(text="Память очищена | Готов к новому диалогу")

    def start_request_thread(self):
        user_query = self.entry_query.get().strip()
        if not user_query:
            messagebox.showwarning("Внимание", "Запрос не может быть пустым!")
            return

        self.btn_send.config(state=tk.DISABLED, text="ИИ думает...")
        
        # Дописываем наш вопрос в текстовое поле, чтобы получился вид реального чата
        self.txt_response.insert(tk.END, f"\n👉 Вы: {user_query}\n")
        self.txt_response.insert(tk.END, "🤖 ИИ: Думает...\n")
        self.txt_response.see(tk.END) # Прокручиваем текст вниз

        thread = threading.Thread(target=self.process_ai_request, args=(user_query,))
        thread.start()

    def process_ai_request(self, query):
        response = self.bot.send_request(query)

        # Удаляем строку "Думает..." и вставляем реальный ответ
        self.txt_response.delete("end - 2 lines", tk.END)
        self.txt_response.insert(tk.END, f"\n🤖 ИИ: {response}\n")
        self.txt_response.insert(tk.END, "---------------------------------------------------------\n")
        self.txt_response.see(tk.END)

        self.entry_query.delete(0, tk.END)

        if self.bot.storage.history:
            last_log = self.bot.storage.history[-1]
            total_queries = len(self.bot.storage.history)
            cost = last_log.get('cost_rub', 0.0)
            tokens = last_log.get('tokens_used', 0)
            
            # Показываем, сколько реплик сейчас лежит в памяти
            memory_count = len(self.bot.context_memory)
            status_text = f"Всего в логах: {total_queries} | Реплик в памяти: {memory_count} | Последний запрос: {tokens} токенов ({cost} ₽)"
            self.status_label.config(text=status_text)

        self.btn_send.config(state=tk.NORMAL, text="Отправить запрос")

if __name__ == "__main__":
    window = tk.Tk()
    app = AIAppGUI(window)
    window.mainloop()
