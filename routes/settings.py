import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from routes.auth import admin_required, permission_required
from werkzeug.utils import secure_filename
from database import db, Settings

settings_bp = Blueprint('settings', __name__)

def get_settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings(academy_name='Dance Academy')
        db.session.add(settings)
        db.session.commit()
    return settings

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_settings')
def index():
    settings = get_settings()
    
    if request.method == 'POST':
        settings.academy_name = request.form.get('academy_name', 'Dance Academy')
        settings.address = request.form.get('address')
        settings.contact = request.form.get('contact')
        settings.default_admission_fee = float(request.form.get('default_admission_fee', 1000.0))
        
        # Handle Logo Upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                
                file.save(os.path.join(upload_path, filename))
                settings.logo_path = f'uploads/{filename}'
        
        db.session.commit()
        flash('Settings updated successfully!')
        return redirect(url_for('settings.index'))
        
    return render_template('settings/index.html', settings=settings)
