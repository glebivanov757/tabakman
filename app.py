# app.py
from flask import Flask, render_template, request, jsonify, session, redirect
from database import db, Product, Category, RareOrder
from config import ADMIN_PASSWORD
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tabakmen-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tabakmen.db'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db.init_app(app)

with app.app_context():
    db.create_all()
    print("✅ База данных создана!")

# Главная страница
@app.route('/')
def index():
    products = Product.query.filter_by(in_stock=True).all()
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('index.html', products=products, categories=categories)

# Админка
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
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

# Управление категориями
@app.route('/admin/categories')
def admin_categories():
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    categories = Category.query.order_by(Category.sort_order).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'icon': c.icon,
        'sort_order': c.sort_order,
        'products_count': len(c.products)
    } for c in categories])

@app.route('/admin/category/add', methods=['POST'])
def add_category():
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    data = request.json
    category = Category(
        name=data['name'],
        icon=data.get('icon', '📦'),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({'success': True, 'id': category.id})

@app.route('/admin/category/delete/<int:category_id>')
def delete_category(category_id):
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    category = Category.query.get(category_id)
    if category:
        if len(category.products) > 0:
            return jsonify({'success': False, 'error': 'В категории есть товары'})
        db.session.delete(category)
        db.session.commit()
    return jsonify({'success': True})

# Добавление товара
@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin'):
        return jsonify({'error': 'Не авторизован'}), 403
    
    try:
        name = request.form.get('name', '').strip()
        category_id = int(request.form.get('category', 0))
        price = float(request.form.get('price', 0))
        description = request.form.get('description', '')
        
        if not name or not category_id or not price:
            return jsonify({'success': False, 'error': 'Заполните все поля'}), 400
        
        product = Product(
            name=name,
            category_id=category_id,
            price=price,
            description=description
        )
        
        db.session.add(product)
        db.session.flush()
        
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename:
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filename = f"product_{product.id}.jpg"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(filepath)
                product.image_path = f"/static/images/{filename}"
                print(f"✅ Фото сохранено: {filename}")
        
        db.session.commit()
        print(f"✅ Товар добавлен: {product.name}")
        
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
            if product.image_path:
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                         os.path.basename(product.image_path))
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    print(f"✅ Фото удалено: {photo_path}")
            
            db.session.delete(product)
            db.session.commit()
            print(f"✅ Товар удален: {product.name}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Заявки на редкие товары
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

# Обновление статуса заявки (НОВОЕ)
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

# Удаление заявки (НОВОЕ)
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
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print(f"✅ Папка для фото: {app.config['UPLOAD_FOLDER']}")
    app.run(debug=True, host='127.0.0.1', port=5000)