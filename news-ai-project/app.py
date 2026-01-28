import streamlit as st
import sqlite3
import os
import requests
import base64
import json

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# Secrets Fix
WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
WP_API_URL = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

st.set_page_config(page_title="AI News Admin Pro", layout="wide")

def get_category_id(cat_name):
    """WordPress Category ID Mapping"""
    mapping = {"Business": 6, "Entertainment": 13, "Health": 14, "Sports": 7, "Technology": 1, "India": 2}
    return mapping.get(cat_name.strip(), 1)

def publish_to_wp(title, content, img_url, excerpt, cat_name):
    """Publishing logic with detailed error reporting"""
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    
    html_body = f"""
    <figure class="wp-block-image size-large"><img src="{img_url}"/></figure><div style="text-align: justify; line-height: 1.8;"><p>{content.replace('\n', '<br>')}</p></div>
    """
    
    post_data = {
        'title': title,
        'content': html_body,
        'excerpt': excerpt,
        'categories': [get_category_id(cat_name)],
        'status': 'publish'
    }
    
    try:
        r = requests.post(WP_API_URL, headers=headers, json=post_data, timeout=30)
        return r.status_code == 201, r.text # Status code 201 means Created
    except Exception as e:
        return False, str(e)

st.title("🗞️ News AI Admin Panel")

# Sidebar Actions
with st.sidebar:
    if st.button("📡 Fetch & Rewrite News", use_container_width=True):
        st.info("Script running... please wait.")
        # Triggering scripts here...

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
            with st.expander(f"📦 {title}", expanded=False):
                f_title = st.text_input("Headline", value=title, key=f"t{pid}")
                f_content = st.text_area("Content", value=content, height=300, key=f"c{pid}")
                
                if st.button("🚀 Publish Now", key=f"pub{pid}", type="primary"):
                    success, error_msg = publish_to_wp(f_title, f_content, img, desc, cat)
                    if success:
                        # Status update is crucial for data to show in Tab 2
                        cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                        conn.commit()
                        st.success("Mubarak ho! Article live hai.")
                        st.rerun() # Refresh tabs
                    else:
                        st.error(f"WordPress Error: {error_msg}")

    # --- TAB 2: PUBLISHED (Data Fix) ---
    with tab2:
        # Fetching strictly based on 'published' status
        cursor.execute("SELECT title, category FROM news_articles WHERE status='published' ORDER BY id DESC")
        published_articles = cursor.fetchall()
        if not published_articles:
            st.warning("Koi bhi article abhi tak publish nahi hua.")
        for t, c in published_articles:
            st.success(f"✔️ **[{c}]** {t}")

    # --- TAB 3: REJECTED ---
    with tab3:
        cursor.execute("SELECT id, title FROM news_articles WHERE status='rejected' ORDER BY id DESC")
        for rid, t in cursor.fetchall():
            col_a, col_b = st.columns([4,1])
            col_a.error(f"❌ {t}")
            if col_b.button("Restore", key=f"res{rid}"):
                cursor.execute("UPDATE news_articles SET status='pending' WHERE id=?", (rid,))
                conn.commit(); st.rerun()

    conn.close()
