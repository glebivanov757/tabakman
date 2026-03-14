from app import app, db, Category

with app.app_context():
    categories = [
        'кальян', 'жижа', 'ашки', 'поды', 'табак', 'уголь', 
        'IQOS', 'HQD', 'вейпы', 'одноразовые сигареты', 'glo',
        'катреджи/аккумуляторы', 'кальяновые смеси', 'аксессуары для кальяна',
        'никотиновые пластинки', 'жевательный табак', 'сигаретный/трубочный табак',
        'нюхательный табак', 'аксессуары для самокруток', 'сигары', 'сигариллы',
        'папиросы', 'энергетические напитки', 'курительные трубки'
    ]
    
    for cat_name in categories:
        # Проверяем, есть ли уже такая категория
        exists = Category.query.filter_by(name=cat_name).first()
        if not exists:
            cat = Category(name=cat_name)
            db.session.add(cat)
            print(f"➕ Добавлена категория: {cat_name}")
    
    db.session.commit()
    print("✅ Категории добавлены!")