from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # DB file will be created
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model (table)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Admin credentials
ADMIN_EMAIL = "admin123@gmail.com"
ADMIN_PASSWORD = "admin"

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not name or not email or not password or not confirm_password:
            flash('Please fill all fields.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session['user'] = user.email
            session['name'] = user.name  # Store the user's name in session
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

# API Routes for Admin
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'email': user.email
    } for user in users])

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email
    })

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        user.password = data['password']
    
    db.session.commit()
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email
    })

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = []
    if os.path.exists('orders.json'):
        with open('orders.json', 'r') as f:
            orders = json.load(f)
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/menu')
@admin_required
def admin_menu():
    menu_items = []
    if os.path.exists('menu.json'):
        with open('menu.json', 'r') as f:
            menu_items = json.load(f)
    return render_template('admin_menu.html', menu_items=menu_items)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if not exist
    app.run(debug=True)
