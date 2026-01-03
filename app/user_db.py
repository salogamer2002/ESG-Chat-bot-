import sqlite3
import os

DB_PATH = "users.db"

def init_db():
    """Initialize database - SIMPLE and RELIABLE"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # FIRST: Drop table completely
        cur.execute("DROP TABLE IF EXISTS users")
        
        # SECOND: Create fresh table with SIMPLE schema
        cur.execute("""
        CREATE TABLE users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            use_case TEXT NOT NULL,
            organization TEXT NOT NULL,
            industry TEXT NOT NULL,
            sector TEXT NOT NULL,
            country TEXT NOT NULL,
            consent INTEGER NOT NULL
        )
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✅ DATABASE RESET: Fresh table created at {os.path.abspath(DB_PATH)}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

def user_exists(email: str) -> bool:
    """Check if user exists"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # First check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cur.fetchone():
            conn.close()
            print("❌ 'users' table doesn't exist!")
            return False
        
        # Check if user exists
        cur.execute("SELECT email FROM users WHERE email = ?", (email,))
        result = cur.fetchone()
        conn.close()
        
        exists = result is not None
        print(f"🔍 User '{email}' exists: {exists}")
        return exists
        
    except Exception as e:
        print(f"❌ Error checking user: {e}")
        return False

def save_user(email: str, name: str, use_case: str, organization: str, 
              industry: str, sector: str, country: str, consent: bool) -> bool:
    """Save user to database"""
    try:
        email = email.lower().strip()
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # First ensure table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cur.fetchone():
            print("❌ Table doesn't exist, creating it...")
            init_db()
        
        # Check if user exists
        cur.execute("SELECT email FROM users WHERE email = ?", (email,))
        exists = cur.fetchone() is not None
        
        if exists:
            # Update
            cur.execute("""
            UPDATE users SET 
                name = ?, use_case = ?, organization = ?, industry = ?,
                sector = ?, country = ?, consent = ?
            WHERE email = ?
            """, (name, use_case, organization, industry, sector, country, 1 if consent else 0, email))
            print(f"📝 Updated existing user: {email}")
        else:
            # Insert
            cur.execute("""
            INSERT INTO users (email, name, use_case, organization, industry, sector, country, consent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (email, name, use_case, organization, industry, sector, country, 1 if consent else 0))
            print(f"✅ Inserted new user: {email}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error saving user {email}: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_user(email: str):
    """Get user details"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return {
                "email": row[0],
                "name": row[1],
                "use_case": row[2],
                "organization": row[3],
                "industry": row[4],
                "sector": row[5],
                "country": row[6],
                "consent": bool(row[7])
            }
        return None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None

def list_users():
    """List all users"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT email, name, organization FROM users")
        users = cur.fetchall()
        conn.close()
        return users
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []

def force_insert_test_user():
    """Force insert a test user - USE THIS TO FIX THE ISSUE"""
    print("🔨 FORCE INSERTING TEST USER...")
    init_db()  # Reset database
    
    success = save_user(
        email="salman.tayyab.kamran@gmail.com",
        name="Muhammad Salman",
        use_case="Academic",
        organization="University",
        industry="Education",
        sector="Higher Education",
        country="Pakistan",
        consent=True
    )
    
    if success:
        print("✅ TEST USER INSERTED SUCCESSFULLY!")
        # Verify
        exists = user_exists("salman.tayyab.kamran@gmail.com")
        print(f"🔍 Verification: User exists = {exists}")
    else:
        print("❌ FAILED TO INSERT TEST USER")
    
    return success

# Aliases for compatibility
insert_user = save_user
upsert_user = save_user

if __name__ == "__main__":
    # Test the database
    print("🧪 TESTING DATABASE FUNCTIONS...")
    print("=" * 50)
    
    # Reset and insert test user
    force_insert_test_user()
    
    # List users
    print("\n👥 ALL USERS IN DATABASE:")
    users = list_users()
    for user in users:
        print(f"   📧 {user[0]} - 👤 {user[1]} - 🏢 {user[2]}")
    
    print("=" * 50)