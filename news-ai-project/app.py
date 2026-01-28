import streamlit as st
import sqlite3
import os
import requests
import base64
import json
from bs4 import BeautifulSoup

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# FIX: Secrets accessed with square brackets []
SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_URL = f"{SITE_URL}/wp-json/wp/v2/posts"
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]

st.set_page_config(page_title="AI News Admin Pro", layout="wide")

# Database initialization function to fix sqlite3 error
def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS news_articles (
        id INTEGER PRIMARY KEY, title TEXT, raw_content TEXT, rewritten_content TEXT,
        image_url TEXT, seo_description TEXT, seo_tags TEXT, category TEXT, status TEXT DEFAULT 'pending'
    )''')
    conn.commit()
    conn.close()

def publish_to_wp(title, content, img_url, excerpt, cat):
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><div style="text-align:justify">{content.replace("\n", "<br>")}</div>'
    data = {'title': title, 'content': html_body, 'excerpt': excerpt, 'status': 'publish'}
    try:
        return requests.post(WP_URL, headers=headers, json=data, timeout=30).status_code == 201
    except: return False

st.title("🤖 AI News Content Manager")
ensure_db() # Run database check on startup

# Sidebar Control
with st.sidebar:
    if st.button("🔄 Reset & Sync Database"):
        ensure_db()
        st.success("Database columns checked!")

tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # SQL error fixed by ensuring table and columns exist
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category FROM news_articles WHERE status='pending'")
        for pid, title, content, img, desc, tags, cat in cursor.fetchall():
            with st.expander(f"📦 {title}", expanded=False):
                final_title = st.text_input("Headline:", value=title, key=f"t{pid}")
                c1, c2 = st.columns([1, 2])
                with c1:
                    if img: st.image(img, use_container_width=True)
                    f_desc = st.text_area("Meta:", str(desc), key=f"d{pid}")
                with c2:
                    f_content = st.text_area("Body:", str(content), height=300, key=f"c{pid}")
                    if st.button("🚀 Publish", key=f"pb{pid}"):
                        if publish_to_wp(final_title, f_content, img, f_desc, cat):
                            cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                            conn.commit(); st.rerun()
    except Exception as e:
        st.error(f"Database Error: {e}. Please use the Sidebar reset button.")
    conn.close()
