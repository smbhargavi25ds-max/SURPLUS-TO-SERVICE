import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'surplus_to_service_secret_key_change_in_production')

# ─── DATABASE SETTINGS (MySQL via SQLAlchemy) ──────────────────────────
# If a DATABASE_URL environment variable is found (like on Render), it uses that.
# Otherwise, it automatically falls back to your local MySQL environment configuration parameters.
LOCAL_MYSQL_URI = 'mysql+pymysql://root:Smbsmb%402007@localhost:3306/surplus_service'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', LOCAL_MYSQL_URI)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── CIRCULAR ECOSYSTEM RULES MAPPING ──────────────────────────────────
# Auto-enforces: Farmer -> Produce, Restaurant -> Meals, NGO -> Organic Waste, Composter -> Fertilizer
ROLE_CATEGORY_MAPPING = {
    "Farmer": "Produce",
    "Restaurant": "Meals",
    "NGO": "Organic Waste",
    "Composter": "Fertilizer"
}

# ─── DATABASE TABLES SCHEMA (MySQL) ────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Farmer, Restaurant, NGO, Composter
    listings = db.relationship('Listing', backref='author_node', lazy=True)

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Produce, Meals, Organic Waste, Fertilizer
    description = db.Column(db.Text, nullable=False)
    weight = db.Column(db.Float, default=0.0)
    pickup_info = db.Column(db.String(200), default="Available for pickup")
    status = db.Column(db.String(50), default="available") # available, claimed, completed
    location_name = db.Column(db.String(100), default="Main Hub")
    address = db.Column(db.String(200), default="Default Address")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# Auto-create schemas inside your active MySQL Database instance
with app.app_context():
    db.create_all()

# ─── AUTHENTICATION ROUTING SYSTEM ─────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email') or request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.username
            session['user_role'] = user.role
            session['user_email'] = user.email
            flash(f'Welcome back, {user.username} ({user.role})!', 'success')
            return redirect(url_for('home'))
            
        flash('Invalid email/username or password configuration.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # Expects: Farmer, Restaurant, NGO, Composter
        
        if not username or not email or not password or not role:
            flash('Please complete all form fields to register profile node.', 'danger')
            return render_template('register.html')
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email structure already exists.', 'danger')
            return render_template('register.html')
            
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_pw, role=role)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please sign in with your node archetype.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            flash('A recovery token link has been dispatched to your email!', 'success')
            return redirect(url_for('login'))
        flash('Please provide a valid asset identifier email.', 'danger')
    return render_template('forgot_password.html')


# ─── DYNAMIC LOG STORAGE AND EXCHANGE ROUTING ──────────────────────────

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Queries live active postings from database rows instead of hardcoded lists
    db_recent = Listing.query.filter_by(status='available').order_by(Listing.id.desc()).limit(5).all()
    
    # Calculate live application state metrics from the MySQL tables
    total_exchanges = Listing.query.filter(Listing.status.in_(['claimed', 'completed'])).count()
    saved_weight_query = db.session.query(db.func.sum(Listing.weight)).filter_by(status='completed').scalar()
    food_saved = float(saved_weight_query) if saved_weight_query else 0.0
    total_nodes = User.query.count()
    
    return render_template('home.html', recent=db_recent,
                           total_exchanges=total_exchanges,
                           food_saved=round(food_saved, 1),
                           total_nodes=total_nodes,
                           co2_saved=round(food_saved * 2.3, 1))

@app.route('/browse')
def browse():
    category_filter = request.args.get('category', 'all')
    
    if category_filter != 'all':
        listings = Listing.query.filter_by(category=category_filter, status='available').order_by(Listing.id.desc()).all()
    else:
        listings = Listing.query.filter_by(status='available').order_by(Listing.id.desc()).all()
        
    return render_template('browse.html', listings=listings, category=category_filter)

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    listing = Listing.query.get_or_400(listing_id)
    return render_template('listing_detail.html', listing=listing)

@app.route('/claim/<int:listing_id>', methods=['POST'])
def claim(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    listing = Listing.query.get_or_400(listing_id)
    listing.status = 'claimed'
    db.session.commit()
    
    flash('Listing claimed successfully in pipeline!', 'success')
    return redirect(url_for('confirmed', listing_id=listing_id))

@app.route('/confirmed/<int:listing_id>')
def confirmed(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    listing = Listing.query.get_or_400(listing_id)
    return render_template('confirmed.html', listing=listing, exchange=[datetime.utcnow()])

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        weight = float(request.form.get('weight', 0.0) or 0.0)
        pickup_info = request.form.get('pickup_info', 'Pick up anytime')
        location_name = request.form.get('location_name', 'Main Office')
        address = request.form.get('address', 'Ecosystem Center')
        
        # Core Rule Implementation: Pull user role to match their exact target category entry
        user_role = session.get('user_role')
        assigned_category = ROLE_CATEGORY_MAPPING.get(user_role, 'Produce')
        
        if title and description:
            new_listing = Listing(
                title=title,
                category=assigned_category,
                description=description,
                weight=weight,
                pickup_info=pickup_info,
                location_name=location_name,
                address=address,
                user_id=session['user_id']
            )
            db.session.add(new_listing)
            db.session.commit()
            flash(f'Asset log successfully cataloged as {assigned_category} in the network pipeline!', 'success')
            return redirect(url_for('browse'))
            
        flash('Failed to submit post. Please verify all data entry parameters.', 'danger')
        
    return render_template('post.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    
    # Collect data arrays directly scoped to this logged-in account
    active_listings_count = Listing.query.filter_by(user_id=user_id, status='available').count()
    exchanges = Listing.query.filter_by(user_id=user_id).all()
    
    total_posted = Listing.query.filter_by(user_id=user_id).count()
    saved_weight_calc = db.session.query(db.func.sum(Listing.weight)).filter_by(user_id=user_id, status='completed').scalar()
    saved_metric = float(saved_weight_calc) if saved_weight_calc else 0.0
    
    user_data = [
        user_id, 
        session.get('user_name'), 
        session.get('user_email', 'noemail@node.org'), 
        session.get('user_role'), 
        "Active Node Hub"
    ]
    
    return render_template('dashboard.html', exchanges=exchanges,
                           total=total_posted, saved=round(saved_metric, 1),
                           co2=round(saved_metric * 2.3, 1),
                           active_listings=active_listings_count, user=user_data)

@app.route('/complete/<int:exchange_id>')
def complete_exchange(exchange_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    listing = Listing.query.get_or_400(exchange_id)
    listing.status = 'completed'
    db.session.commit()
    
    flash('Exchange successfully logged and closed as completed!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)