from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tabakmen-secret-key-2024'

# Подключение к базе
DB_URL = "postgresql://postgres:vGRKKdVkmansJcljFhyJZfamVTGivIso@postgres.railway.internal:5432/railway"

try:
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
    print("✅ Используется PostgreSQL")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    exit(1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ============================================
# ФУНКЦИЯ ПРЕОБРАЗОВАНИЯ ССЫЛОК GOOGLE DRIVE
# ============================================
def convert_google_drive_link(url):
    """Преобразует любую ссылку Google Drive в прямую ссылку на изображение"""
    if not url or not isinstance(url, str):
        return url
    
    print(f"🔍 Оригинальная ссылка: {url}")
    
    if 'drive.google.com' in url:
        try:
            if '/file/d/' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
                converted = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
                print(f"✅ Преобразована в thumbnail: {converted}")
                return converted
            elif 'id=' in url:
                file_id = url.split('id=')[1].split('&')[0]
                converted = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
                print(f"✅ Преобразована в thumbnail: {converted}")
                return converted
            elif 'uc?' in url:
                return url
        except Exception as e:
            print(f"⚠️ Ошибка преобразования: {e}")
            return url
    return url

# Модели
class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), default='')
    in_stock = db.Column(db.Boolean, default=True)
    category = db.relationship('Category', backref='products')

class RareOrder(db.Model):
    __tablename__ = 'rare_order'
    id = db.Column(db.Integer, primary_key=True)
    customer_contact = db.Column(db.String(200), nullable=False)
    product_request = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='новый')
    created_at = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    db.create_all()
    print("✅ Таблицы созданы")
    
    # Полный список нужных категорий
    correct_categories = [
        'Одноразовые электронные сигареты',
        'glo',
        'IQOS',
        'Вейпы и электронные сигареты',
        'Картриджи, испарители и аккумуляторы',
        'Жидкости',
        'Никотиновые пластинки',
        'Кальяны',
        'Табак для кальяна',
        'Уголь для кальяна',
        'Аксессуары для кальяна',
        'Жевательный табак',                    # ← Отдельная категория
        'Сигаретный, Трубочный табак',            # ← Отдельная категория
        'Нюхательный табак',
        'Аксессуары для самокруток',
        'Сигары, сигариллы',
        'Папиросы',
        'Зажигалки, аксессуары',
        'Напитки',
        'Курительные трубки'
    ]
    
    # Словарь для переноса товаров
    move_map = {
        'кальян': 'Кальяны',
        'уголь': 'Уголь для кальяна',
        'вейпы': 'Вейпы и электронные сигареты',
        'одноразовые сигареты': 'Одноразовые электронные сигареты',
        'катреджи/аккумуляторы': 'Картриджи, испарители и аккумуляторы',
        'кальяновые смеси': 'Табак для кальяна',
        'аксессуары для кальяна': 'Аксессуары для кальяна',
        'никотиновые пластинки': 'Никотиновые пластинки',
        'жевательный табак': 'Жевательный табак',
        'сигаретный/трубочный табак': 'Сигаретный/Трубочный табак',
        'нюхательный табак': 'Нюхательный табак',
        'аксессуары для самокруток': 'Аксессуары для самокруток',
        'сигары': 'Сигары, сигариллы',
        'сигариллы': 'Сигары, сигариллы',
        'папиросы': 'Папиросы',
        'энергетические напитки': 'Напитки',
        'курительные трубки': 'Курительные трубки',
        'ашка': 'Одноразовые электронные сигареты',
        'ашки': 'Одноразовые электронные сигареты',
        'жижа': 'Жидкости',
        'поды': 'Вейпы и электронные сигареты',
        'HQD': 'Одноразовые электронные сигареты'
    }
    
    # ПЕРЕНОС ТОВАРОВ
    for old_name, new_name in move_map.items():
        old_cat = Category.query.filter_by(name=old_name).first()
        new_cat = Category.query.filter_by(name=new_name).first()
        
        if old_cat:
            products = Product.query.filter_by(category_id=old_cat.id).all()
            if products:
                if not new_cat:
                    new_cat = Category(name=new_name)
                    db.session.add(new_cat)
                    db.session.flush()
                    print(f"➕ Создана новая категория: {new_name}")
                
                print(f"🔄 Перенос {len(products)} товаров из '{old_name}' в '{new_name}'")
                for product in products:
                    product.category_id = new_cat.id
    
    # УДАЛЕНИЕ СТАРЫХ КАТЕГОРИЙ
    old_categories_to_delete = [
        'кальян', 'табак', 'уголь', 'вейпы', 'одноразовые сигареты',
        'катреджи/аккумуляторы', 'кальяновые смеси', 'аксессуары для кальяна',
        'никотиновые пластинки', 'жевательный табак', 'сигаретный/трубочный табак',
        'нюхательный табак', 'аксессуары для самокруток', 'сигары',
        'сигариллы', 'папиросы', 'энергетические напитки', 'курительные трубки',
        'ашка', 'ашки', 'жижа', 'поды', 'HQD', 'Кальянные смеси', 'Сигаретный табак, Жевательный табак' , 'Сигаретный/Трубочный табак'
    ]
    
    for cat_name in old_categories_to_delete:
        cat = Category.query.filter_by(name=cat_name).first()
        if cat:
            products_left = Product.query.filter_by(category_id=cat.id).count()
            if products_left == 0:
                db.session.delete(cat)
                print(f"🗑️ Удалена пустая категория: {cat_name}")
            else:
                print(f"⚠️ Категория '{cat_name}' ещё содержит {products_left} товаров")
    
    # ДОБАВЛЕНИЕ НОВЫХ КАТЕГОРИЙ
    for cat_name in correct_categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
            print(f"➕ Добавлена новая категория: {cat_name}")
    
    db.session.commit()
    print("✅ Категории обновлены")

@app.route('/')
def index():
    # Проверка возраста
    if not session.get('age_verified'):
        return redirect('/age-verification')
    
    products = Product.query.filter_by(in_stock=True).all()
    categories = Category.query.all()
    return render_template('index.html', products=products, categories=categories)

@app.route('/age-verification', methods=['GET', 'POST'])
def age_verification():
    if request.method == 'POST':
        if request.form.get('age') == 'yes':
            session['age_verified'] = True
            return redirect('/')
        else:
            return "<h1 style='color: red; text-align: center; margin-top: 50px;'>🚫 Доступ запрещен лицам младше 18 лет</h1>"
    
    return render_template('age_verification.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    password = os.getenv('ADMIN_PASSWORD', 'tabakmen1823*4')
    
    if request.method == 'POST':
        if request.form.get('password') == password:
            session['admin'] = True
    
    if session.get('admin'):
        return render_template('admin.html', 
                             products=Product.query.all(),
                             categories=Category.query.all())
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        # Получаем ссылку и преобразуем её
        original_url = request.form.get('image_url', '')
        converted_url = convert_google_drive_link(original_url)
        
        product = Product(
            name=request.form['name'],
            category_id=int(request.form['category']),
            price=float(request.form['price']),
            image_url=converted_url,
            in_stock='in_stock' in request.form
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Товар не найден'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': product.id,
            'name': product.name,
            'category_id': product.category_id,
            'price': product.price,
            'image_url': product.image_url,
            'in_stock': product.in_stock
        })
    
    if request.method == 'POST':
        try:
            original_url = request.form.get('image_url', '')
            converted_url = convert_google_drive_link(original_url)
            
            product.name = request.form['name']
            product.category_id = int(request.form['category'])
            product.price = float(request.form['price'])
            product.image_url = converted_url
            product.in_stock = 'in_stock' in request.form
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/delete/<int:product_id>')
def delete_product(product_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        product = Product.query.get(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/orders')
def get_orders():
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    orders = RareOrder.query.order_by(RareOrder.created_at.desc()).all()
    return jsonify([{
        'id': o.id,
        'contact': o.customer_contact,
        'request': o.product_request,
        'status': o.status,
        'created_at': o.created_at.strftime('%d.%m.%Y %H:%M')
    } for o in orders])

@app.route('/admin/order/<int:order_id>/complete', methods=['POST'])
def complete_order(order_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    order = RareOrder.query.get(order_id)
    if order:
        order.status = 'выполнено'
        db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/order/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    order = RareOrder.query.get(order_id)
    if order:
        db.session.delete(order)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/rare-order', methods=['POST'])
def rare_order():
    try:
        data = request.json
        order = RareOrder(
            customer_contact=data.get('contact', 'Не указан'),
            product_request=data.get('request', '')
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run()