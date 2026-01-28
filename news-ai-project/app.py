import streamlit as st
import sqlite3
import os
import requests
import base64
import time

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# FIX: Secrets accessed with [] brackets
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

def publish_to_wp(title, content, img_url, excerpt, cat_name):
    """Publishing with Error Handling"""
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><div style="text-align:justify">{content.replace("\n", "<br>")}</div>'
    
    # Mapping Category Names to IDs
    mapping = {"Business": 6, "Entertainment": 13, "Health": 14, "Sports": 7, "Technology": 1, "India": 2}
    cat_id = mapping.get(cat_name.strip(), 1)

    post_data = {'title': title, 'content': html_body, 'excerpt': excerpt, 'categories': [cat_id], 'status': 'publish'}
    try:
        r = requests.post(WP_API_URL, headers=headers, json=post_data, timeout=30)
        return r.status_code == 201, r.text
    except Exception as e: return False, str(e)

init_db()
st.title("🤖 AI News Content Manager")

# --- SIDEBAR ACTION CENTER ---
with st.sidebar:
    st.header("⚡ Action Center")
    if st.button("📡 Fetch News", use_container_width=True):
        with st.status("Fetching news..."):
            from agents.news_fetcher import fetch_news
            fetch_news()
            st.success("News Fetched!")
            st.rerun()
    
    if st.button("🪄 AI Rewrite (Cooldown Active)", type="primary", use_container_width=True):
        with st.status("AI Rewriting articles... please wait."):
            from agents.ai_rewriter import rewrite_news
            rewrite_news()
            st.success("Rewriting Complete!")
            st.rerun()

# --- TABS LAYOUT ---
tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with tab1:
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, category FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        posts = cursor.fetchall()
        if not posts: st.info("Koi rewritten news nahi hai. Sidebar se trigger karein.")
        for pid, title, content, img, desc, cat in posts:
            with st.expander(f"📦 [{cat}] - {title}", expanded=False):
                f_title = st.text_input("Headline", value=title, key=f"t{pid}")
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    if img: st.image(img, use_container_width=True)
                    f_desc = st.text_area("Meta Description", value=str(desc), key=f"d{pid}")
                with c2:
                    f_content = st.text_area("Content (300-400 words)", value=content, height=350, key=f"c{pid}")
                    if st.button("🚀 Publish Now", key=f"p{pid}", type="primary"):
                        success, err = publish_to_wp(f_title, f_content, img, f_desc, cat)
                        if success:
                            cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                            conn.commit()
                            st.success("Live on WordPress!")
                            st.rerun()
                        else: st.error(f"Error: {err}")

    with tab2: # Published Tab
        cursor.execute("SELECT title, category FROM news_articles WHERE status='published' ORDER BY id DESC")
        for t, c in cursor.fetchall(): st.success(f"✔️ **[{c}]** {t}")

    conn.close()
