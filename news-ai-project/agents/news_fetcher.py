import sqlite3
import requests
from bs4 import BeautifulSoup
import os
import streamlit as st

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')

def fetch_news():
    st.write("📡 Connecting to Google News RSS...")
    
    # Updated RSS feeds
    sources = {
        "Technology": "https://news.google.com/rss/search?q=technology&hl=en-IN&gl=IN&ceid=IN:en",
        "Business": "https://news.google.com/rss/search?q=business&hl=en-IN&gl=IN&ceid=IN:en",
        "India": "https://news.google.com/rss/search?q=india&hl=en-IN&gl=IN&ceid=IN:en",
        "Sports": "https://news.google.com/rss/search?q=sports&hl=en-IN&gl=IN&ceid=IN:en"
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        new_articles_count = 0

        for category, url in sources.items():
            try:
                response = requests.get(url, timeout=10)
                # Parse with lxml-xml for RSS compatibility
                soup = BeautifulSoup(response.content, 'lxml-xml')
                items = soup.find_all('item')

                for item in items[:10]: # Top 10 articles per category
                    title = item.title.text
                    summary = item.description.text if item.description else "No context found."
                    
                    # Duplicate check
                    cursor.execute("SELECT id FROM news_articles WHERE title = ?", (title,))
                    if not cursor.fetchone():
                        # Category insert karna bahut zaroori hai
                        cursor.execute(
                            "INSERT INTO news_articles (title, raw_content, category, status) VALUES (?, ?, ?, ?)",
                            (title, summary, category, 'pending')
                        )
                        new_articles_count += 1
            except Exception as e:
                st.warning(f"⚠️ {category} fetch fail: {e}")
                continue
        
        conn.commit()
        conn.close()
        return new_articles_count

    except Exception as e:
        st.error(f"❌ Database Error: {e}")
        return 0
