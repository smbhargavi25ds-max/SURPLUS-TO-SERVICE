from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key_change_in_production')

# Configure database: Uses Render variable if available, otherwise defaults to your local DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'mysql+pymysql://root:Smbsmb@2007@localhost/surplus_service'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── AUTHENTICATION ROUTES ───────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        # Hardcoded verification profile to allow site testing
        if email:
            session['user_id'] = 1
            session['user_name'] = "Test User"
            session['user_role'] = "donor"
            flash('Welcome back, Test User!', 'success')
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── CORE PAGES AND DATA HANDLING ───────────────────────

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', recent=[], total_exchanges=142, food_saved=412.5, total_nodes=24, co2_saved=948.8)

@app.route('/browse')
def browse():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    category = request.args.get('category')
    
    if category and category != 'all':
        query = db.text("SELECT id, title, category, weight, description, pickup_info FROM listing WHERE category = :cat")
        result = db.session.execute(query, {'cat': category})
    else:
        query = db.text("SELECT id, title, category, weight, description, pickup_info FROM listing")
        result = db.session.execute(query)

    listings = result.mappings().all()
    return render_template('browse.html', listings=listings, current_category=category)

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        sql = db.text("""
            INSERT INTO listings (title, category, weight, description, pickup_info) 
            VALUES (:title, :category, :weight, :description, :pickup_info)
        """)
        db.session.execute(sql, {
            'title': request.form.get('title'), 
            'category': request.form.get('category'), 
            'weight': request.form.get('weight'), 
            'description': request.form.get('description'), 
            'pickup_info': request.form.get('pickup_info')
        })
        db.session.commit()
        flash('Listing published!', 'success')
        return redirect(url_for('browse'))
    return render_template('post.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', exchanges=[], total=12, saved=34.5, co2=79.4, active_listings=2)

if __name__ == '__main__':
    app.run(debug=True)