import sqlite3

# Add missing columns to existing articles table
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE articles ADD COLUMN category_name VARCHAR(100)")
    print("Added category_name column")
except sqlite3.OperationalError:
    print("category_name column already exists")

try:
    cursor.execute("ALTER TABLE articles ADD COLUMN category_color VARCHAR(7)")
    print("Added category_color column")
except sqlite3.OperationalError:
    print("category_color column already exists")

conn.commit()
conn.close()
print("Database migration complete")