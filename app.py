from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime
from reportlab.pdfgen import canvas
from flask import send_file

app = Flask(__name__)
app.secret_key = 'theavocados'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

if not os.path.isdir(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# =========================
# CUSTOM JINJA FILTER
# =========================
@app.template_filter('format_currency')
def format_currency(value):
    """Format: Rp x.xxx.xxx"""
    if value is None:
        return 'Rp 0'
    try:
        value = int(value)
        formatted = f"{value:,}".replace(',', '.')
        return f"Rp {formatted}"
    except:
        return f"Rp {value}"

# =========================
# MODELS
# =========================

class Product(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(100))
    price = db.Column(db.Integer)
    cost  = db.Column(db.Integer)
    image = db.Column(db.String(500))
    stock = db.Column(db.Integer, default=0)

class Journal(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    account     = db.Column(db.String(100))
    debit       = db.Column(db.Integer)
    credit      = db.Column(db.Integer)
    description = db.Column(db.String(200))

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100))
    email    = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    orders   = db.relationship('Order', backref='user', lazy=True)

class Order(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    total          = db.Column(db.Integer)
    payment_method = db.Column(db.String(50))
    date           = db.Column(db.DateTime, default=datetime.datetime.now)
    items          = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    order_id     = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_name = db.Column(db.String(100))
    price        = db.Column(db.Integer)
    quantity     = db.Column(db.Integer)
    subtotal     = db.Column(db.Integer)

class ModalAwal(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    amount      = db.Column(db.Integer)
    description = db.Column(db.String(200))
    date        = db.Column(db.DateTime, default=datetime.datetime.now)

# =========================
# HOME
# =========================
@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)

# =========================
# ADD TO CART
# =========================
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    product = Product.query.get(id)
    if not product:
        return redirect(url_for('home'))

    if 'cart' not in session:
        session['cart'] = []

    cart  = session['cart']
    found = False

    for item in cart:
        if item['id'] == product.id:
            item['quantity'] += 1
            found = True
            break

    if not found:
        cart.append({
            'id':       product.id,
            'name':     product.name,
            'price':    product.price,
            'cost':     product.cost,
            'image':    product.image,
            'quantity': 1
        })

    session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': len(session['cart'])})

    return redirect(url_for('home'))

# =========================
# CART
# =========================
@app.route('/cart')
def cart():
    cart  = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart_items=cart, total=total)

# =========================
# REMOVE FROM CART
# =========================
@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    cart     = session.get('cart', [])
    new_cart = [item for item in cart if item['id'] != id]
    session['cart'] = new_cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        total = sum(i['price'] * i['quantity'] for i in new_cart)
        return jsonify({'success': True, 'cart_count': len(new_cart), 'total': total})

    return redirect(url_for('cart'))

# =========================
# INCREASE QUANTITY
# =========================
@app.route('/increase_quantity/<int:id>')
def increase_quantity(id):
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == id:
            item['quantity'] += 1
            break
    session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item_data = next((i for i in cart if i['id'] == id), None)
        total = sum(i['price'] * i['quantity'] for i in cart)
        return jsonify({
            'success':  True,
            'quantity': item_data['quantity'] if item_data else 0,
            'subtotal': item_data['price'] * item_data['quantity'] if item_data else 0,
            'total':    total,
            'cart_count': len(cart)
        })

    return redirect(url_for('cart'))

# =========================
# DECREASE QUANTITY
# =========================
@app.route('/decrease_quantity/<int:id>')
def decrease_quantity(id):
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == id:
            item['quantity'] -= 1
            if item['quantity'] <= 0:
                cart.remove(item)
            break
    session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item_data = next((i for i in cart if i['id'] == id), None)
        total = sum(i['price'] * i['quantity'] for i in cart)
        return jsonify({
            'success':  True,
            'quantity': item_data['quantity'] if item_data else 0,
            'removed':  item_data is None,
            'subtotal': item_data['price'] * item_data['quantity'] if item_data else 0,
            'total':    total,
            'cart_count': len(cart)
        })

    return redirect(url_for('cart'))

# =========================
# CHECKOUT
# =========================
@app.route('/checkout')
def checkout():
    cart  = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('checkout.html', cart_items=cart, total=total)

# =========================
# RECEIPT + JURNAL + ORDER
# =========================
@app.route('/receipt/<payment>')
def receipt(payment):
    cart  = session.get('cart', [])
    if not cart:
        return redirect(url_for('home'))

    total = sum(item['price'] * item['quantity'] for item in cart)

    # Jurnal penjualan
    db.session.add(Journal(account='Kas',       debit=total,  credit=0,     description='Transaksi Penjualan'))
    db.session.add(Journal(account='Penjualan', debit=0,      credit=total, description='Transaksi Penjualan'))

    # Jurnal HPP + kurangi stok
    total_hpp = 0
    for item in cart:
        product    = Product.query.get(item['id'])
        hpp_item   = product.cost * item['quantity']
        total_hpp += hpp_item
        # kurangi stok
        product.stock = max(0, product.stock - item['quantity'])

    db.session.add(Journal(account='HPP',        debit=total_hpp, credit=0,         description='Harga Pokok Penjualan'))
    db.session.add(Journal(account='Persediaan', debit=0,         credit=total_hpp, description='Pengurangan Persediaan'))

    # Simpan Order
    order = Order(
        user_id        = session.get('user_id'),
        total          = total,
        payment_method = payment,
        date           = datetime.datetime.now()
    )
    db.session.add(order)
    db.session.flush()  # get order.id

    for item in cart:
        db.session.add(OrderItem(
            order_id     = order.id,
            product_name = item['name'],
            price        = item['price'],
            quantity     = item['quantity'],
            subtotal     = item['price'] * item['quantity']
        ))

    db.session.commit()

    cart_display     = list(cart)
    session['cart']  = []

    return render_template(
        'receipt.html',
        cart_items     = cart_display,
        total          = total,
        payment_method = payment,
        date           = datetime.datetime.now().strftime('%d %B %Y, %H:%M')
    )

# =========================
# REGISTER CUSTOMER
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form['name']
        email    = request.form['email']
        password = request.form['password']
        confirm  = request.form['confirm']

        if password != confirm:
            return render_template('register.html', error='Password tidak cocok')

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email sudah terdaftar')

        new_user = User(
            name     = name,
            email    = email,
            password = generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        session['user_id']   = new_user.id
        session['user_name'] = new_user.name

        return redirect(url_for('home'))

    return render_template('register.html')

# =========================
# LOGIN CUSTOMER
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login_customer():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        user     = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id']   = user.id
            session['user_name'] = user.name
            return redirect(url_for('home'))

        return render_template('login_customer.html', error='Email atau password salah')

    return render_template('login_customer.html')

# =========================
# LOGOUT CUSTOMER
# =========================
@app.route('/logout')
def logout_customer():
    session.pop('user_id',   None)
    session.pop('user_name', None)
    return redirect(url_for('home'))

# =========================
# ORDER HISTORY
# =========================
@app.route('/orders')
def order_history():
    if 'user_id' not in session:
        return redirect(url_for('login_customer'))

    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.date.desc()).all()
    return render_template('order_history.html', orders=orders)

# =========================
# JURNAL UMUM
# =========================
@app.route('/journal')
def journal():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    journals = Journal.query.all()
    return render_template('journal.html', journals=journals)

# =========================
# BUKU BESAR
# =========================
@app.route('/ledger')
def ledger():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    journals   = Journal.query.all()
    ledger_data = {}

    for j in journals:
        if j.account not in ledger_data:
            ledger_data[j.account] = {'debit': 0, 'credit': 0}
        ledger_data[j.account]['debit']  += j.debit
        ledger_data[j.account]['credit'] += j.credit

    return render_template('ledger.html', ledger_data=ledger_data)

# =========================
# LOGIN ADMIN
# =========================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

# =========================
# DASHBOARD ADMIN
# =========================
@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    total_products    = Product.query.count()
    total_journals    = Journal.query.count()
    total_transactions = Order.query.count()

    sales = 0
    for j in Journal.query.all():
        if j.account == 'Penjualan':
            sales += j.credit

    return render_template(
        'admin_dashboard.html',
        total_products    = total_products,
        total_journals    = total_journals,
        total_sales       = sales,
        total_transactions = total_transactions
    )

# =========================
# LOGOUT ADMIN
# =========================
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# =========================
# PRODUK ADMIN
# =========================
@app.route('/admin/products')
def admin_products():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

# =========================
# TAMBAH PRODUK
# =========================
@app.route('/admin/products/add', methods=['GET', 'POST'])
def add_product():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        name  = request.form['name']
        price = request.form['price']
        cost  = request.form['cost']
        stock = request.form.get('stock', 0)

        image_file = request.files.get('image')
        image_path = None

        if image_file and image_file.filename != '':
            filename   = secure_filename(image_file.filename)
            image_path = f'uploads/{filename}'
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.session.add(Product(name=name, price=price, cost=cost, stock=stock, image=image_path))
        db.session.commit()
        return redirect(url_for('admin_products'))

    return render_template('add_product.html')

# =========================
# EDIT PRODUK
# =========================
@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    product = Product.query.get(id)

    if request.method == 'POST':
        product.name  = request.form['name']
        product.price = request.form['price']
        product.cost  = request.form['cost']
        product.stock = request.form.get('stock', product.stock)

        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename      = secure_filename(image_file.filename)
            image_path    = f'uploads/{filename}'
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product.image = image_path

        db.session.commit()
        return redirect(url_for('admin_products'))

    return render_template('edit_product.html', product=product)

# =========================
# HAPUS PRODUK
# =========================
@app.route('/admin/products/delete/<int:id>')
def delete_product(id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    product = Product.query.get(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin_products'))

# =========================
# NERACA SALDO
# =========================
@app.route('/trial-balance')
def trial_balance():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    journals     = Journal.query.all()
    accounts     = {}
    total_debit  = 0
    total_credit = 0

    for j in journals:
        if j.account not in accounts:
            accounts[j.account] = {'debit': 0, 'credit': 0}
        accounts[j.account]['debit']  += j.debit
        accounts[j.account]['credit'] += j.credit
        total_debit  += j.debit
        total_credit += j.credit

    return render_template('trial_balance.html', accounts=accounts, total_debit=total_debit, total_credit=total_credit)

# =========================
# LABA RUGI
# =========================
@app.route('/income-statement')
def income_statement():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    journals = Journal.query.all()
    revenue  = 0
    hpp      = 0

    for j in journals:
        if j.account == 'Penjualan':
            revenue += j.credit
        if j.account == 'HPP':
            hpp += j.debit

    # modal awal
    total_modal = sum(m.amount for m in ModalAwal.query.all())
    profit      = revenue - hpp - total_modal

    return render_template('income_statement.html', revenue=revenue, hpp=hpp, total_modal=total_modal, profit=profit)

# =========================
# JURNAL PENUTUP
# =========================
@app.route('/closing-entry')
def closing_entry():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    revenue = 0
    for j in Journal.query.all():
        if j.account == 'Penjualan':
            revenue += j.credit

    closing_entries = [
        {'account': 'Penjualan',          'debit': revenue, 'credit': 0},
        {'account': 'Ikhtisar Laba Rugi', 'debit': 0,       'credit': revenue}
    ]

    return render_template('closing_entry.html', closing_entries=closing_entries, revenue=revenue)

# =========================
# MODAL AWAL
# =========================
@app.route('/admin/modal', methods=['GET', 'POST'])
def admin_modal():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        amount      = int(request.form['amount'])
        description = request.form.get('description', '')
        db.session.add(ModalAwal(amount=amount, description=description))
        db.session.commit()
        return redirect(url_for('admin_modal'))

    modals      = ModalAwal.query.order_by(ModalAwal.date.desc()).all()
    total_modal = sum(m.amount for m in modals)
    return render_template('admin_modal.html', modals=modals, total_modal=total_modal)

# =========================
# EXPORT PDF
# =========================
@app.route('/export-pdf')
def export_pdf():
    pdf_path = "laporan.pdf"
    c = canvas.Canvas(pdf_path)
    c.drawString(100, 800, "Laporan The Avocados")
    c.drawString(100, 780, "Penjualan dan Keuangan")
    c.save()
    return send_file(pdf_path, as_attachment=True)

# =========================
# RUN
# =========================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)