import streamlit as st
import sqlite3
import os
import requests
from bs4 import BeautifulSoup
import base64
import json

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# FIX: Secrets accessed with square brackets
WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
WP_API_URL = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

st.set_page_config(page_title="AI News Admin", layout="wide")

# --- DATABASE FIX: Automatically create table if missing ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS news_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        title TEXT, 
        raw_content TEXT, 
        rewritten_content TEXT,
        image_url TEXT, 
        seo_description TEXT, 
        seo_tags TEXT, 
        category TEXT, 
        status TEXT DEFAULT 'pending'
    )''')
    conn.commit()
    conn.close()

# --- NEWS FETCHER LOGIC ---
def run_fetcher():
    sources = {
        "General": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
        "Technology": "https://news.google.com/rss/search?q=technology&hl=en-IN&gl=IN&ceid=IN:en"
    }
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    new_count = 0
    for cat, url in sources.items():
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.content, 'lxml-xml')
            for item in soup.find_all('item')[:10]:
                title = item.title.text
                cursor.execute("SELECT id FROM news_articles WHERE title=?", (title,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO news_articles (title, raw_content, status) VALUES (?, ?, ?)", 
                                   (title, item.description.text, 'pending'))
                    new_count += 1
        except: continue
    conn.commit()
    conn.close()
    return new_count

# --- UI START ---
init_db() # Ensure table exists
st.title("🤖 AI News Content Manager")

# Sidebar for manual controls
with st.sidebar:
    st.header("Admin Controls")
    if st.button("🔄 Fetch New News", use_container_width=True):
        with st.spinner("Fetching..."):
            count = run_fetcher()
            st.success(f"{count} naye articles mile!")
            st.rerun()
        
with st.sidebar:
    st.header("Admin Controls")
    # ... (Fetch News Button) ...
    if st.button("🪄 Rewrite All Pending", use_container_width=True):
        with st.spinner("AI is rewriting articles... Please wait."):
            # Yahan ai_rewriter ka function call hoga
            from agents.ai_rewriter import rewrite_news
            rewrite_news()
            st.success("Articles Rewritten! Refreshing...")
            st.rerun()

tab1, tab2, tab3 = st.tabs(["⏳ Pending Articles", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with tab1:
        # SQL error fixed by verifying table
        cursor.execute("SELECT id, title, rewritten_content, category FROM news_articles WHERE status='pending'")
        posts = cursor.fetchall()
        
        if not posts:
            st.info("Abhi koi news nahi hai. Sidebar se 'Fetch' button dabayein.")
        
        for pid, title, content, cat in posts:
            with st.expander(f"📦 {title}"):
                if content:
                    st.write(content)
                else:
                    st.warning("Article abhi rewrite nahi hua hai. ai_rewriter.py chalayein.")
                
                if st.button("Reject", key=f"r{pid}"):
                    cursor.execute("UPDATE news_articles SET status='rejected' WHERE id=?", (pid,))
                    conn.commit()
                    st.rerun()
    conn.close()
