import os
import json
from dotenv import load_dotenv
from gigachat import GigaChat

load_dotenv()

PROMPTS = {
    "creator": (
        "Ты — Агент-Креатор стартапов в Москве. Твоя задача — придумать уникальную, "
        "креативную и жизнеспособную концепцию бизнеса на основе вводных данных.\n"
        "ОБЯЗАТЕЛЬНО дай проекту яркое название на русском языке и сформулируй Уникальное Торговое Предложение (УТП)."
    ),
    "analyst": (
        "Ты — Агент-Маркетолог и Аналитик московского рынка. Изучи предложенную концепцию стартапа.\n"
        "Определи целевую аудиторию (ЦА) в Москве, выдели 2-3 главных конкурента "
        "и опиши основные риски, с которыми столкнется проект."
    ),
    "financier": (
        "Ты — Агент-Финансист. Проанализируй стартап и выделенный бюджет.\n"
        "Опиши, на что конкретно пойдут первоначальные вложения в Москве (аренда, софт, маркетинг).\n"
        "Спрогнозируй примерный срок окупаемости бизнеса и ключевые источники доходов."
    )
}

class AIAgentManager:
    def __init__(self, model_version: str = "GigaChat-3-Ultra"):
        self.model = model_version
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not self.credentials:
            raise ValueError("Ошибка: Токен GIGACHAT_CREDENTIALS не найден в .env!")

    def _call_gigachat(self, system_prompt: str, user_message: str) -> str:
        """Синхронный боевой метод вызова реального API Сбера с добавлением квадратных скобок [0]"""
        try:
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat({
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.6
                })
                # Жестко используем индекс [0] для предотвращения ошибок 'list object'
                return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Ошибка агента: {e}"

    def generate_full_startup(self, sphere: str, budget: str) -> dict:
        """Последовательная координация цепочки из 3-х ИИ-агентов"""
        base_context = f"Сфера бизнеса: {sphere}. Стартовый бюджет: {budget}."
        
        # 1. Запуск Креатора
        print("[Мультиагент] Шаг 1: Агент-Креатор создает концепцию...")
        creator_response = self._call_gigachat(PROMPTS["creator"], base_context)
        
        # 2. Запуск Аналитика (передаем ему контекст Креатора)
        print("[Мультиагент] Шаг 2: Агент-Аналитик оценивает рынок Москвы...")
        analyst_context = f"{base_context}\n\nКонцепция от Креатора:\n{creator_response}"
        analyst_response = self._call_gigachat(PROMPTS["analyst"], analyst_context)
        
        # 3. Запуск Финансиста (передаем ему вообще всю цепочку)
        print("[Мультиагент] Шаг 3: Агент-Финансист просчитывает окупаемость...")
        final_context = f"{analyst_context}\n\nАнализ рынка от Аналитика:\n{analyst_response}"
        financier_response = self._call_gigachat(PROMPTS["financier"], final_context)
        
        return {
            "title": f"Стартап в сфере {sphere}",
            "concept": creator_response,
            "market_analysis": analyst_response,
            "financial_plan": financier_response
        }
