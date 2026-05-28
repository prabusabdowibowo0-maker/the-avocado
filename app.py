from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from reportlab.pdfgen import canvas
from flask import send_file

# bikin aplikasi flask
app = Flask(__name__)
app.secret_key = 'theavocados'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# konfigurasi database sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# koneksi database
db = SQLAlchemy(app)

# buat folder uploads kalau belum ada

# =========================
# TABEL PRODUCT
# =========================
class Product(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    price = db.Column(db.Integer)

    cost = db.Column(db.Integer)

    image = db.Column(db.String(500))

# =========================
# TABEL JURNAL UMUM
# =========================
class Journal(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    account = db.Column(db.String(100))

    debit = db.Column(db.Integer)

    credit = db.Column(db.Integer)

    description = db.Column(db.String(200))

# =========================
# HALAMAN HOME
# =========================
@app.route('/')
def home():

    # ambil semua data produk
    products = Product.query.all()

    # kirim ke html
    return render_template('index.html', products=products)

# =========================
# TAMBAH KE KERANJANG
# =========================
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):

    product = Product.query.get(id)

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']

    found = False

    # cek apakah produk sudah ada
    for item in cart:

        if item['id'] == product.id:

            item['quantity'] += 1

            found = True

            break

    # kalau belum ada
    if not found:

        cart.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'cost': product.cost,
            'image': product.image,
            'quantity': 1
        })

    session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': len(session['cart'])})

    return redirect(url_for('home'))

# =========================
# HALAMAN CART
# =========================
@app.route('/cart')
def cart():

    cart = session.get('cart', [])

    total = sum(item['price'] * item['quantity'] for item in cart)

    return render_template(
        'cart.html',
        cart_items=cart,
        total=total
    )

# =========================
# HAPUS ITEM CART
# =========================
@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):

    cart = session.get('cart', [])

    new_cart = []

    for item in cart:

        if item['id'] != id:
            new_cart.append(item)

    session['cart'] = new_cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        total = sum(item['price'] * item['quantity'] for item in new_cart)
        return jsonify({'success': True, 'cart_count': len(new_cart), 'total': total})

    return redirect(url_for('cart'))

# =========================
# TAMBAH QUANTITY
# =========================
@app.route('/increase_quantity/<int:id>')
def increase_quantity(id):

    cart = session.get('cart', [])

    for item in cart:

        if item['id'] == id:
            item['quantity'] += 1

    session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item_data = next((i for i in cart if i['id'] == id), None)
        total = sum(i['price'] * i['quantity'] for i in cart)
        return jsonify({
            'success': True,
            'quantity': item_data['quantity'] if item_data else 0,
            'subtotal': item_data['price'] * item_data['quantity'] if item_data else 0,
            'total': total,
            'cart_count': len(cart)
        })

    return redirect(url_for('cart'))

# =========================
# KURANGI QUANTITY
# =========================
@app.route('/decrease_quantity/<int:id>')
def decrease_quantity(id):

    cart = session.get('cart', [])

    for item in cart:

        if item['id'] == id:

            item['quantity'] -= 1

            # kalau quantity 0 hapus
            if item['quantity'] <= 0:
                cart.remove(item)

            break

    session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item_data = next((i for i in cart if i['id'] == id), None)
        total = sum(i['price'] * i['quantity'] for i in cart)
        return jsonify({
            'success': True,
            'quantity': item_data['quantity'] if item_data else 0,
            'removed': item_data is None,
            'subtotal': item_data['price'] * item_data['quantity'] if item_data else 0,
            'total': total,
            'cart_count': len(cart)
        })

    return redirect(url_for('cart'))

# =========================
# CHECKOUT
# =========================
@app.route('/checkout')
def checkout():

    cart = session.get('cart', [])

    total = sum(item['price'] * item['quantity'] for item in cart)

    return render_template(
        'checkout.html',
        cart=cart,
        total=total
    )

# =========================
# RECEIPT + JURNAL
# =========================
@app.route('/receipt/<payment>')
def receipt(payment):

    cart = session.get('cart', [])

    total = sum(item['price'] * item['quantity'] for item in cart)

    # =========================
    # JURNAL PENJUALAN
    # =========================

    debit_journal = Journal(
        account='Kas',
        debit=total,
        credit=0,
        description='Transaksi Penjualan'
    )

    credit_journal = Journal(
        account='Penjualan',
        debit=0,
        credit=total,
        description='Transaksi Penjualan'
    )

    db.session.add(debit_journal)
    db.session.add(credit_journal)

    # =========================
    # JURNAL HPP
    # =========================

    total_hpp = 0

    for item in cart:

        product = Product.query.get(item['id'])

        total_hpp += product.cost * item['quantity']

    hpp_journal = Journal(
        account='HPP',
        debit=total_hpp,
        credit=0,
        description='Harga Pokok Penjualan'
    )

    inventory_journal = Journal(
        account='Persediaan',
        debit=0,
        credit=total_hpp,
        description='Pengurangan Persediaan'
    )

    db.session.add(hpp_journal)
    db.session.add(inventory_journal)

    db.session.commit()

    # simpan cart untuk ditampilkan di receipt
    cart_display = list(cart)

    # clear cart setelah transaksi berhasil
    session['cart'] = []

    return render_template(
        'receipt.html',
        cart=cart_display,
        total=total,
        payment=payment
    )

# =========================
# HALAMAN JURNAL UMUM
# =========================
@app.route('/journal')
def journal():

    # cek login
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    journals = Journal.query.all()

    return render_template(
        'journal.html',
        journals=journals
    )


# =========================
# HALAMAN BUKU BESAR
# =========================
@app.route('/ledger')
def ledger():

    # cek login
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    journals = Journal.query.all()

    ledger_data = {}

    for journal in journals:

        account = journal.account

        # kalau akun belum ada
        if account not in ledger_data:

            ledger_data[account] = {
                'debit': 0,
                'credit': 0
            }

        ledger_data[account]['debit'] += journal.debit
        ledger_data[account]['credit'] += journal.credit

    return render_template(
        'ledger.html',
        ledger_data=ledger_data
    )

# =========================
# LOGIN ADMIN
# =========================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # login sederhana
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

    total_products = Product.query.count()

    total_journals = Journal.query.count()

    # total penjualan
    sales = 0

    journals = Journal.query.all()

    for journal in journals:

        if journal.account == 'Penjualan':

            sales += journal.credit

    return render_template(
        'admin_dashboard.html',
        total_products=total_products,
        total_journals=total_journals,
        sales=sales
    )

# =========================
# LOGOUT ADMIN
# =========================
@app.route('/admin/logout')
def admin_logout():

    # hapus session admin
    session.pop('admin', None)

    return redirect(url_for('admin_login'))

# =========================
# HALAMAN PRODUK ADMIN
# =========================
@app.route('/admin/products')
def admin_products():

    if 'admin' not in session:

        return redirect(url_for('admin_login'))

    products = Product.query.all()

    return render_template(
        'admin_products.html',
        products=products
    )

# =========================
# TAMBAH PRODUK
# =========================
@app.route('/admin/products/add', methods=['GET', 'POST'])
def add_product():

    if 'admin' not in session:

        return redirect(url_for('admin_login'))

    if request.method == 'POST':

        name = request.form['name']

        price = request.form['price']

        cost = request.form['cost']

        image_file = request.files['image']

        filename = secure_filename(image_file.filename)

        image_path = f'uploads/{filename}'

        image_file.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

        new_product = Product(
            name=name,
            price=price,
            cost=cost,
            image=image_path
        )

        db.session.add(new_product)

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

        product.name = request.form['name']
        product.price = request.form['price']
        product.cost = request.form['cost']

        image_file = request.files.get('image')

        # hanya update gambar kalau ada file baru yang diupload
        if image_file and image_file.filename != '':

            filename = secure_filename(image_file.filename)

            image_path = f'uploads/{filename}'

            image_file.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
                )
            )

            product.image = image_path

        db.session.commit()

        return redirect(url_for('admin_products'))

    return render_template(
        'edit_product.html',
        product=product
    )

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

    journals = Journal.query.all()

    accounts = {}

    total_debit = 0
    total_credit = 0

    for journal in journals:

        account = journal.account

        if account not in accounts:

            accounts[account] = {
                'debit': 0,
                'credit': 0
            }

        accounts[account]['debit'] += journal.debit
        accounts[account]['credit'] += journal.credit

        total_debit += journal.debit
        total_credit += journal.credit

    return render_template(
        'trial_balance.html',
        accounts=accounts,
        total_debit=total_debit,
        total_credit=total_credit
    )

# =========================
# LABA RUGI
# =========================
@app.route('/income-statement')
def income_statement():

    if 'admin' not in session:

        return redirect(url_for('admin_login'))

    journals = Journal.query.all()

    revenue = 0
    hpp = 0

    for journal in journals:

        if journal.account == 'Penjualan':

            revenue += journal.credit

        if journal.account == 'HPP':

            hpp += journal.debit

    profit = revenue - hpp

    return render_template(
        'income_statement.html',
        revenue=revenue,
        hpp=hpp,
        profit=profit
    )

# =========================
# JURNAL PENUTUP
# =========================
@app.route('/closing-entry')
def closing_entry():

    if 'admin' not in session:

        return redirect(url_for('admin_login'))

    journals = Journal.query.all()

    revenue = 0

    # hitung total penjualan
    for journal in journals:

        if journal.account == 'Penjualan':

            revenue += journal.credit

    closing_entries = []

    # jurnal penutup
    closing_entries.append({
        'account': 'Penjualan',
        'debit': revenue,
        'credit': 0
    })

    closing_entries.append({
        'account': 'Ikhtisar Laba Rugi',
        'debit': 0,
        'credit': revenue
    })

    return render_template(
        'closing_entry.html',
        closing_entries=closing_entries,
        revenue=revenue
    )

#==========================
# EXPORT DATA JURNAL KE PDF
#==========================
@app.route('/export-pdf')
def export_pdf():

    pdf_path = "laporan.pdf"

    c = canvas.Canvas(pdf_path)

    c.drawString(100, 800, "Laporan The Avocados")

    c.drawString(100, 780, "Penjualan dan Keuangan")

    c.save()

    return send_file(pdf_path,
                     as_attachment=True)

# =========================
# JALANKAN APP
# =========================
if __name__ == '__main__':

    # bikin database + tabel
    with app.app_context():

        db.create_all()

        # kalau database kosong
        if Product.query.count() == 0:

            # tambah data produk
            product1 = Product(
                name='Alpukat Premium',
                price=25000,
                cost=15000,
                image=None
            )

            product2 = Product(
                name='Pupuk Organik',
                price=50000,
                cost=30000,
                image=None
            )

            # simpan data
            db.session.add(product1)
            db.session.add(product2)

            db.session.commit()

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)