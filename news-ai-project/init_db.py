import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Pura schema ek sath ensure karein
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            raw_content TEXT,
            rewritten_content TEXT,
            image_url TEXT,
            category TEXT DEFAULT 'General',
            seo_description TEXT,
            seo_tags TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Success! Database with 'category' column is ready.")

if __name__ == "__main__":
    initialize_database()
