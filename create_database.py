import sqlite3
import os

DB_PATH = "users.db"

def init_db():
    """Initialize database"""
    try:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            use_case TEXT NOT NULL,
            organization TEXT NOT NULL,
            industry TEXT NOT NULL,
            sector TEXT NOT NULL,
            country TEXT NOT NULL,
            consent BOOLEAN NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at: {os.path.abspath(DB_PATH)}")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def insert_test_user():
    """Insert a test user directly into the database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # First check if user exists
        cur.execute("SELECT email FROM users WHERE email = ?", ("salman.tayyab.kamran@gmail.com",))
        if cur.fetchone():
            print("✅ User already exists in database")
            return True
        
        # Insert test user
        cur.execute("""
        INSERT INTO users (email, name, use_case, organization, industry, sector, country, consent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "salman.tayyab.kamran@gmail.com",
            "Muhammad Salman",
            "Academic",
            "University",
            "Education",
            "Higher Education",
            "Pakistan",
            1  # consent = True
        ))
        
        conn.commit()
        print("✅ Test user inserted successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        conn.close()

def check_users():
    """Check all users in database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cur.fetchone():
            print("❌ 'users' table doesn't exist!")
            return
        
        # Count users
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        print(f"👥 Total users in database: {count}")
        
        # List all users
        cur.execute("SELECT email, name, organization, created_at FROM users")
        users = cur.fetchall()
        
        for user in users:
            print(f"   📧 Email: {user[0]}")
            print(f"   👤 Name: {user[1]}")
            print(f"   🏢 Organization: {user[2]}")
            print(f"   📅 Created: {user[3]}")
            print()
            
    except sqlite3.Error as e:
        print(f"❌ Error checking users: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 Testing Database...")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    # Insert test user
    print("\n📝 Inserting test user...")
    insert_test_user()
    
    # Check users
    print("\n🔍 Checking database contents...")
    check_users()
    
    print("=" * 50)
    print("✅ Test complete! Now start the app and type 'done' in chat.")