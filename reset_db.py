from app import app
from database import db

with app.app_context():
    # Удаляем все таблицы
    db.drop_all()
    print("✅ Старые таблицы удалены")
    
    # Создаем таблицы заново
    db.create_all()
    print("✅ Новые таблицы созданы")
    
    # Проверяем (новая команда)
    inspector = db.inspect(db.engine)
    print("📊 Таблицы в базе:", inspector.get_table_names())
