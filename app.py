from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

# Категории товаров (просто список)
categories = ['кальян', 'жижа', 'ашки', 'поды', 'табак', 'уголь', 'IQOS', 'HQD', 'вейпы']

@app.route('/')
def index():
    # Передаём только категории, товаров пока нет
    return render_template('index.html', products=[], categories=categories)

@app.route('/rare-order', methods=['POST'])
def rare_order():
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)