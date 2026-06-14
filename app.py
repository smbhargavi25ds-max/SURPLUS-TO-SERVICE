import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import urllib.parse  # Used to safely handle special characters like '@' in database passwords

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# -------------------------------------------------------------------------
# DATABASE CONFIGURATION (Local MySQL vs Live Production Render)
# -------------------------------------------------------------------------
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Modernizes older cloud connection strings automatically to prevent engine crashes
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Safely URL-encodes your password so the '@' doesn't break your local machine path
    encoded_password = urllib.parse.quote_plus("Smbsmb@2007")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{encoded_password}@localhost/surplus_service'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------------------------------------------------------------
# DATABASE MODELS
# -------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Aligned with your local MySQL column name
    role = db.Column(db.String(50), nullable=False, default='farmer')
    location = db.Column(db.String(200), nullable=True)

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    weight = db.Column(db.Float, nullable=False)          
    expires_at = db.Column(db.String(100), nullable=False) 
    pickup_info = db.Column(db.String(100), nullable=False) 
    location_name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)

# -------------------------------------------------------------------------
# APPLICATION ROUTES
# -------------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'farmer')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
            
        # Forces role to lower case to conform to your local MySQL ENUM constraints
        new_user = User(username=username, name=name, email=email, password=password, role=role.lower())
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
        
        # Look up using the column key name matching your database structure
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('browse'))
        flash('Invalid credentials, please try again.', 'danger')
    return render_template('login.html')

@app.route('/browse')
def browse():
    category = request.args.get('category')
    if category:
        listings = Listing.query.filter_by(category=category).all()
    else:
        listings = Listing.query.all()
    return render_template('browse.html', listings=listings, current_category=category)

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        new_listing = Listing(
            title=request.form.get('title'),
            category=request.form.get('category'),
            description=request.form.get('description'),
            weight=float(request.form.get('weight') or 0.0),
            expires_at=request.form.get('expires_at'),
            pickup_info=request.form.get('pickup_preference'),
            location_name=request.form.get('location_name', ''),
            address=request.form.get('address', '')
        )
        db.session.add(new_listing)
        db.session.commit()
        flash('Listing published successfully!', 'success')
        return redirect(url_for('browse'))
    return render_template('post.html')

# Single, unique endpoint route setup - resolves the duplicate mapping AssertionError
@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Correct variable definition resolves Pylance warnings completely
    listing = Listing.query.get_or_404(listing_id)
    return render_template('listing_detail.html', listing=listing)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# -------------------------------------------------------------------------
# STARTUP OPERATION
# -------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
