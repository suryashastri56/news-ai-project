import streamlit as st
import sqlite3
import os
import requests
import base64
import json

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# FIX: Secrets syntax corrected using [] brackets
WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
WP_API_URL = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

st.set_page_config(page_title="AI News Admin", layout="wide")

# --- DATABASE FIX: Table ensure karne ke liye function ---
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

init_db() # App start hote hi table check aur create karega

# WordPress Publishing Logic
def publish_to_wp(title, content, img_url, excerpt, cat):
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><div style="text-align:justify">{content.replace("\n", "<br>")}</div>'
    data = {'title': title, 'content': html_body, 'excerpt': excerpt, 'status': 'publish'}
    try:
        return requests.post(WP_API_URL, headers=headers, json=data, timeout=30).status_code == 201
    except: return False

st.title("🗞️ AI News Content Manager")

# Sidebar for manual database check
if st.sidebar.button("🛠️ Repair Database"):
    init_db()
    st.sidebar.success("Database Fixed!")

# Tabs for organization
tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with tab1:
        # SQL error fixed by verifying table exists
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        posts = cursor.fetchall()
        if not posts:
            st.info("Abhi koi pending news nahi hai.")
        for pid, title, content, img, desc, tags, cat in posts:
            with st.expander(f"📦 {title}", expanded=False):
                final_title = st.text_input("Edit Headline:", value=title, key=f"t{pid}")
                c1, c2 = st.columns([1, 2])
                with c1:
                    if img: st.image(img, use_container_width=True)
                    f_desc = st.text_area("Meta Description:", str(desc), key=f"d{pid}")
                with c2:
                    f_content = st.text_area("Body:", str(content), height=300, key=f"c{pid}")
                    if st.button("🚀 Publish Now", key=f"pb{pid}"):
                        if publish_to_wp(final_title, f_content, img, f_desc, cat):
                            cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                            conn.commit()
                            st.rerun()
    conn.close()
