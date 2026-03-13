# run.py
import threading
from bot import main as run_bot
from app import app

def run_website():
    app.run(debug=True, use_reloader=False, port=5000)

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем сайт
    print("🚀 Запуск сайта на http://127.0.0.1:5000")
    print("📱 Открой Telegram и найди своего бота")
    run_website()