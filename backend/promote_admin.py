import sys
import os
from sqlalchemy import text

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.database import engine, get_db
from app.models.user import User

def promote_to_superuser(email, password=None):
    print(f"Promoting {email} to Super Admin...")
    
    # Check if table has is_superuser and password_hash columns
    with engine.connect() as conn:
        try:
            # Force migration logic for is_superuser
            conn.execute(text("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT 0"))
        except Exception:
            pass 
        
        try:
            # Force migration logic for password_hash
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash TEXT"))
        except Exception:
            pass 
            
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        if not password:
            print(f"User {email} not found! Provide a password to create the account.")
            return
        print(f"Creating new user {email}...")
        user = User(
            id=User.generate_id(),
            email=email
        )
        db.add(user)
    
    if password:
        user.set_password(password)
        print("Password updated.")
        
    user.is_superuser = True
    db.commit()
    print(f"SUCCESS: {email} is now a Super Admin and can see all tokens.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_admin.py <email> [password]")
    else:
        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else None
        promote_to_superuser(email, password)
