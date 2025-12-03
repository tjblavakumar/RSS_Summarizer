import sqlite3

# Add relevancy_score column to existing articles table
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE articles ADD COLUMN relevancy_score INTEGER DEFAULT 0")
    print("Added relevancy_score column")
except sqlite3.OperationalError as e:
    print(f"relevancy_score column might already exist: {e}")

conn.commit()
conn.close()
print("Database migration complete")
