from sqlalchemy import String, Integer, select, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# 1. Настройка подключения к SQLite
engine = create_async_engine(url='sqlite+aiosqlite:///./test.db')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

# 2. Описание таблицы работ
class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
    # nullable=True позволяет добавлять работы БЕЗ фото
    photo_id: Mapped[str] = mapped_column(String(255), nullable=True) 
    category: Mapped[str] = mapped_column(String(50))

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ---

# Создание таблиц
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Получение списка работ по категории
async def get_items_by_category(category_name):
    async with async_session() as session:
        result = await session.execute(select(Item).where(Item.category == category_name))
        return result.scalars().all()

# Удаление работы из базы
async def delete_item_from_db(item_id: int):
    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(Item).where(Item.id == item_id))
