# database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Таблица категорий
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # Название категории
    icon = db.Column(db.String(10), default='📦')                  # Иконка (эмодзи)
    sort_order = db.Column(db.Integer, default=0)                  # Порядок сортировки
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Связь с товарами (одна категория - много товаров)
    products = db.relationship('Product', backref='category_obj', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

# Таблица товаров
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # ID категории
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default='')
    image_path = db.Column(db.String(500))
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Product {self.name}>'

# Таблица заявок на редкие товары
class RareOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_contact = db.Column(db.String(200), nullable=False)
    product_request = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='новый')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Order {self.product_request}>'