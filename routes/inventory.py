from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db, Product, ProductSale, Student, LedgerTransaction
from routes.auth import admin_required, permission_required
from routes.finance import add_transaction
import nepali_datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def index():
    products = Product.query.all()
    sales = ProductSale.query.order_by(ProductSale.date.desc()).limit(20).all()
    return render_template('inventory/index.html', products=products, sales=sales)

@inventory_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        
        new_product = Product(name=name, price=price, stock=stock)
        db.session.add(new_product)
        db.session.commit()
        flash('Product added to inventory!')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/form.html', product=None)

@inventory_bp.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        db.session.commit()
        flash('Product updated!')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/form.html', product=product)

@inventory_bp.route('/inventory/sell', methods=['GET', 'POST'])
@login_required
def sell():
    products = Product.query.filter(Product.stock > 0).all()
    students = Student.query.filter_by(status='Active').all()
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        student_id = request.form['student_id']
        quantity = int(request.form['quantity'])
        price_sold = float(request.form['price_sold']) # Can be adjusted for discount
        
        product = Product.query.get(product_id)
        if product.stock < quantity:
            flash(f'Not enough stock for {product.name}. Available: {product.stock}', 'danger')
            return redirect(url_for('inventory.sell'))
            
        today_bs = nepali_datetime.date.today().strftime('%Y-%m-%d')
        
        sale = ProductSale(
            product_id=product_id,
            student_id=student_id,
            quantity=quantity,
            price_sold=price_sold,
            date=today_bs
        )
        db.session.add(sale)
        
        # Deduct stock
        product.stock -= quantity
        
        # Charge student ledger
        description_debit = f"Purchase: {product.name} (Qty: {quantity})"
        debit_txn = add_transaction(student_id, description=description_debit, debit=price_sold, credit=0, txn_type='FEE')
        
        # Handle Immediate Payment
        pay_now = request.form.get('pay_now') == 'on'
        credit_txn = None
        if pay_now:
            amount_paid = float(request.form.get('amount_paid', price_sold))
            description_credit = f"Payment for {product.name}"
            credit_txn = add_transaction(student_id, description=description_credit, debit=0, credit=amount_paid, txn_type='PAYMENT')
        
        db.session.commit()
        
        flash(f'Sold {quantity} {product.name} to student.')
        
        # Redirect to receipt if paid now or generic receipt requested
        if pay_now:
             return redirect(url_for('inventory.view_receipt', sale_id=sale.id, txn_id=debit_txn.id))
             
        return redirect(url_for('inventory.index'))
        
    return render_template('inventory/sell.html', products=products, students=students)

@inventory_bp.route('/inventory/receipt/<int:sale_id>')
@login_required
def view_receipt(sale_id):
    sale = ProductSale.query.get_or_404(sale_id)
    student = Student.query.get(sale.student_id)
    product = Product.query.get(sale.product_id)
    
    # Check for linked payment (heuristic: same date, same amount, credit txn)
    # Ideally link them via key, but for now we search for recent credit txn
    payment_txn = LedgerTransaction.query.filter_by(
        student_id=student.id, 
        credit=sale.price_sold, 
        date=sale.date,
        txn_type='PAYMENT'
    ).order_by(LedgerTransaction.id.desc()).first()
    
    return render_template('inventory/receipt.html', sale=sale, student=student, product=product, payment=payment_txn)

@inventory_bp.route('/inventory/delete/<int:id>')
@login_required
@admin_required
def delete(id):
    product = Product.query.get_or_404(id)
    if ProductSale.query.filter_by(product_id=id).first():
        flash('Cannot delete product that has sales records.', 'danger')
        return redirect(url_for('inventory.index'))
        
    db.session.delete(product)
    db.session.commit()
    flash('Product removed from inventory.')
    return redirect(url_for('inventory.index'))
