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

# Streamlit Secrets (Square brackets fix)
SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_URL = f"{SITE_URL}/wp-json/wp/v2/posts"
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]

st.set_page_config(page_title="AI News Admin Pro", layout="wide")

# --- NEWS FETCHER LOGIC ---
def run_fetcher():
    sources = {
        "General": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
        "Technology": "https://news.google.com/rss/search?q=technology&hl=en-IN&gl=IN&ceid=IN:en",
        "Business": "https://news.google.com/rss/search?q=business&hl=en-IN&gl=IN&ceid=IN:en"
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

# --- WP PUBLISH LOGIC ---
def publish_to_wp(title, content, img_url, excerpt, cat_name):
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><div style="text-align:justify">{content.replace("\n", "<br>")}</div>'
    data = {'title': title, 'content': html_body, 'excerpt': excerpt, 'status': 'publish'}
    try:
        r = requests.post(WP_URL, headers=headers, json=data, timeout=30)
        return r.status_code == 201
    except: return False

# --- UI LAYOUT ---
st.title("🗞️ AI News Content Manager")

# Sidebar for Controls
with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Fetch New News", use_container_width=True):
        count = run_fetcher()
        st.success(f"{count} naye articles mile!")
        st.rerun()

tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with tab1:
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        for pid, title, content, img, desc, tags, cat in cursor.fetchall():
            with st.expander(f"📦 {title}", expanded=True):
                final_title = st.text_input("Headline:", value=title, key=f"t{pid}")
                c1, c2 = st.columns([1, 2])
                with c1:
                    if img: st.image(img, use_container_width=True)
                    f_desc = st.text_area("Meta:", str(desc), key=f"d{pid}")
                    f_tags = st.text_input("Tags:", str(tags), key=f"tg{pid}")
                with c2:
                    f_content = st.text_area("Body:", str(content), height=350, key=f"c{pid}")
                    if st.button("🚀 Publish", key=f"pb{pid}"):
                        if publish_to_wp(final_title, f_content, img, f_desc, cat):
                            cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                            conn.commit(); st.rerun()
    conn.close()
