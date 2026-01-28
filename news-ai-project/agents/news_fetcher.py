import sqlite3
import requests
from bs4 import BeautifulSoup
import os
import streamlit as st

# Path configuration for Streamlit Cloud
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')

def fetch_news():
    st.write("🚀 News fetching shuru ho rahi hai...")
    
    # Diverse news sources
    sources = {
        "General": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
        "Technology": "https://news.google.com/rss/search?q=technology&hl=en-IN&gl=IN&ceid=IN:en",
        "Business": "https://news.google.com/rss/search?q=business&hl=en-IN&gl=IN&ceid=IN:en",
        "Sports": "https://news.google.com/rss/search?q=sports&hl=en-IN&gl=IN&ceid=IN:en",
        "India": "https://news.google.com/rss/search?q=india&hl=en-IN&gl=IN&ceid=IN:en"
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        total_count = 0
        
        for category, url in sources.items():
            st.write(f"📡 Fetching: {category}")
            response = requests.get(url, timeout=10)
            # 'lxml-xml' parser use kiya gaya hai fast processing ke liye
            soup = BeautifulSoup(response.content, 'lxml-xml') 
            items = soup.find_all('item')
            
            for item in items[:10]: # Har category se top 10
                title = item.title.text
                summary = item.description.text if item.description else "No context available"
                
                # Check duplicate title before inserting
                cursor.execute("SELECT id FROM news_articles WHERE title = ?", (title,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO news_articles (title, raw_content, status) VALUES (?, ?, ?)",
                        (title, summary, 'pending')
                    )
                    total_count += 1
        
        conn.commit()
        conn.close()
        st.success(f"✅ SUCCESS: Total {total_count} articles database mein save ho gaye!")
        
    except Exception as e:
        st.error(f"❌ Error during fetching: {e}")

if __name__ == "__main__":
    fetch_news()
