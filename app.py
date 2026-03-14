from flask import Flask, render_template, jsonify, request, session, redirect
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tabakmen-secret-key-2024'

# Временные данные вместо базы
categories = [
    'кальян', 'жижа', 'ашки', 'поды', 'табак', 'уголь', 
    'IQOS', 'HQD', 'вейпы', 'одноразовые сигареты', 'glo',
    'катреджи/аккумуляторы', 'кальяновые смеси', 'аксессуары для кальяна',
    'никотиновые пластинки', 'жевательный табак', 'сигаретный/трубочный табак',
    'нюхательный табак', 'аксессуары для самокруток', 'сигары', 'сигариллы',
    'папиросы', 'энергетические напитки', 'курительные трубки'
]

products = []  # Пока пусто

@app.route('/')
def index():
    return render_template('index.html', products=products, categories=categories)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    password = os.getenv('ADMIN_PASSWORD', 'tabakmen1823*4')
    
    if request.method == 'POST':
        if request.form.get('password') == password:
            session['admin'] = True
    
    if session.get('admin'):
        return render_template('admin.html', products=products, categories=categories)
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/rare-order', methods=['POST'])
def rare_order():
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)