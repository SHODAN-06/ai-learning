from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Указываем, где будет лежать файл нашей базы данных
DATABASE_URL = "sqlite:///./database.db"

# 2. Создаем «движок» для подключения к SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 3. Создаем сессию для выполнения операций записи/чтения
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Базовый класс, от которого будут наследоваться наши таблицы
Base = declarative_base()

# 5. Описываем структуру нашей таблицы в БД (Модель таблицы)
class BusinessIdeaModel(Base):
    __tablename__ = "saved_ideas" # Имя таблицы в базе данных

    id = Column(Integer, primary_key=True, index=True) # Уникальный номер записи
    topic = Column(String, index=True)                 # Тема, которую ввел пользователь
    title = Column(String)                             # Название стартапа от ИИ
    concept = Column(Text)                             # Концепция от ИИ
    target_audience = Column(Text)                     # Аудитория
    start_capital_rub = Column(Integer)                # Капитал (число)
    monetization = Column(Text)                        # Монетизация
    steps = Column(Text)                               # Шаги (сохраним как текст через запятую)

# Функция для получения сессии базы данных при каждом запросе к серверу
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
