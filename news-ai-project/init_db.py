import sqlite3
import os

# Database path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def initialize_database():
    # Database connection setup
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🚀 Database initialize ho raha hai...")

    # Table structure with Category and SEO columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            raw_content TEXT,            -- Fetcher se aane wala raw content
            rewritten_content TEXT,      -- AI dwara likha gaya English content
            image_url TEXT,              -- AI image link
            category TEXT DEFAULT 'General', -- News ki category (Tech, Sports, etc.)
            seo_description TEXT,        -- Meta description for SEO
            seo_tags TEXT,               -- Keywords/Tags
            status TEXT DEFAULT 'pending' -- Article status (pending, published, rejected)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Success! Updated Database Schema taiyar hai yahan: {DB_PATH}")

if __name__ == "__main__":
    # Naye schema ko apply karne ke liye purani file delete karna behtar hai
    if os.path.exists(DB_PATH):
        print("Purana database mila. Schema update (Category add) karne ke liye naya start kar rahe hain.")
    
    initialize_database()
