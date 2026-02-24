from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Главное меню
def main_menu(user_id: int, admin_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📂 ПОРТФОЛИО", callback_data="open_portfolio"))
    # Замени логин на свой
    builder.row(InlineKeyboardButton(text="💎 ЗАКАЗАТЬ", url="https://t.me/andrey_bager"))
    builder.row(InlineKeyboardButton(text="💬 ОТЗЫВЫ", url="https://t.me/твой_канал"))
    
    if user_id == admin_id:
        builder.row(InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="stats"))
    return builder.as_markup()

# Меню категорий внутри Портфолио
def portfolio_categories():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎨 Дизайн", callback_data="cat_design"))
    builder.row(InlineKeyboardButton(text="🌐 Сайты", callback_data="cat_sites"))
    builder.row(InlineKeyboardButton(text="🤖 Боты", callback_data="cat_bots"))
    builder.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="go_main"))
    builder.adjust(1)
    return builder.as_markup()

# Кнопка назад (универсальная)
def back_button():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад в категории", callback_data="open_portfolio"))
    return builder.as_markup()