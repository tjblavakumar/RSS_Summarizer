import sqlite3

# Add access_key column to existing feeds table
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE feeds ADD COLUMN access_key VARCHAR(500)")
    print("Added access_key column")
except sqlite3.OperationalError as e:
    print(f"access_key column might already exist: {e}")

conn.commit()
conn.close()
print("Database migration complete")