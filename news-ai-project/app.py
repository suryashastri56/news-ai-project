import streamlit as st
import sqlite3
import os
import requests
import base64
import time

# --- CONFIG & PATHS ---
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# Streamlit Secrets (Correct Syntax)
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
    """WordPress REST API logic"""
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><div style="text-align:justify">{content.replace("\n", "<br>")}</div>'
    
    mapping = {"Business": 6, "Entertainment": 13, "Health": 14, "Sports": 7, "Technology": 1, "India": 2}
    cat_id = mapping.get(cat_name.strip(), 1)

    data = {'title': title, 'content': html_body, 'excerpt': excerpt, 'categories': [cat_id], 'status': 'publish'}
    try:
        r = requests.post(WP_API_URL, headers=headers, json=data, timeout=30)
        return r.status_code == 201, r.text
    except Exception as e: return False, str(e)

# --- 1. SIDEBAR (Hamesha sabase upar) ---
with st.sidebar:
    st.header("⚡ Admin Controls")
    st.info("Yahan se news manage karein.")
    
    if st.button("📡 Fetch New News", use_container_width=True):
        with st.status("Fetching news..."):
            from agents.news_fetcher import fetch_news
            fetch_news()
            st.success("News Fetched!")
            st.rerun()
            
    if st.button("🪄 AI Rewrite", type="primary", use_container_width=True):
        with st.status("AI Rewriting..."):
            from agents.ai_rewriter import rewrite_news
            rewrite_news()
            st.success("Rewriting Done!")
            st.rerun()

    st.divider()
    if st.button("🛠️ Repair Database", use_container_width=True):
        init_db()
        st.sidebar.success("DB Fixed!")

# --- 2. MAIN DASHBOARD ---
init_db()
st.title("🗞️ AI News Content Manager")

tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- TAB 1: PENDING ---
    with tab1:
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, category FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        posts = cursor.fetchall()
        if not posts: st.info("Abhi koi pending news nahi hai.")
        for pid, title, content, img, desc, cat in posts:
            with st.expander(f"📦 [{cat}] - {title}"):
                f_title = st.text_input("Headline", value=title, key=f"t{pid}")
                f_content = st.text_area("Content", value=content, height=300, key=f"c{pid}")
                if st.button("🚀 Publish Now", key=f"p{pid}", type="primary"):
                    success, resp = publish_to_wp(f_title, f_content, img, desc, cat)
                    if success:
                        cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                        conn.commit()
                        st.success("Article live!")
                        time.sleep(1)
                        st.rerun()
                    else: st.error(f"Error: {resp}")

    # --- TAB 2: PUBLISHED (Data fix) ---
    with tab2:
        cursor.execute("SELECT title, category FROM news_articles WHERE status='published' ORDER BY id DESC")
        for t, c in cursor.fetchall():
            st.success(f"✔️ **[{c}]** {t}")

    conn.close()
