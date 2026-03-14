from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import base64
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tabakmen-secret-key-2024'

# Формируем строку подключения из переменных окружения
DB_HOST = os.getenv('PGHOST')
DB_NAME = os.getenv('PGDATABASE')
DB_USER = os.getenv('PGUSER')
# Пароль уже с URL-encode (подчеркивание заменено на %5F)
DB_PASSWORD = os.getenv('PGPASSWORD')
DB_PORT = os.getenv('PGPORT', '5432')

# Собираем DATABASE_URL вручную
if DB_HOST and DB_NAME and DB_USER and DB_PASSWORD:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print("✅ Используется PostgreSQL из переменных окружения")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tabakmen.db'
    print("⚠️ Используется SQLite (локальная база)")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

db = SQLAlchemy(app)

# Модель категории
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    icon = db.Column(db.String(10), default='📦')
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    products = db.relationship('Product', backref='category', lazy=True)

# Модель товара с base64 фото
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default='')
    image_base64 = db.Column(db.Text, default='')
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

# Модель заявок
class RareOrder(db.Model):
    __tablename__ = 'rare_orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_contact = db.Column(db.String(200), nullable=False)
    product_request = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='новый')
    created_at = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    db.create_all()
    # Добавим базовые категории если их нет
    if Category.query.count() == 0:
        categories = [
            'кальян', 'жижа', 'ашки', 'поды', 'табак', 'уголь', 
            'IQOS', 'HQD', 'вейпы', 'одноразовые сигареты', 'glo',
            'катреджи/аккумуляторы', 'кальяновые смеси', 'аксессуары для кальяна',
            'никотиновые пластинки', 'жевательный табак', 'сигаретный/трубочный табак',
            'нюхательный табак', 'аксессуары для самокруток', 'сигары', 'сигариллы',
            'папиросы', 'энергетические напитки', 'курительные трубки'
        ]
        for cat in categories:
            db.session.add(Category(name=cat))
        db.session.commit()
        print("✅ Категории добавлены")
    print("✅ База данных готова!")

# Главная страница
@app.route('/')
def index():
    products = Product.query.filter_by(in_stock=True).all()
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('index.html', products=products, categories=categories)

# Админка
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    password = os.getenv('ADMIN_PASSWORD', 'tabakmen1823*4')
    
    if request.method == 'POST':
        if request.form.get('password') == password:
            session['admin'] = True
            return render_template('admin.html', 
                                 products=Product.query.all(),
                                 categories=Category.query.all())
    
    if session.get('admin'):
        return render_template('admin.html', 
                             products=Product.query.all(),
                             categories=Category.query.all())
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/')

# Получение категорий для админки
@app.route('/admin/categories')
def admin_categories():
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    categories = Category.query.order_by(Category.sort_order).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'icon': c.icon,
        'products_count': len(c.products)
    } for c in categories])

# Добавление товара с фото в base64
@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        product = Product(
            name=request.form['name'],
            category_id=int(request.form['category']),
            price=float(request.form['price']),
            description=request.form.get('description', '')
        )
        
        # Конвертируем фото в base64
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename:
                # Читаем файл и конвертируем в base64
                photo_data = photo.read()
                photo_base64 = base64.b64encode(photo_data).decode('utf-8')
                # Сохраняем в базу
                product.image_base64 = photo_base64
                print(f"✅ Фото сконвертировано в base64, размер: {len(photo_base64)} символов")
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({'success': True, 'id': product.id})
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении товара: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Удаление товара
@app.route('/admin/delete/<int:product_id>')
def delete_product(product_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        product = Product.query.get(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
            print(f"✅ Товар удален: {product.name}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Получение заявок
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

# Обновление статуса заявки
@app.route('/admin/order/<int:order_id>/complete', methods=['POST'])
def complete_order(order_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        order = RareOrder.query.get(order_id)
        if order:
            order.status = 'выполнено'
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Заявка не найдена'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Удаление заявки
@app.route('/admin/order/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        order = RareOrder.query.get(order_id)
        if order:
            db.session.delete(order)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Заявка не найдена'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Заказ редкого товара
@app.route('/rare-order', methods=['POST'])
def rare_order():
    try:
        data = request.json
        print("📝 Получен заказ:", data)
        
        if not data.get('request'):
            return jsonify({'success': False, 'error': 'Пустой запрос'}), 400
        
        order = RareOrder(
            customer_contact=data.get('contact', 'Не указан'),
            product_request=data.get('request', '')
        )
        db.session.add(order)
        db.session.commit()
        
        print(f"🔔 Новая заявка! {order.customer_contact} хочет: {order.product_request}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        print("❌ Ошибка при создании заявки:", e)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)