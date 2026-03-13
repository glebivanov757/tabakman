# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, SUPPORT_USERNAME, ADMIN_ID
import logging

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Основные кнопки для всех
    keyboard = [
        [InlineKeyboardButton(
            "🛍 Открыть магазин", 
            url="https://tabakman.vercel.app"
        )],
        [InlineKeyboardButton(
            "📢 Наш канал", 
            url="https://t.me/TABAKMAN_tgk"
        )],
        [InlineKeyboardButton("📞 Техподдержка", callback_data='support')]
    ]
    
    # Если это админ - добавляем маленькую кнопку
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton(
            "⚙️ Админка", 
            url="https://tabakman.vercel.app/admin"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в ТАБАКМЕН!\n\n"
        "🛍 Жми кнопку — смотри каталог\n"
        "📢 Новинки и поставки в канале\n"
        "📞 Если что — техподдержка рядом",
        reply_markup=reply_markup
    )

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'support':
        # Создаем клавиатуру с кнопкой "Назад"
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📞 Свяжись с техподдержкой: {SUPPORT_USERNAME}\n\n"
            "Поможем с любыми вопросами!",
            reply_markup=reply_markup
        )
    
    elif query.data == 'back_to_main':
        user_id = update.effective_user.id
        
        # Основные кнопки для всех
        keyboard = [
            [InlineKeyboardButton(
                "🛍 Открыть магазин", 
                url="https://tabakman.vercel.app"
            )],
            [InlineKeyboardButton(
                "📢 Наш канал", 
                url="https://t.me/TABAKMAN_tgk"
            )],
            [InlineKeyboardButton("📞 Техподдержка", callback_data='support')]
        ]
        
        # Если это админ - добавляем маленькую кнопку
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton(
                "⚙️ Админка", 
                url="https://tabakman.vercel.app/admin"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👋 Добро пожаловать в ТАБАКМЕН!\n\n"
            "🛍 Жми кнопку — смотри каталог\n"
            "📢 Новинки и поставки в канале\n"
            "📞 Если что — техподдержка рядом",
            reply_markup=reply_markup
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 Бот запущен! Нажми Ctrl+C для остановки.")
    print(f"📢 Кнопка с каналом добавлена: @TABAKMAN_tgk")
    print(f"👑 Кнопка админки будет видна только пользователю с ID: {ADMIN_ID}")
    app.run_polling()

if __name__ == '__main__':
    main()