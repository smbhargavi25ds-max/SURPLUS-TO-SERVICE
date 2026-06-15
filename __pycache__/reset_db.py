from app import app, db

with app.app_context():
    print("Step 1: Dropping outdated database tables...")
    db.drop_all()
    
    print("Step 2: Building fresh tables with all modern form columns...")
    db.create_all()
    
    print("Success! Your database structure matches your code perfectly.")