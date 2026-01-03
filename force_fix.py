import os
import sqlite3

print("🔨 FORCE FIXING DATABASE...")
print("=" * 60)

# 1. Delete old database
db_path = "users.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print("🗑️  Deleted old users.db")

# 2. Create fresh database with correct schema
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Create table with SIMPLE schema (NO created_at)
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

print("✅ Created fresh 'users' table")

# 3. Insert test user directly
test_user = (
    "salman.tayyab.kamran@gmail.com",
    "Muhammad Salman",
    "Academic",
    "University",
    "Education",
    "Higher Education",
    "Pakistan",
    1  # consent = True
)

cur.execute("""
INSERT INTO users (email, name, use_case, organization, industry, sector, country, consent)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", test_user)

conn.commit()

# 4. Verify
cur.execute("SELECT COUNT(*) FROM users")
count = cur.fetchone()[0]

cur.execute("SELECT * FROM users")
users = cur.fetchall()

print(f"📊 Total users: {count}")
print("\n👥 User details:")
for user in users:
    print(f"  📧 Email: {user[0]}")
    print(f"  👤 Name: {user[1]}")
    print(f"  🎯 Use Case: {user[2]}")
    print(f"  🏢 Organization: {user[3]}")
    print(f"  🏭 Industry: {user[4]}")
    print(f"  📋 Sector: {user[5]}")
    print(f"  🌍 Country: {user[6]}")
    print(f"  ✅ Consent: {'Yes' if user[7] else 'No'}")
    print()

conn.close()

print("=" * 60)
print("✅ DATABASE FIXED!")
print("\n📋 SCHEMA VERIFICATION:")
print("Columns in 'users' table: email, name, use_case, organization, industry, sector, country, consent")
print("\n🎯 NEXT STEPS:")
print("1. RESTART the app: chainlit run chainlit_callbacks.py")
print("2. Login with Google")
print("3. Type 'done' in chat")
print("4. Should see: 'Profile verified! Welcome to the ESG Compliance Chatbot'")