import os
import sqlite3
import requests
from bs4 import BeautifulSoup

# --- PATH SETUP ---
# Ye logic dhoondega ki aapka main 'news-ai-project' folder kahan hai
# Aur database.db ko wahi par dhundega/banayega.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def fetch_trending_news():
    print("News dhoondne ka kaam shuru ho raha hai...")
    
    # Google News RSS feed (Technology category - India)
    rss_url = "https://news.google.com/rss/search?q=technology&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        response = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        articles = soup.find_all('item')
        
        # Database se connect karein
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        new_count = 0
        for item in articles[:10]: # Top 10 trending news
            title = item.title.text
            link = item.link.text
            
            # Check karein ki ye news pehle se database mein toh nahi hai
            cursor.execute("SELECT id FROM news_articles WHERE title=?", (title,))
            if not cursor.fetchone():
                # Agar nahi hai, toh insert karein
                cursor.execute("INSERT INTO news_articles (title, raw_content) VALUES (?, ?)", (title, link))
                new_count += 1
                print(f"Added: {title[:50]}...")

        conn.commit()
        conn.close()
        
        if new_count > 0:
            print(f"\nSafalta! {new_count} nayi news database mein save ho gayi hain.")
        else:
            print("\nKoi nayi news nahi mili jo pehle se DB mein na ho.")

    except Exception as e:
        print(f"Error aa gaya: {e}")

if __name__ == "__main__":
    fetch_trending_news()