from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

# Категории товаров
categories = ['кальян', 'жижа', 'ашки', 'поды', 'табак', 'уголь', 'IQOS', 'HQD', 'вейпы']
products = []  # товары пока пусто

@app.route('/')
def index():
    return render_template('index.html', products=products, categories=categories)

@app.route('/rare-order', methods=['POST'])
def rare_order():
    return jsonify({'success': True})

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True)
