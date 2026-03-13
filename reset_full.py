from app import app
from database import db, Category

with app.app_context():
    # Удаляем все таблицы
    db.drop_all()
    print("✅ Старые таблицы удалены")
    
    # Создаем новые таблицы
    db.create_all()
    print("✅ Новые таблицы созданы")
    
    # Добавляем категории
    categories = [
        "одноразовые сигареты", "вейпы и системы", "glo", "IQOS", "жидкости",
        "катреджи/аккумуляторы", "кальян", "кальяновые смеси", "уголь",
        "аксессуары для кальяна", "никотиновые пластинки", "жевательный табак",
        "сигаретный/трубочный табак", "нюхательный табак",
        "аксессуары для самокруток", "сигары", "сигариллы", "папиросы",
        "энергетические напитки", "курительные трубки"
    ]
    
    for cat_name in categories:
        cat = Category(name=cat_name, icon='📦')
        db.session.add(cat)
    
    db.session.commit()
    print(f"✅ Добавлено {len(categories)} категорий")
    
    # Проверяем
    from database import Product
    print("📊 Таблицы созданы:")
    print("   - Category (категории)")
    print("   - Product (товары)")
    print("   - RareOrder (заявки)")
