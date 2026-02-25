import os
from aiogram import Bot, Dispatcher
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.state import StatesGroup, State 
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder # Главный импорт тут
from sqlalchemy import select

# ИЗ ТВОИХ ФАЙЛОВ
from database import async_main, async_session, Item, get_items_by_category, delete_item_from_db
from kb import main_menu, portfolio_categories, back_button

# Настройки
logging.basicConfig(level=logging.INFO)
ADMIN_ID = 8344208200 
TOKEN = os.getenv("BOT_TOKEN") 
bot = Bot(token=TOKEN)

# Ссылки на картинки
MAIN_IMG = "https://i.postimg.cc/PJkWFWYX/cover-4.jpg"
PORTFOLIO_IMG = "https://i.postimg.cc/rs4F66S4/Gemini-Generated-Image-tzdyq1tzdyq1tzdy-(1).png"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояния для админки
class AddItem(StatesGroup):
    category = State()
    name = State()
    description = State()
    photo = State()

# --- ОСНОВНЫЕ КОМАНДЫ ---

@dp.message(Command("start"))
async def start_command(message: Message):
    welcome_text = (
        f"🚀 **FULLSTACK DEVELOPER | ANDREY BAGER**\n\n"
        f"Приветствую, {message.from_user.full_name}! Я создаю комплексные цифровые продукты: от архитектуры ботов до современных веб-интерфейсов. 💻\n\n"
        "**Мой стек технологий:**\n"
        "⚡️ Backend: Python (Aiogram, FastAPI, SQLAlchemy)\n"
        "🎨 Frontend & Design: UI/UX, Web Apps\n"
        "⚙️ Automation: CRM-системы и бизнес-логика\n\n"
        "⬇️ **Выберите интересующий вас раздел:**"
    )
    await message.answer_photo(
        photo=MAIN_IMG,
        caption=welcome_text,
        reply_markup=main_menu(message.from_user.id, ADMIN_ID),
        parse_mode="Markdown"
    )

@dp.message(Command("my_id"))
async def get_id(message: Message):
    await message.answer(f"Твой ID: `{message.from_user.id}`", parse_mode="MarkdownV2")

# --- ЛОГИКА МЕНЮ ПОРТФОЛИО ---

@dp.callback_query(F.data == "open_portfolio")
async def show_portfolio(callback: CallbackQuery):
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=PORTFOLIO_IMG,
            caption="📂 **ПОРТФОЛИО**\n\nВыберите направление, чтобы увидеть примеры моих работ:",
            parse_mode="Markdown"
        ),
        reply_markup=portfolio_categories()
    )
    await callback.answer()

@dp.callback_query(F.data == "go_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=MAIN_IMG,
            caption="Главное меню. Выберите раздел:",
            parse_mode="Markdown"
        ),
        reply_markup=main_menu(callback.from_user.id, ADMIN_ID)
    )
    await callback.answer()

# --- ВЫВОД РАБОТ ---

@dp.callback_query(F.data.startswith("cat_"))
async def show_category_items(callback: CallbackQuery):
    category = callback.data.split('_')[1]
    items = await get_items_by_category(category)
    
    # 1. СПЕЦИАЛЬНЫЙ UX ДЛЯ КАТЕГОРИИ БОТОВ
    if category == "bots":
        await callback.message.delete()
        
        text = "🤖 **СПИСОК РАЗРАБОТАННЫХ БОТОВ**\n\n"
        text += "1️⃣ **👁️ ГЛАЗ БОГА**\n"
        text += "**«Глаз Бога» — это бот в Telegram, через который можно найти информацию о людях: номера телефонов, адреса, аккаунты в соцсетях и другие личные данные.**\n"
        text += "🔗 Ссылка: @Bager_godbot\n\n"
        
        text += "2️⃣ **FULLSTACK DEVELOPER | ANDREY BAGER**\n"
        text += "**Интерактивное портфолио с динамической сменой контента, встроенной админ-панелью и базой данных SQLAlchemy. Демонстрация UX/UI решений для бизнеса.**\n"
        text += "🔗 Ссылка: @portfoliocode_bot\n\n"
        
        kb = InlineKeyboardBuilder()
        if items:
            text += "➕ **Другие работы:**\n"
            for item in items:
                text += f"▪️ **{item.name}**\n{item.description}\n\n"
                if callback.from_user.id == ADMIN_ID:
                    kb.row(InlineKeyboardButton(text=f"🗑 Удалить {item.name}", callback_data=f"delete_{item.id}"))
        
        kb.row(InlineKeyboardButton(text="⬅️ Назад в категории", callback_data="open_portfolio"))
        await callback.message.answer(text=text, reply_markup=kb.as_markup(), parse_mode="Markdown")

    # 2. ГАЛЕРЕЯ ДЛЯ ДИЗАЙНА И САЙТОВ
    else:
        if not items:
            await callback.answer("В этом разделе пока пусто.", show_alert=True)
            return

        await callback.message.delete()
        for item in items:
            # Используем InlineKeyboardBuilder без локальных импортов
            item_kb = InlineKeyboardBuilder()
            if callback.from_user.id == ADMIN_ID:
                item_kb.row(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{item.id}"))
            item_kb.row(InlineKeyboardButton(text="⬅️ Назад в категории", callback_data="open_portfolio"))
            
            await callback.message.answer_photo(
                photo=item.photo_id,
                caption=f"🔥 **{item.name}**\n\n{item.description}",
                reply_markup=item_kb.as_markup(),
                parse_mode="Markdown"
            )
    await callback.answer()

# --- АДМИН-ФУНКЦИИ ---

@dp.callback_query(F.data.startswith("delete_"))
async def delete_item_handler(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    await delete_item_from_db(item_id)
    await callback.answer("Работа удалена!")
    await callback.message.delete()

@dp.message(Command("admin"))
async def add_item_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
        
    kb = InlineKeyboardBuilder()
    # Замени URL ниже на свой, когда развернешь сайт. Пока для теста поставим Google.
    kb.row(InlineKeyboardButton(
        text="🌐 Открыть Web-Админку", 
        web_app=WebAppInfo(url="https://my-portfolio-bot-io0y.onrender.com"))
    )
    kb.row(InlineKeyboardButton(text="➕ Добавить вручную (текст)", callback_data="add_manual"))
    
    await message.answer(
        "🛠 **Панель управления**\n\nВы можете управлять портфолио через современный Web-интерфейс или старым способом через чат:",
        reply_markup=kb.as_markup()
    )

@dp.message(AddItem.category)
async def add_item_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text.lower())
    await state.set_state(AddItem.name)
    await message.answer("Введите название работы:")

@dp.message(AddItem.name)
async def add_item_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddItem.description)
    await message.answer("Введите описание:")

@dp.message(AddItem.description)
async def add_item_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddItem.photo)
    await message.answer("Отправьте фото работы:")

@dp.message(AddItem.photo, F.photo)
async def add_item_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    async with async_session() as session:
        async with session.begin():
            new_item = Item(
                name=data['name'],
                description=data['description'],
                category=data['category'],
                photo_id=photo_id
            )
            session.add(new_item)
    await message.answer("✅ Работа успешно добавлена!")
    await state.clear()

@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    async with async_session() as session:
        from sqlalchemy import func
        result = await session.execute(select(func.count(Item.id)))
        count = result.scalar()
    await callback.message.answer(f"📊 Всего работ в базе: {count}")
    await callback.answer()

async def main():
    await async_main()
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:

        pass
