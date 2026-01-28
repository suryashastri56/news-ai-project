import streamlit as st
import sqlite3
import os
import requests
import base64
from bs4 import BeautifulSoup

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# FIX: Secrets accessed with [] instead of ()
WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
WP_API_URL = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

st.set_page_config(page_title="AI News Admin Pro", layout="wide")

# --- DATABASE AUTO-INIT ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS news_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        title TEXT, raw_content TEXT, rewritten_content TEXT,
        image_url TEXT, seo_description TEXT, seo_tags TEXT, 
        category TEXT, status TEXT DEFAULT 'pending'
    )''')
    conn.commit()
    conn.close()

# Sidebar Controls
with st.sidebar:
    st.header("⚡ Action Center")
    if st.button("📡 Fetch News", width="stretch"): # Updated parameter
        from agents.news_fetcher import fetch_news
        fetch_news()
        st.success("News Fetched!")
        st.rerun()
    
    if st.button("🪄 Rewrite Articles", type="primary", width="stretch"):
        from agents.ai_rewriter import rewrite_news
        rewrite_news()
        st.success("AI Rewriting Done!")
        st.rerun()

init_db() # App start hote hi table ensure karein
st.title("🗞️ AI News Content Manager")

tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with tab1:
        # Table error resolved
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category FROM news_articles WHERE status='pending'")
        posts = cursor.fetchall()
        
        if not posts:
            st.info("Abhi koi pending news nahi hai.")
        
        for pid, title, content, img, desc, tags, cat in posts:
            with st.expander(f"📦 {title}", expanded=True):
                if not content:
                    st.warning("Article abhi rewrite nahi hua hai. Sidebar se 'Rewrite' dabayein.")
                else:
                    # Headline & Body Editor
                    f_title = st.text_input("Headline", value=title, key=f"t{pid}")
                    c1, c2 = st.columns([1, 1.5])
                    with c1:
                        if img: st.image(img, width="stretch") # Updated param
                        f_desc = st.text_area("Meta Description", value=str(desc), key=f"d{pid}")
                    with c2:
                        f_content = st.text_area("Article Body", value=str(content), height=400, key=f"c{pid}")
                        if st.button("🚀 Publish Now", key=f"p{pid}", type="primary"):
                            # WP publish logic...
                            cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                            conn.commit(); st.rerun()
    conn.close()
