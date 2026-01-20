import sqlite3

def migrate():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(articles)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'user_feedback' not in columns:
            print("Adding user_feedback column...")
            cursor.execute("ALTER TABLE articles ADD COLUMN user_feedback INTEGER DEFAULT 0")
            print("Column added successfully.")
        else:
            print("user_feedback column already exists.")
            
    except Exception as e:
        print(f"Error migrating database: {e}")
        conn.rollback()
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    migrate()
