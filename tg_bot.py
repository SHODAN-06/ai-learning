import os
import asyncio
import re
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from ai_agent_manager import AIAgentManager
from database import engine, Base, SessionLocal, BusinessIdeaModel

Base.metadata.create_all(bind=engine)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Ошибка: Токен TELEGRAM_TOKEN не найден в .env!")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
agent_manager = AIAgentManager()

class StartupForm(StatesGroup):
    waiting_for_topic = State()   
    waiting_for_budget = State()  

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💡 Сгенерировать идею"), KeyboardButton(text="📊 Мои сохраненные идеи")],
            [KeyboardButton(text="🗑️ Очистить историю")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def get_finish_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💡 Сгенерировать новую идею")],
            [KeyboardButton(text="🔚 Завершить работу")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Что делаем дальше?..."
    )

def clean_and_format_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"^\s*[\*\-]\s+", r"• ", text, flags=re.MULTILINE)
    text = text.replace("#", "")
    return text.strip()

async def send_long_message(message: Message, text: str):
    max_length = 4000
    if len(text) <= max_length:
        await message.answer(text, parse_mode="HTML")
    else:
        lines = text.split("\n")
        current_chunk = ""
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_length:
                await message.answer(current_chunk, parse_mode="HTML")
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            await message.answer(current_chunk, parse_mode="HTML")

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear() 
    welcome_text = (
        f"Привет, <b>{message.from_user.full_name}</b>! 👋\n\n"
        "🤖 Рад приветствовать тебя в мультиагентной ИИ-системе разработки бизнеса.\n\n"
        "Нажми кнопку ниже, чтобы запустить пошаговый разбор стартапа."
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@dp.message(F.text.contains("сохраненные"))
async def handle_history_btn(message: Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    db = SessionLocal()
    try:
        ideas = db.query(BusinessIdeaModel).order_by(BusinessIdeaModel.id.desc()).limit(5).all()
        if not ideas:
            await message.answer("📊 Ваша база данных SQL пока пуста.")
            return
            
        history_text = "📊 <b>Последние сохраненные проекты в SQL БД:</b>\n-----------------------------------------\n"
        for idea in ideas:
            safe_topic = clean_and_format_html(idea.topic or "Общая")
            concept_raw = idea.concept or ""
            
            title_line = f"Стартап (сфера {safe_topic})"
            clean_lines = []
            
            for line in concept_raw.split("\n"):
                line_strip = line.strip()
                if not line_strip:
                    continue
                if ("название" in line_strip.lower() or "проект" in line_strip.lower() or "🏆" in line_strip) and title_line == f"Стартап (сфера {safe_topic})":
                    title_line = re.sub(r"(название проекта|проект|название|упт|идея|🏆|:|«|»|\*|\#)", "", line_strip, flags=re.IGNORECASE).strip()
                    title_line = f"«{title_line}»"
                # 🔥 УЛУЧШЕНО: Жестко вырезаем любые упоминания слова "Концепция" и двоеточия
                elif re.search(r"(концепция|описание сути бизнеса|суть проекта|описание)", line_strip, flags=re.IGNORECASE) and len(line_strip) < 30:
                    continue
                else:
                    clean_lines.append(line_strip)
            
            clean_concept = " ".join(clean_lines)
            # Дополнительно чистим превью от остаточных жирных тегов "Концепция:" на старте
            clean_concept = re.sub(r"^(<b>)?(концепция|описание|суть проекта)(:)?(<\/b>)?(\s*:)?", "", clean_concept, flags=re.IGNORECASE).strip()
            
            short_concept = clean_and_format_html(clean_concept)[:90].strip() + "..."
            history_text += f"🔹 <b>ID {idea.id}</b> | <b>Проект: {title_line}</b> ({safe_topic})\n📝 {short_concept}\n\n"
            
        history_text += "👉 Полную историю можно посмотреть на сайте: http://127.0.0"
        await message.answer(history_text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"Ошибка чтения базы данных: {e}")
    finally:
        db.close()


@dp.message(F.text.contains("Очистить историю"))
async def handle_clear_history(message: Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    db = SessionLocal()
    try:
        db.query(BusinessIdeaModel).delete()
        db.commit()
        await message.answer(
            "🗑️ <b>Ваша история успешно очищена!</b>\n\nВсе записи удалены из SQL-базы данных.", 
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        db.rollback()
        await message.answer(f"❌ Ошибка при очистке базы данных: {e}", reply_markup=get_main_keyboard())
    finally:
        db.close()

@dp.message(F.text.contains("Завершить работу"))
async def handle_finish_work(message: Message, state: FSMContext):
    await state.clear() 
    goodbye_text = (
        "🏁 <b>Работа успешно завершена!</b>\n\n"
        "Рад был помочь вам в проработке бизнес-моделей. Все ваши стартапы надежно сохранены в базе данных SQL. "
        "Когда решите сгенерировать новые гениальные идеи, просто введите команду /start или отправьте любое сообщение!"
    )
    await message.answer(goodbye_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

@dp.message(F.text.contains("Придумать") | F.text.contains("Сгенерировать"))
async def handle_suggest_btn(message: Message, state: FSMContext):
    await message.answer("1️⃣ <b>Шаг 1 из 2:</b> Напишите сферу бизнеса (например: <i>Доставка цветов</i> или <i>Online-школа</i>):", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await state.set_state(StartupForm.waiting_for_topic)

@dp.message(StartupForm.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(chosen_topic=message.text.strip())
    await message.answer("2️⃣ <b>Шаг 2 из 2:</b> Укажите ваш стартовый бюджет (например: <i>500 000 рублей</i> или <i>3 миллиона</i>):", parse_mode="HTML")
    await state.set_state(StartupForm.waiting_for_budget)

@dp.message(StartupForm.waiting_for_budget)
async def process_budget(message: Message, state: FSMContext):
    user_budget = message.text.strip()
    user_data = await state.get_data()
    user_topic = user_data.get("chosen_topic")
    await state.clear() 
    
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    status_msg = await message.answer("🤖 <b>Запуск мультиагентной сессии...</b>\n\n1️⃣ Шаг 1: Агент-Креатор проектирует уникальную концепцию стартапа...", parse_mode="HTML")

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, agent_manager.generate_full_startup, user_topic, user_budget)
        
        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=status_msg.message_id,
            text="🤖 <b>Мультиагентная сессия:</b>\n\n✅ Шаг 1: Концепция построена.\n2️⃣ Шаг 2: Агент-Маркетолог оценивает риски и конкурентов в Москве...",
            parse_mode="HTML"
        )
        await asyncio.sleep(0.3)

        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=status_msg.message_id,
            text=f"🤖 <b>Мультиагентная сессия:</b>\n\n✅ Шаг 1: Концепция построена.\n✅ Шаг 2: Анализ рынка завершен.\n3️⃣ Шаг 3: Агент-Финансист просчитывает вложения под бюджет {user_budget}...",
            parse_mode="HTML"
        )
        await asyncio.sleep(0.3)

        concept_text = clean_and_format_html(result.get("concept", "Нет данных"))
        market_text = clean_and_format_html(result.get("market_analysis", "Нет данных"))
        finance_text = clean_and_format_html(result.get("financial_plan", "Нет данных"))
        title_text = clean_and_format_html(result.get("title", f"Стартап в сфере {user_topic}"))

        db = SessionLocal()
        try:
            db_idea = BusinessIdeaModel(
                topic=user_topic, title=title_text, concept=concept_text,
                target_audience=market_text, start_capital_rub=0, 
                monetization=finance_text, steps=f"Бюджет: {user_budget}"
            )
            db.add(db_idea)
            db.commit()
            db.refresh(db_idea)
            last_id = db_idea.id
        finally:
            db.close()

        await bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

        final_response = (
            f"🎯 <b>РЕЗУЛЬТАТ РАБОТЫ КОМАНДЫ АГЕНТОВ (ID в БД: {last_id})</b>\n"
            f"💰 <b>Выделенный бюджет:</b> {user_budget}\n"
            f"-----------------------------------------\n\n"
            f"🎨 <b>1. ИДЕЯ И УТП (От Агента-Креатора):</b>\n{concept_text}\n\n"
            f"📈 <b>2. АНАЛИЗ РЫНКА И РИСКИ (От Агента-Аналитика):</b>\n{market_text}\n\n"
            f"💸 <b>3. ФИНАНСОВЫЙ ПЛАН (От Агента-Финансиста):</b>\n{finance_text}"
        )
        
        await send_long_message(message, final_response)
        await message.answer("🤖 Команда агентов успешно выполнила задачу! Что делаем дальше?", reply_markup=get_finish_keyboard())

    except Exception as e:
        await message.answer(f"❌ Произошла ошибка в координации агентов: {e}", reply_markup=get_main_keyboard())
@dp.message(F.text, StateFilter(None), ~F.text.contains("сохраненные"), ~F.text.contains("Придумать"), ~F.text.contains("Сгенерировать"), ~F.text.contains("Очистить"), ~F.text.contains("завершить"))
async def handle_fallback_text(message: Message):
    await message.answer("🤖 Для генерации бизнес-плана нажмите на кнопку <b>💡 Сгенерировать идею</b> ниже:", parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    print("[Система] Мультиагентный Telegram ИИ-Агент с FSM запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
