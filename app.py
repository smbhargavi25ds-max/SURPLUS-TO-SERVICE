import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# This is the single source of truth for your DB
database_url = os.environ.get('DATABASE_URL')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-key')  # Ensure you set this in production

if not database_url:
    # Fallback to local only if absolutely necessary
    database_url = 'mysql+pymysql://SM Bhargavi:Smbsmb@2007@localhost/surplus_service'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
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
        # Simple test logic for demonstration
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

# Add these routes to your app.py to prevent BuildErrors
@app.route('/forgot-password')
def forgot_password():
    return "Recovery coming soon!"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Dummy data to ensure the dashboard renders while you build the DB logic
    return render_template('dashboard.html', 
                           exchanges=[], 
                           total=0, 
                           saved=0.0, 
                           co2=0.0, 
                           active_listings=0)

if __name__ == '__main__':
    # Get the port from the environment variable provided by Railway
    # Default to 5000 if no port is provided (for local testing)
    port = int(os.environ.get("PORT", 5000))
    
    # Listen on all available network interfaces (0.0.0.0)
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    app.run(debug=True)