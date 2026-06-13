# SURPLUS TO SERVICE — Circular Resource Network

A full-stack web app connecting farmers, restaurants, NGOs, and composters
to share surplus food and close the resource loop.

---

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Frontend   | HTML + CSS + Bootstrap 5|
| Backend    | Flask (Python)          |
| Database   | MySQL                   |
| IDE        | VS Code                 |

---

## Project Structure

```
SURPLUS TO SERVICE/
├── app.py                    ← Flask app & all routes
├── schema.sql                ← MySQL database + tables
├── requirements.txt          ← Python dependencies
├── .vscode/
│   └── launch.json           ← VS Code debug config
├── static/
│   ├── css/style.css         ← Custom styles
│   └── js/main.js            ← Frontend JS
└── templates/
    ├── base.html             ← Navbar + layout shell
    ├── login.html            ← Login page
    ├── register.html         ← Registration page
    ├── home.html             ← Landing + recent listings
    ├── browse.html           ← All listings + filter
    ├── listing_detail.html   ← Single listing + claim
    ├── confirmed.html        ← Claim success page
    ├── post.html             ← Post surplus form
    └── dashboard.html        ← User profile + history
```

---

## Setup Instructions

### 1. Clone / open in VS Code
Open the `SURPLUS TO SERVICE/` folder in VS Code.

### 2. Create a Python virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up MySQL
Open MySQL Workbench or your terminal and run:
```bash
mysql -u root -p < schema.sql
```
This creates the `surplus_service` database and all tables with sample data.

### 5. Update database credentials in app.py
```python
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'   # ← change this
app.config['MYSQL_DB']       = 'surplus_service'
```

### 6. Run the app
```bash
# Option A — terminal
flask run

# Option B — VS Code
Press F5 (uses .vscode/launch.json)
```

### 7. Open in browser
```
http://localhost:5000
```

---

## Database Tables

### users
| Column     | Type        | Description               |
|------------|-------------|---------------------------|
| id         | INT PK      | Auto-increment            |
| name       | VARCHAR     | Full name / org name      |
| email      | VARCHAR     | Unique login email        |
| role       | ENUM        | farmer/restaurant/ngo/…   |
| password   | VARCHAR     | Hashed (Werkzeug)         |
| location   | VARCHAR     | City / area               |
| created_at | TIMESTAMP   | Auto                      |

### listings
| Column      | Type      | Description               |
|-------------|-----------|---------------------------|
| id          | INT PK    | Auto-increment            |
| user_id     | FK        | References users.id       |
| category    | ENUM      | produce/cooked/compost/…  |
| description | VARCHAR   | What's being offered      |
| quantity_kg | DECIMAL   | Amount in kg              |
| expires_at  | DATETIME  | When it expires           |
| pickup_pref | ENUM      | self_collect/i_deliver/…  |
| status      | ENUM      | available/claimed/expired |
| created_at  | TIMESTAMP | Auto                      |

### exchanges
| Column       | Type      | Description               |
|--------------|-----------|---------------------------|
| id           | INT PK    | Auto-increment            |
| listing_id   | FK        | References listings.id    |
| donor_id     | FK        | References users.id       |
| recipient_id | FK        | References users.id       |
| pickup_time  | VARCHAR   | Agreed time               |
| quantity_kg  | DECIMAL   | Amount exchanged          |
| status       | ENUM      | pending/completed/…       |
| created_at   | TIMESTAMP | Auto                      |

---

## Pages & Routes

| Route                    | Method    | Page                  |
|--------------------------|-----------|-----------------------|
| `/`                      | GET       | Redirect to home/login|
| `/login`                 | GET, POST | Login page            |
| `/register`              | GET, POST | Register page         |
| `/logout`                | GET       | Clear session         |
| `/home`                  | GET       | Dashboard home        |
| `/browse`                | GET       | All listings          |
| `/listing/<id>`          | GET       | Listing detail        |
| `/claim/<id>`            | POST      | Claim a listing       |
| `/confirmed/<id>`        | GET       | Claim confirmation    |
| `/post`                  | GET, POST | Post surplus form     |
| `/dashboard`             | GET       | User dashboard        |
| `/complete/<exchange_id>`| GET       | Mark exchange done    |

---

## User Flow

```
Register → Login → Home
                    ├── Browse listings → View listing → Claim → Confirmed
                    ├── Post surplus → Publish → visible to others
                    └── Dashboard → view exchanges → mark done
```

---

## VS Code Extensions (recommended)
- Python (Microsoft)
- Pylance
- Flask Snippets
- MySQL (weijan chen)
- HTML CSS Support
- Prettier
