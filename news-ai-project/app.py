import streamlit as st
import sqlite3
import os
import requests
import base64
import json

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# FIX: Secrets syntax corrected using square brackets []
SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_URL = f"{SITE_URL}/wp-json/wp/v2/posts"
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]

st.set_page_config(page_title="AI News Admin", layout="wide")
st.title("🤖 AI News Content Manager")

def get_category_id(cat_name):
    mapping = {"Business": 6, "Entertainment": 13, "Health": 14, "Sports": 7, "Science": 8, "General": 1, "World": 10, "India": 2}
    return mapping.get(cat_name.strip(), 1)

def publish_to_wp(title, content, img_url, excerpt, tags, category_name):
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><div style="text-align:justify">{content.replace("\n", "<br>")}</div>'
    post_data = {
        'title': title, 'content': html_body, 'excerpt': excerpt,
        'categories': [get_category_id(category_name)], 'status': 'publish'
    }
    try:
        response = requests.post(WP_URL, headers=headers, json=post_data, timeout=30)
        return response.status_code == 201, response.text
    except Exception as e: return False, str(e)

# --- UI TABS ---
tab1, tab2, tab3 = st.tabs(["⏳ Pending Articles", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with tab1:
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        posts = cursor.fetchall()
        if not posts: st.info("Abhi koi pending news nahi hai.")
        for pid, title, content, img_url, seo_desc, seo_tags, category in posts:
            with st.expander(f"📦 [{category}] - {title}", expanded=True):
                # Edit title logic included
                final_title = st.text_input("Edit Headline:", value=title, key=f"t_{pid}")
                col1, col2 = st.columns([1, 2])
                with col1:
                    if img_url: st.image(img_url, use_container_width=True)
                    f_desc = st.text_area("Meta Description:", str(seo_desc), key=f"d_{pid}")
                    f_tags = st.text_input("Tags:", str(seo_tags), key=f"tg_{pid}")
                with col2:
                    f_content = st.text_area("Edit Body:", str(content), height=350, key=f"c_{pid}")
                    if st.button(f"🚀 Publish", key=f"pub_{pid}"):
                        success, msg = publish_to_wp(final_title, f_content, img_url, f_desc, f_tags, category)
                        if success:
                            cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                            conn.commit(); st.rerun()
                    if st.button(f"🗑️ Reject", key=f"rej_{pid}"):
                        cursor.execute("UPDATE news_articles SET status='rejected' WHERE id=?", (pid,))
                        conn.commit(); st.rerun()

    with tab2: # Published section
        cursor.execute("SELECT title FROM news_articles WHERE status='published' ORDER BY id DESC")
        for (t,) in cursor.fetchall(): st.success(f"✔️ {t}")

    with tab3: # Rejected section
        cursor.execute("SELECT id, title FROM news_articles WHERE status='rejected' ORDER BY id DESC")
        for rid, t in cursor.fetchall():
            if st.button(f"♻️ Restore: {t}", key=f"rs_{rid}"):
                cursor.execute("UPDATE news_articles SET status='pending' WHERE id=?", (rid,))
                conn.commit(); st.rerun()
    conn.close()
