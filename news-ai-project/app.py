import streamlit as st
import sqlite3
import os
import requests
from bs4 import BeautifulSoup
import base64
import json
import time

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# Streamlit Secrets (Corrected Syntax)
WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
WP_API_URL = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

st.set_page_config(page_title="AI News Pro Admin", layout="wide")

# --- DATABASE INITIALIZATION ---
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

# --- SIDEBAR CONTROLS LOGIC ---

def run_fetcher():
    """Google News se articles fetch karna"""
    sources = {
        "Technology": "https://news.google.com/rss/search?q=technology&hl=en-IN&gl=IN&ceid=IN:en",
        "Business": "https://news.google.com/rss/search?q=business&hl=en-IN&gl=IN&ceid=IN:en",
        "India": "https://news.google.com/rss/search?q=india&hl=en-IN&gl=IN&ceid=IN:en"
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
                    cursor.execute("INSERT INTO news_articles (title, raw_content, category, status) VALUES (?, ?, ?, ?)", 
                                   (title, item.description.text, cat, 'pending'))
                    new_count += 1
        except: continue
    conn.commit()
    conn.close()
    return new_count

def run_rewriter():
    """Dashboard se hi AI Rewrite trigger karna"""
    from agents.ai_rewriter import rewrite_news
    rewrite_news()

# --- UI LAYOUT ---
init_db()
st.title("🗞️ AI News Content Manager")

# Sidebar with Action Buttons
with st.sidebar:
    st.header("⚡ Quick Actions")
    
    if st.button("📡 Fetch News", use_container_width=True, help="Google News se naye articles layein"):
        with st.spinner("Fetching..."):
            count = run_fetcher()
            st.success(f"Done! {count} articles mile.")
            st.rerun()

    if st.button("🪄 Rewrite Articles", use_container_width=True, type="primary", help="AI se 300-400 words mein likhwayein"):
        with st.spinner("AI is working... (Rate limit cooldown active)"):
            run_rewriter()
            st.success("Rewriting complete!")
            st.rerun()
            
    st.divider()
    if st.button("🛠️ Repair Database", use_container_width=True):
        init_db()
        st.sidebar.success("Database Fixed!")

# --- MAIN DASHBOARD TABS ---
tab1, tab2, tab3 = st.tabs(["⏳ Pending Articles", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with tab1:
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        posts = cursor.fetchall()
        
        if not posts:
            st.info("Koi rewritten news nahi hai. Sidebar se 'Rewrite' button dabayein.")
        
        for pid, title, content, img, desc, tags, cat in posts:
            with st.container(border=True):
                f_title = st.text_input("Headline", value=title, key=f"t{pid}")
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    if img: st.image(img, use_container_width=True)
                    f_desc = st.text_area("Meta Desc", value=str(desc), key=f"d{pid}")
                    f_tags = st.text_input("Tags", value=str(tags), key=f"tg{pid}")
                with c2:
                    f_content = st.text_area("Body", value=str(content), height=400, key=f"c{pid}")
                    if st.button(f"🚀 Publish Now", key=f"pb{pid}", type="primary"):
                        # (WordPress publishing logic here)
                        cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                        conn.commit(); st.rerun()
    conn.close()
