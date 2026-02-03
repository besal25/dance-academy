from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User

import re

auth_bp = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            flash('Access Denied: Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Admins always have all permissions
            if current_user.role == 'Admin':
                return f(*args, **kwargs)
                
            # Check for specific permission
            if not getattr(current_user, permission_name, False):
                flash(f'Access Denied: You do not have permission to access this feature.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_password(password):
    """
    Rules: 8+ chars, at least one letter and one number.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search("[a-zA-Z]", password) or not re.search("[0-9]", password):
        return False, "Password must contain both letters and numbers."
    return True, ""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if not check_password_hash(current_user.password_hash, old_password):
            flash('Incorrect old password', 'danger')
            return redirect(url_for('auth.change_password'))
            
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('auth.change_password'))
            
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, 'warning')
            return redirect(url_for('auth.change_password'))
            
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('auth/change_password.html')

@auth_bp.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.all()
    return render_template('auth/users.html', users=users)

@auth_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form['username']
    password = request.form['password']
    role = request.form.get('role', 'Staff')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'warning')
        return redirect(url_for('auth.user_list'))
        
    is_valid, message = validate_password(password)
    if not is_valid:
        flash(message, 'warning')
        return redirect(url_for('auth.user_list'))
        
    hashed_pw = generate_password_hash(password)
    new_user = User(
        username=username, 
        password_hash=hashed_pw, 
        role=role,
        can_manage_students = 'can_manage_students' in request.form,
        can_manage_classes = 'can_manage_classes' in request.form,
        can_view_attendance = 'can_view_attendance' in request.form,
        can_view_finance = 'can_view_finance' in request.form,
        can_manage_expenses = 'can_manage_expenses' in request.form,
        can_view_reports = 'can_view_reports' in request.form,
        can_manage_settings = 'can_manage_settings' in request.form
    )
    db.session.add(new_user)
    db.session.commit()
    flash(f'User {username} created with custom permissions!', 'success')
    return redirect(url_for('auth.user_list'))

@auth_bp.route('/users/update_permissions/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_permissions(id):
    user = User.query.get_or_404(id)
    if user.username == 'admin':
        flash('Cannot modify permissions of primary admin', 'danger')
        return redirect(url_for('auth.user_list'))
        
    user.can_manage_students = 'can_manage_students' in request.form
    user.can_manage_classes = 'can_manage_classes' in request.form
    user.can_view_attendance = 'can_view_attendance' in request.form
    user.can_view_finance = 'can_view_finance' in request.form
    user.can_manage_expenses = 'can_manage_expenses' in request.form
    user.can_view_reports = 'can_view_reports' in request.form
    user.can_manage_settings = 'can_manage_settings' in request.form
    
    db.session.commit()
    flash(f'Permissions updated for {user.username}', 'success')
    return redirect(url_for('auth.user_list'))

@auth_bp.route('/users/delete/<int:id>')
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.username == 'admin':
        flash('Cannot delete primary admin', 'danger')
        return redirect(url_for('auth.user_list'))
        
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted.', 'info')
    return redirect(url_for('auth.user_list'))

# Helper to create initial admin user if none exists
def create_admin_user():
    user = User.query.filter_by(username='admin').first()
    if not user:
        hashed_pw = generate_password_hash('admin123')
        new_user = User(
            username='admin', 
            password_hash=hashed_pw, 
            role='Admin',
            can_manage_students=True,
            can_manage_classes=True,
            can_view_attendance=True,
            can_view_finance=True,
            can_manage_expenses=True,
            can_view_reports=True,
            can_manage_settings=True
        )
        db.session.add(new_user)
        db.session.commit()
        print("Admin user created: admin / admin123")
