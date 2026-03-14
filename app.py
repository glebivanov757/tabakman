from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import base64
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tabakmen-secret-key-2024'

# Используем PostgreSQL через переменные
DB_HOST = os.getenv('PGHOST')
DB_NAME = os.getenv('PGDATABASE')
DB_USER = os.getenv('PGUSER')
DB_PASSWORD = os.getenv('PGPASSWORD')
DB_PORT = os.getenv('PGPORT', '5432')

if DB_HOST and DB_NAME and DB_USER and DB_PASSWORD:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print("✅ Используется PostgreSQL")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tabakmen.db'
    print("⚠️ Используется SQLite")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель категории
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

# Модель товара
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    price = db.Column(db.Float, nullable=False)
    category = db.relationship('Category')

# Создаём таблицы
with app.app_context():
    db.create_all()
    # Добавляем категории если их нет
    if Category.query.count() == 0:
        categories = [
            'кальян', 'жижа', 'ашки', 'поды', 'табак', 'уголь', 
            'IQOS', 'HQD', 'вейпы'
        ]
        for cat in categories:
            db.session.add(Category(name=cat))
        db.session.commit()
        print("✅ Категории добавлены")

@app.route('/')
def index():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('index.html', products=products, categories=categories)

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
        product = Product(
            name=request.form['name'],
            category_id=int(request.form['category']),
            price=float(request.form['price'])
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/delete/<int:product_id>')
def delete_product(product_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/rare-order', methods=['POST'])
def rare_order():
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run()