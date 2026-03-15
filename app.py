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
    print("✅ Используется PostgreSQL (жёстко прописано)")
    print(f"🔌 Строка подключения: {DB_URL}")
except Exception as e:
    print(f"❌ Ошибка подключения к PostgreSQL: {e}")
    exit(1)  # Останавливаем приложение, если нет базы

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    
    # Добавляем категории если их нет
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
        print(f"✅ Добавлено {len(categories)} категорий")

@app.route('/')
def index():
    try:
        products = Product.query.filter_by(in_stock=True).all()
        categories = Category.query.all()
        return render_template('index.html', products=products, categories=categories)
    except Exception as e:
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
        product = Product(
            name=request.form['name'],
            category_id=int(request.form['category']),
            price=float(request.form['price']),
            image_url=request.form.get('image_url', '')
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True, 'id': product.id})
    except Exception as e:
        db.session.rollback()
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
        return jsonify({'success': True})
    except Exception as e:
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
        return jsonify({'success': True})
    except Exception as e:
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
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run()