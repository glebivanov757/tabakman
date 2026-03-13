from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tabakmen-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///tabakmen.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# Модель товара
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default='')
    image_path = db.Column(db.String(500))
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
    print("✅ База данных PostgreSQL готова!")

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

# Добавление товара
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
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True, 'id': product.id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Удаление товара
@app.route('/admin/delete/<int:product_id>')
def delete_product(product_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return jsonify({'success': True})

# Заявки
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
    app.run(debug=True)