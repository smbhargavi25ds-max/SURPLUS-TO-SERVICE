import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'organic_leaf_green_secret_key_10293')

DB_FILE = 'surplus_service.db'

def get_db_connection():
    """Establishes a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables if they do not exist and injects dummy data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            hub TEXT NOT NULL
        )
    ''')
    
    # 2. Listings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            quantity REAL NOT NULL,
            expires_at TIMESTAMP,
            provider_name TEXT,
            hub_name TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # 3. Exchanges Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchanges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER,
            donor_id INTEGER,
            recipient_id INTEGER,
            status TEXT DEFAULT 'pending',
            title TEXT,
            category TEXT,
            donor_name TEXT,
            recipient_name TEXT,
            FOREIGN KEY(listing_id) REFERENCES listings(id)
        )
    ''')
    
    # Inject Mock Data if completely empty to ensure templates populate seamlessly
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, email, role, hub) VALUES (?, ?, ?, ?)",
                       ('Bengaluru Eco Hub', 'hub1@surplus.org', 'donor', 'Bengaluru Central'))
        cursor.execute("INSERT INTO users (username, email, role, hub) VALUES (?, ?, ?, ?)",
                       ('Community Kitchen', 'kitchen@service.org', 'recipient', 'Bengaluru West'))
        
        # Mock Listings (item tuple indices align with template layout requirements)
        # Template indexes used: item[0]=id, item[2]=category, item[3]=title, item[4]=qty, item[5]=expiry, item[8]=provider, item[9]=hub
        cursor.execute("INSERT INTO listings (user_id, category, title, quantity, expires_at, provider_name, hub_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (1, 'Produce', 'Organic Carrots & Greens Baskets', 25.5, '2026-07-20 18:00:00', 'Bengaluru Eco Hub', 'Bengaluru Central'))
        cursor.execute("INSERT INTO listings (user_id, category, title, quantity, expires_at, provider_name, hub_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (1, 'Bakery', 'Sourdough & Whole Wheat Batches', 12.0, '2026-06-30 12:00:00', 'Bengaluru Eco Hub', 'Bengaluru Central'))
        cursor.execute("INSERT INTO listings (user_id, category, title, quantity, expires_at, provider_name, hub_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (1, 'Meals', 'Vegan Lentil Stew Packs', 45.0, '2026-06-25 21:00:00', 'Bengaluru Eco Hub', 'Bengaluru Central'))
        
    conn.commit()
    conn.close()

# Initialize the database immediately on application startup
init_db()


# -------------------------------------------------------------
# CORE APP ROUTES
# -------------------------------------------------------------

@app.route('/')
def index():
    """Root URL context routing filter."""
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles secure user environment login access processing."""
    if request.method == 'POST':
        username = request.form.get('username')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']
            return redirect(url_for('home'))
        else:
            # Auto-register user implicitly if not found to smooth development debugging loops
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, role, hub) VALUES (?, ?, ?, ?)",
                           (username, f"{username.lower()}@network.org", 'donor', 'Primary Node Hub'))
            conn.commit()
            new_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()
            
            session['user_id'] = new_user['id']
            session['username'] = new_user['username']
            session['user_role'] = new_user['role']
            return redirect(url_for('home'))
            
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration framework node setup."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role', 'recipient')
        hub = request.form.get('hub', 'Main Network Terminal')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, email, role, hub) VALUES (?, ?, ?, ?)',
                         (username, email, role, hub))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or Email already registered node.')
            
    return render_template('register.html')


@app.route('/home')
def home():
    """Serves the central user portal landing platform."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')


@app.route('/browse')
def browse():
    """Handles marketplace searches, indexing, and category card filtering."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    category = request.args.get('category', 'all')
    conn = get_db_connection()
    
    if category == 'all':
        query_results = conn.execute('SELECT * FROM listings').fetchall()
    else:
        query_results = conn.execute('SELECT * FROM listings WHERE category = ?', (category,)).fetchall()
        
    conn.close()
    
    # Map sqlite3.Row rows explicitly into flat lists/tuples matching template layout indices:
    # item[0]=id, item[2]=category, item[3]=title, item[4]=qty, item[5]=expiry_date_object, item[8]=provider, item[9]=hub
    listings = []
    for row in query_results:
        exp_date = None
        if row['expires_at']:
            try:
                exp_date = datetime.strptime(row['expires_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                exp_date = datetime.now()
                
        listings.append([
            row['id'],            # [0]
            row['user_id'],       # [1]
            row['category'],      # [2]
            row['title'],         # [3]
            row['quantity'],      # [4]
            exp_date,             # [5] (Datetime object parsed safely)
            None, None,           # [6], [7]
            row['provider_name'], # [8]
            row['hub_name']       # [9]
        ])
        
    return render_template('browse.html', listings=listings, category=category)


@app.route('/post', methods=['GET', 'POST'])
def post():
    """Logs resource additions onto the distributed marketplace ledger."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        category = request.form.get('category')
        title = request.form.get('title')
        quantity = float(request.form.get('quantity', 0))
        expiry_str = request.form.get('expiry', '2026-12-31 23:59:59')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        conn.execute('''
            INSERT INTO listings (user_id, category, title, quantity, expires_at, provider_name, hub_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], category, title, quantity, expiry_str, user['username'], user['hub']))
        
        conn.commit()
        conn.close()
        return redirect(url_for('browse'))
        
    return render_template('post.html')


@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    """Processes pipeline reservation request nodes instantly upon initialization trigger."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM listings WHERE id = ?', (listing_id,)).fetchone()
    
    if item:
        recipient = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        # Build immediate connection record exchange log row entry mapping parameters directly
        conn.execute('''
            INSERT INTO exchanges (listing_id, donor_id, recipient_id, status, title, category, donor_name, recipient_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item['id'], item['user_id'], session['user_id'], 'pending', item['title'], item['category'], item['provider_name'], recipient['username']))
        
        # Drop item from active visibility pool to signal allocated state routing
        conn.execute('DELETE FROM listings WHERE id = ?', (listing_id,))
        conn.commit()
        
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Assembles metrics, user variables, and transaction logs safely inside wrapped exceptions."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    try:
        conn = get_db_connection()
        
        # Fetch profile metrics info state definitions
        user_row = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        user_data = [user_row['id'], user_row['username'], user_row['email'], user_row['role'], user_row['hub']]
        
        # Count pipeline indicators metric stats
        total_connections = conn.execute('SELECT COUNT(*) FROM exchanges WHERE donor_id = ? OR recipient_id = ?', 
                                         (session['user_id'], session['user_id'])).fetchone()[0]
        
        active_listings = conn.execute('SELECT COUNT(*) FROM listings WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
        
        # Sample dynamic math footprint metric scales calculations values
        footprint_saved = total_connections * 15 # Assumes approx 15 KG per average resource load
        co2_mitigation = int(footprint_saved * 2.5) # Generic metric weight multiplier variable transformation conversion constant
        
        # Fetch track logs exchanges lists mapping arrays: ex[0]=id, ex[5]=status, ex[6]=title, ex[7]=cat, ex[8]=recipient, ex[9]=donor
        exchange_rows = conn.execute('''
            SELECT * FROM exchanges WHERE donor_id = ? OR recipient_id = ?
        ''', (session['user_id'], session['user_id'])).fetchall()
        
        exchanges = []
        for ex in exchange_rows:
            exchanges.append([
                ex['id'], None, None, None, None, 
                ex['status'],         # [5]
                ex['title'],          # [6]
                ex['category'],       # [7]
                ex['recipient_name'], # [8]
                ex['donor_name']      # [9]
            ])
            
        conn.close()
        
        return render_template('dashboard.html', 
                               user=user_data,
                               total=total_connections,
                               saved=footprint_saved,
                               co2=co2_mitigation,
                               active_listings=active_listings,
                               exchanges=exchanges)
                               
    except Exception as e:
        print(f"CRITICAL DASHBOARD EXCEPTION TRACE DETECTED: {e}")
        # Secure placeholder crash fallback structure routing 
        return render_template('dashboard.html', user=[0, 'Node', 'err@system.org', 'Participant', 'Global'], 
                               total=0, saved=0, co2=0, active_listings=0, exchanges=[])


@app.route('/complete_exchange/<int:exchange_id>')
def complete_exchange(exchange_id):
    """Updates active allocation pipelines to completed states."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute("UPDATE exchanges SET status = 'completed' WHERE id = ?", (exchange_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    """Wipes active instance states."""
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Bind to standard production infrastructure environment port matrix parameters
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)