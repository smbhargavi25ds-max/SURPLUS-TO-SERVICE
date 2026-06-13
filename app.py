from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'surplus_to_service_secret_key_change_in_production'

# MySQL config — update with your credentials
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Smbsmb@2007'
app.config['MYSQL_DB'] = 'surplus_service'

mysql = MySQL(app)

# ─── AUTH ───────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[4], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[3]
            flash('Welcome back, ' + user[1] + '!', 'success')
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        location = request.form['location']
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO users (name, email, role, password, location) VALUES (%s, %s, %s, %s, %s)",
                (name, email, role, password, location)
            )
            mysql.connection.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Email already registered.', 'danger')
        finally:
            cur.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── MAIN PAGES ─────────────────────────────────────────

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT l.*, u.name, u.location FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.status = 'available' AND l.expires_at > NOW()
        ORDER BY l.created_at DESC LIMIT 3
    """)
    recent = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM exchanges WHERE status='completed'")
    total_exchanges = cur.fetchone()[0]
    cur.execute("SELECT SUM(quantity_kg) FROM exchanges WHERE status='completed'")
    food_saved = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(DISTINCT id) FROM users")
    total_nodes = cur.fetchone()[0]
    cur.close()
    return render_template('home.html', recent=recent,
                           total_exchanges=total_exchanges,
                           food_saved=round(food_saved, 1),
                           total_nodes=total_nodes,
                           co2_saved=round(food_saved * 2.3, 1))

@app.route('/browse')
def browse():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    category = request.args.get('category', 'all')
    cur = mysql.connection.cursor()
    if category == 'all':
        cur.execute("""
            SELECT l.*, u.name, u.location FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.status = 'available' AND l.expires_at > NOW()
            ORDER BY l.created_at DESC
        """)
    else:
        cur.execute("""
            SELECT l.*, u.name, u.location FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.status = 'available' AND l.category = %s AND l.expires_at > NOW()
            ORDER BY l.created_at DESC
        """, (category,))
    listings = cur.fetchall()
    cur.close()
    return render_template('browse.html', listings=listings, category=category)

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT l.*, u.name, u.location, u.email FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.id = %s
    """, (listing_id,))
    listing = cur.fetchone()
    cur.close()
    if not listing:
        flash('Listing not found.', 'danger')
        return redirect(url_for('browse'))
    return render_template('listing_detail.html', listing=listing)

@app.route('/claim/<int:listing_id>', methods=['POST'])
def claim(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    pickup_time = request.form['pickup_time']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM listings WHERE id = %s AND status = 'available'", (listing_id,))
    listing = cur.fetchone()
    if not listing:
        flash('Listing no longer available.', 'danger')
        return redirect(url_for('browse'))
    cur.execute("""
        INSERT INTO exchanges (listing_id, donor_id, recipient_id, pickup_time, quantity_kg, status)
        VALUES (%s, %s, %s, %s, %s, 'pending')
    """, (listing_id, listing[1], session['user_id'], pickup_time, listing[4]))
    cur.execute("UPDATE listings SET status = 'claimed' WHERE id = %s", (listing_id,))
    mysql.connection.commit()
    cur.close()
    flash('Listing claimed successfully!', 'success')
    return redirect(url_for('confirmed', listing_id=listing_id))

@app.route('/confirmed/<int:listing_id>')
def confirmed(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT l.*, u.name, u.email, u.location FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.id = %s
    """, (listing_id,))
    listing = cur.fetchone()
    cur.execute("""
        SELECT pickup_time FROM exchanges WHERE listing_id = %s AND recipient_id = %s
    """, (listing_id, session['user_id']))
    exchange = cur.fetchone()
    cur.close()
    return render_template('confirmed.html', listing=listing, exchange=exchange)

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        category = request.form['category']
        description = request.form['description']
        quantity = request.form['quantity']
        expires_at = request.form['expires_at']
        pickup_pref = request.form['pickup_pref']
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO listings (user_id, category, description, quantity_kg, expires_at, pickup_pref, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'available')
        """, (session['user_id'], category, description, quantity, expires_at, pickup_pref))
        mysql.connection.commit()
        cur.close()
        flash('Listing published!', 'success')
        return redirect(url_for('browse'))
    return render_template('post.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    uid = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.*, l.description, l.category,
               r.name as recipient_name, d.name as donor_name
        FROM exchanges e
        JOIN listings l ON e.listing_id = l.id
        JOIN users r ON e.recipient_id = r.id
        JOIN users d ON e.donor_id = d.id
        WHERE e.donor_id = %s OR e.recipient_id = %s
        ORDER BY e.created_at DESC LIMIT 10
    """, (uid, uid))
    exchanges = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM exchanges WHERE donor_id=%s OR recipient_id=%s", (uid, uid))
    total = cur.fetchone()[0]
    cur.execute("SELECT SUM(quantity_kg) FROM exchanges WHERE (donor_id=%s OR recipient_id=%s) AND status='completed'", (uid, uid))
    saved = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM listings WHERE user_id=%s AND status='available'", (uid,))
    active_listings = cur.fetchone()[0]
    cur.execute("SELECT * FROM users WHERE id = %s", (uid,))
    user = cur.fetchone()
    cur.close()
    return render_template('dashboard.html', exchanges=exchanges,
                           total=total, saved=round(saved,1),
                           co2=round(saved*2.3,1),
                           active_listings=active_listings, user=user)

@app.route('/complete/<int:exchange_id>')
def complete_exchange(exchange_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE exchanges SET status='completed' WHERE id=%s AND donor_id=%s",
                (exchange_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Exchange marked as completed!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
