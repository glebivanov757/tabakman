from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tabakmen-secret-key-2024'

# ============================================
# ЖЁСТКО ПРОПИСЫВАЕМ ПОДКЛЮЧЕНИЕ К POSTGRESQL
# ============================================
DB_URL = "postgresql://postgres:vGRKKdVkmansJcljFhyJZfamVTGivIso@postgres.railway.internal:5432/railway"

try:
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
    print("✅ Используется PostgreSQL")
except Exception as e:
    print(f"❌ Ошибка подключения к PostgreSQL: {e}")
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

# Модель категории
class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

# Модель товара
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), default='')
    in_stock = db.Column(db.Boolean, default=True)
    category = db.relationship('Category')

# Модель заявок
class RareOrder(db.Model):
    __tablename__ = 'rare_order'
    id = db.Column(db.Integer, primary_key=True)
    customer_contact = db.Column(db.String(200), nullable=False)
    product_request = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='новый')
    created_at = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    # Создаём таблицы
    db.create_all()
    print("✅ Таблицы созданы")
    
    # ============================================
    # ОБНОВЛЕНИЕ КАТЕГОРИЙ (С СОХРАНЕНИЕМ ПРОГРЕССА)
    # ============================================
    
    # Полный список новых категорий
    new_categories = [
        'Одноразовые электронные сигареты',  # бывшие ашки
        'glo',
        'IQOS',
        'Вейпы и электронные сигареты',      # бывшие поды
        'Картриджи, испарители и аккумуляторы',
        'Жидкости',                           # бывшая жижа
        'Никотиновые пластинки',
        'Кальяны',
        'Кальянные смеси',
        'Уголь для кальяна',
        'Аксессуары для кальяна',
        'Сигаретный табак, Жевательный табак',
        'Нюхательный табак',
        'Аксессуары для самокруток',
        'Сигары, сигариллы',
        'Папиросы',
        'Зажигалки, аксессуары',
        'Напитки',
        'Курительные трубки'
    ]
    
    if Category.query.count() == 0:
        # Если категорий нет - создаём все новые
        for cat in new_categories:
            db.session.add(Category(name=cat))
        db.session.commit()
        print(f"✅ Добавлено {len(new_categories)} новых категорий")
    else:
        # Если категории уже есть - обновляем старые названия
        print("🔄 Обновляем названия категорий...")
        
        # Словарь замены старых названий на новые
        category_updates = {
            'ашка': 'Одноразовые электронные сигареты',
            'ашки': 'Одноразовые электронные сигареты',
            'жижа': 'Жидкости',
            'поды': 'Вейпы и электронные сигареты'
        }
        
        # Обновляем старые названия
        for old_name, new_name in category_updates.items():
            cat = Category.query.filter_by(name=old_name).first()
            if cat:
                cat.name = new_name
                print(f"  ➡️ {old_name} → {new_name}")
        
        # Проверяем, есть ли уже все новые категории
        existing_names = [cat.name for cat in Category.query.all()]
        added_count = 0
        for new_cat in new_categories:
            if new_cat not in existing_names:
                db.session.add(Category(name=new_cat))
                added_count += 1
                print(f"  ➕ Добавлена новая категория: {new_cat}")
        
        db.session.commit()
        print(f"✅ Обновление завершено. Добавлено {added_count} новых категорий")

@app.route('/')
def index():
    try:
        products = Product.query.filter_by(in_stock=True).all()
        categories = Category.query.all()
        return render_template('index.html', products=products, categories=categories)
    except Exception as e:
        print(f"❌ Ошибка на главной: {e}")
        return f"Ошибка базы данных: {e}", 500

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    password = os.getenv('ADMIN_PASSWORD', 'tabakmen1823*4')
    
    if request.method == 'POST':
        if request.form.get('password') == password:
            session['admin'] = True
    
    if session.get('admin'):
        try:
            return render_template('admin.html', 
                                 products=Product.query.all(),
                                 categories=Category.query.all())
        except Exception as e:
            print(f"❌ Ошибка в админке: {e}")
            return f"Ошибка загрузки данных: {e}", 500
    
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
        original_url = request.form.get('image_url', '')
        converted_url = convert_google_drive_link(original_url)
        
        product = Product(
            name=request.form['name'],
            category_id=int(request.form['category']),
            price=float(request.form['price']),
            image_url=converted_url
        )
        db.session.add(product)
        db.session.commit()
        print(f"✅ Товар добавлен: {product.name}")
        return jsonify({'success': True, 'id': product.id})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при добавлении товара: {e}")
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
            print(f"✅ Товар удален: {product.name}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/orders')
def get_orders():
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        orders = RareOrder.query.order_by(RareOrder.created_at.desc()).all()
        return jsonify([{
            'id': o.id,
            'contact': o.customer_contact,
            'request': o.product_request,
            'status': o.status,
            'created_at': o.created_at.strftime('%d.%m.%Y %H:%M')
        } for o in orders])
    except Exception as e:
        print(f"❌ Ошибка при получении заявок: {e}")
        return jsonify([])

@app.route('/admin/order/<int:order_id>/complete', methods=['POST'])
def complete_order(order_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        order = RareOrder.query.get(order_id)
        if order:
            order.status = 'выполнено'
            db.session.commit()
            print(f"✅ Заявка {order_id} выполнена")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Ошибка при выполнении заявки: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/order/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        order = RareOrder.query.get(order_id)
        if order:
            db.session.delete(order)
            db.session.commit()
            print(f"✅ Заявка {order_id} удалена")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Ошибка при удалении заявки: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        print(f"📝 Новая заявка: {order.customer_contact} хочет {order.product_request}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Ошибка при создании заявки: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run()