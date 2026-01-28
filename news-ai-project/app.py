import streamlit as st
import sqlite3
import os
import requests
import base64

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# Secrets (Square brackets fix)
WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
WP_API_URL = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

st.set_page_config(page_title="AI News Admin Pro", layout="wide")

# --- DATABASE FIX: Table ensure karne ke liye logic ---
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

# SIDEBAR
with st.sidebar:
    st.header("⚡ Action Center")
    if st.button("📡 Fetch News", width="stretch"): # Updated parameter
        from agents.news_fetcher import fetch_news
        fetch_news()
        st.success("News Fetched!")
        st.rerun()
    
    if st.button("🪄 AI Rewrite", type="primary", width="stretch"):
        from agents.ai_rewriter import rewrite_news
        rewrite_news()
        st.success("AI Processing Complete!")
        st.rerun()
    
    st.divider()
    if st.button("🛠️ Repair Database", width="stretch"):
        init_db()
        st.sidebar.success("Database Table Created!")

init_db() # Run at startup
st.title("🗞️ AI News Content Manager")

tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with tab1:
        # SQL error fixed by ensuring table existence
        cursor.execute("SELECT id, title, rewritten_content, image_url, category FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        posts = cursor.fetchall()
        
        if not posts:
            st.info("Koi rewritten news nahi hai. Sidebar se trigger karein.")
        
        for pid, title, content, img, cat in posts:
            with st.expander(f"📦 [{cat}] - {title}", expanded=False):
                if content == "Not Generated": # Fix for image_79df3e.png
                    st.warning("AI ne is article ko sahi se parse nahi kiya. Dobara Rewrite karein.")
                else:
                    f_title = st.text_input("Headline", value=title, key=f"t{pid}")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if img: st.image(img, width="stretch") # Updated param
                    with c2:
                        f_content = st.text_area("Content", value=content, height=350, key=f"c{pid}")
                        if st.button("🚀 Publish Now", key=f"p{pid}", type="primary"):
                            # WP publish logic yahan aayegi
                            cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                            conn.commit(); st.rerun()
    conn.close()
