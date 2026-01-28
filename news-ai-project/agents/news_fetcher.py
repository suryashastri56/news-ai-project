import sqlite3
import requests
from bs4 import BeautifulSoup
import os
import streamlit as st

# Absolute path ensure karne ke liye
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')

def fetch_news():
    # RSS Sources
    sources = {
        "Technology": "https://news.google.com/rss/search?q=technology&hl=en-IN&gl=IN&ceid=IN:en",
        "Business": "https://news.google.com/rss/search?q=business&hl=en-IN&gl=IN&ceid=IN:en",
        "India": "https://news.google.com/rss/search?q=india&hl=en-IN&gl=IN&ceid=IN:en"
    }
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    new_count = 0
    
    for category, url in sources.items():
        try:
            response = requests.get(url, timeout=10)
            # RSS ke liye 'lxml-xml' sabase best hai
            soup = BeautifulSoup(response.content, 'lxml-xml')
            items = soup.find_all('item')
            
            for item in items[:10]:
                title = item.title.text
                summary = item.description.text if item.description else "No Content"
                
                # Check if news already exists
                cursor.execute("SELECT id FROM news_articles WHERE title=?", (title,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO news_articles (title, raw_content, category, status) VALUES (?, ?, ?, ?)",
                        (title, summary, category, 'pending')
                    )
                    new_count += 1
        except Exception as e:
            st.error(f"Error fetching {category}: {e}")
            
    conn.commit()
    conn.close()
    return new_count
