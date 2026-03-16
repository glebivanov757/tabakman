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
    # ПОЛНАЯ ЗАМЕНА КАТЕГОРИЙ (СТАРЫЕ УДАЛЯЮТСЯ)
    # ============================================
    
    # ЕДИНСТВЕННЫЙ ПРАВИЛЬНЫЙ СПИСОК КАТЕГОРИЙ
    correct_categories = [
        'Одноразовые электронные сигареты',  # вместо ашка
        'glo',
        'IQOS',
        'Вейпы и электронные сигареты',      # вместо поды
        'Картриджи, испарители и аккумуляторы',
        'Жидкости',                           # вместо жижа
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
    
    # Получаем все существующие категории
    all_cats = Category.query.all()
    existing_names = [cat.name for cat in all_cats]
    
    print("🔄 Текущие категории в базе:")
    for cat in all_cats:
        print(f"   - {cat.name}")
    
    # Словарь для маппинга старых названий на новые
    category_map = {
        'ашка': 'Одноразовые электронные сигареты',
        'ашки': 'Одноразовые электронные сигареты',
        'жижа': 'Жидкости',
        'поды': 'Вейпы и электронные сигареты',
        'кальян': 'Кальяны',
        'табак': 'Сигаретный табак, Жевательный табак',
        'уголь': 'Уголь для кальяна'
    }
    
    # Переносим товары из старых категорий в новые
    for old_name, new_name in category_map.items():
        old_cat = Category.query.filter_by(name=old_name).first()
        new_cat = Category.query.filter_by(name=new_name).first()
        
        if old_cat and old_cat.products:
            print(f"🔄 Перенос товаров из '{old_name}' в '{new_name}'")
            for product in old_cat.products:
                if new_cat:
                    product.category_id = new_cat.id
                else:
                    # Если новой категории нет - создаём
                    new_cat = Category(name=new_name)
                    db.session.add(new_cat)
                    db.session.flush()
                    product.category_id = new_cat.id
    
    # Удаляем ВСЕ старые категории, которых нет в правильном списке
    deleted_count = 0
    for cat in all_cats:
        if cat.name not in correct_categories:
            if not cat.products:  # Удаляем только пустые категории
                print(f"🗑️ Удаление пустой категории: {cat.name}")
                db.session.delete(cat)
                deleted_count += 1
            else:
                print(f"⚠️ Категория '{cat.name}' не пуста ({len(cat.products)} товаров) - оставляем")
    
    # Добавляем недостающие категории из правильного списка
    added_count = 0
    for cat_name in correct_categories:
        exists = Category.query.filter_by(name=cat_name).first()
        if not exists:
            db.session.add(Category(name=cat_name))
            added_count += 1
            print(f"➕ Добавлена категория: {cat_name}")
    
    db.session.commit()
    print(f"✅ Итог: удалено {deleted_count} старых категорий, добавлено {added_count} новых")
    
    # Показываем финальный список
    final_cats = Category.query.all()
    print("📊 Финальные категории в базе:")
    for cat in final_cats:
        print(f"   - {cat.name}")
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