import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.state import StatesGroup, State 
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

# ИЗ ТВОИХ ФАЙЛОВ
from database import async_main, async_session, Item, get_items_by_category, delete_item_from_db
from kb import main_menu, portfolio_categories, back_button

# Настройки
logging.basicConfig(level=logging.INFO)
ADMIN_ID = 8344208200 
TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Ссылки на картинки
MAIN_IMG = "https://i.postimg.cc/PJkWFWYX/cover-4.jpg"
PORTFOLIO_IMG = "https://i.postimg.cc/rs4F66S4/Gemini-Generated-Image-tzdyq1tzdyq1tzdy-(1).png"

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
        f"Приветствую, {message.from_user.full_name}! Я создаю комплексные цифровые продукты.\n\n"
        "⬇️ **Выберите интересующий вас раздел:**"
    )
    await message.answer_photo(
        photo=MAIN_IMG,
        caption=welcome_text,
        reply_markup=main_menu(message.from_user.id, ADMIN_ID),
        parse_mode="Markdown"
    )

# --- ЛОГИКА МЕНЮ ПОРТФОЛИО ---

@dp.callback_query(F.data == "open_portfolio")
async def show_portfolio(callback: CallbackQuery):
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=PORTFOLIO_IMG,
            caption="📂 **ПОРТФОЛИО**\n\nВыберите направление:",
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
    
    # СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ БОТОВ (Вывод списком)
    if category == "bots":
        text = "🤖 **СПИСОК РАЗРАБОТАННЫХ БОТОВ**\n\n"
        text += "🔗 Основной проект: @Bager_godbot\n\n"
        
        kb = InlineKeyboardBuilder()
        if items:
            text += "➕ **Дополнительные работы:**\n"
            for item in items:
                text += f"▪️ **{item.name}**\n{item.description}\n\n"
                if callback.from_user.id == ADMIN_ID:
                    kb.row(InlineKeyboardButton(text=f"🗑 Удалить {item.name}", callback_data=f"delete_{item.id}"))
        
        kb.row(InlineKeyboardButton(text="⬅️ Назад в категории", callback_data="open_portfolio"))
        await callback.message.delete()
        await callback.message.answer(text=text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        return

    # ЛОГИКА ДЛЯ ОСТАЛЬНЫХ (Карточки с фото)
    if not items:
        await callback.answer("В этом разделе пока пусто.", show_alert=True)
        return

    await callback.message.delete()
    for item in items:
        item_kb = InlineKeyboardBuilder()
        if callback.from_user.id == ADMIN_ID:
            item_kb.row(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{item.id}"))
        item_kb.row(InlineKeyboardButton(text="⬅️ Назад в категории", callback_data="open_portfolio"))
        
        caption = f"🔥 **{item.name}**\n\n{item.description}"
        
        if item.photo_id:
            await callback.message.answer_photo(photo=item.photo_id, caption=caption, reply_markup=item_kb.as_markup(), parse_mode="Markdown")
        else:
            await callback.message.answer(text=caption, reply_markup=item_kb.as_markup(), parse_mode="Markdown")
    
    await callback.answer()

# --- АДМИН-ФУНКЦИИ ---

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🌐 Открыть Web-Админку", web_app=WebAppInfo(url="https://my-portfolio-bot-io0y.onrender.com")))
    kb.row(InlineKeyboardButton(text="➕ Добавить вручную", callback_data="add_manual"))
    await message.answer("🛠 **Панель управления**", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "add_manual")
async def add_manual_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddItem.category)
    await callback.message.answer("Введите категорию (bots, sites, design):")
    await callback.answer()

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
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⏩ Пропустить фото", callback_data="skip_photo"))
    await message.answer("Отправьте фото или нажмите кнопку пропуска:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "skip_photo")
async def skip_photo_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        async with session.begin():
            new_item = Item(name=data['name'], description=data['description'], category=data['category'], photo_id=None)
            session.add(new_item)
    await callback.message.answer("✅ Работа добавлена без фотографии!")
    await state.clear()
    await callback.answer()

@dp.message(AddItem.photo, F.photo)
async def add_item_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    async with async_session() as session:
        async with session.begin():
            new_item = Item(name=data['name'], description=data['description'], category=data['category'], photo_id=photo_id)
            session.add(new_item)
    await message.answer("✅ Работа успешно добавлена!")
    await state.clear()

@dp.callback_query(F.data.startswith("delete_"))
async def delete_item_handler(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    await delete_item_from_db(item_id)
    await callback.answer("Работа удалена!")
    await callback.message.delete()

async def main():
    await async_main()
    await dp.start_polling(bot, handle_signals=False) 

if __name__ == "__main__":
    asyncio.run(main())
