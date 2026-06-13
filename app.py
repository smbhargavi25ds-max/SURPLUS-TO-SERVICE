from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'surplus_to_service_temporary_key_2026')

# Baseline mockup grid data configured to align perfectly with browse loops
MOCK_LISTINGS = [
    [1, 1, "Produce", "Organic Carrots & Greens Baskets", 25.5, datetime.now(), "Pick up before 6 PM", "available", "Bengaluru Eco Hub", "Bengaluru Central"],
    [2, 1, "Bakery", "Sourdough & Whole Wheat Batches", 12.0, datetime.now(), "Available all afternoon", "available", "Bakehouse B", "Bengaluru West"],
    [3, 1, "Meals", "Vegan Lentil Stew Packs", 45.0, datetime.now(), "Freshly frozen", "available", "Community Kitchen", "Bengaluru Central"]
]

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username') or request.form.get('email')
        if username:
            session['user_id'] = 1
            session['username'] = username.split('@')[0].title()
            session['user_role'] = "donor"
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/home')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/browse')
def browse():
    if 'user_id' not in session: return redirect(url_for('login'))
    category = request.args.get('category', 'all')
    return render_template('browse.html', listings=MOCK_LISTINGS, category=category)

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        return redirect(url_for('browse'))
    return render_template('post.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    exchanges = [[1, None, None, None, None, "completed", "Organic Carrots", "Produce", "Kitchen", "Hub"]]
    user = [1, session.get('username', 'Test User'), "user@network.org", "donor", "Central Hub"]
    return render_template('dashboard.html', exchanges=exchanges, total=1, saved=15.0, co2=37.5, active_listings=1, user=user)

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    listing = [listing_id, 1, "Produce", "Organic Carrots", 25.5, datetime.now(), "Fast pick up", "available", "Eco Hub", "Central", "hub@net.org"]
    return render_template('listing_detail.html', listing=listing)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)