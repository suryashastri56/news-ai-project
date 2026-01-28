import streamlit as st
import sqlite3
import os
import requests
import base64
import time

# --- CONFIG & PATHS ---
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# Secrets
WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
WP_API_URL = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

st.set_page_config(page_title="AI News Admin", layout="wide")

def publish_to_wp(title, content, img_url, excerpt, cat_name):
    """WordPress REST API logic with response check"""
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    
    # Justified HTML body
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><div style="text-align:justify">{content.replace("\n", "<br>")}</div>'
    
    # Category mapping
    mapping = {"Business": 6, "Entertainment": 13, "Health": 14, "Sports": 7, "Technology": 1, "India": 2}
    cat_id = mapping.get(cat_name.strip(), 1)

    data = {'title': title, 'content': html_body, 'excerpt': excerpt, 'categories': [cat_id], 'status': 'publish'}
    try:
        r = requests.post(WP_API_URL, headers=headers, json=data, timeout=30)
        return r.status_code == 201, r.text # 201 means Success
    except Exception as e:
        return False, str(e)

st.title("🗞️ AI News Manager")

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
            with st.expander(f"📦 [{cat}] - {title}", expanded=False):
                f_title = st.text_input("Headline", value=title, key=f"t{pid}")
                f_content = st.text_area("Body", value=content, height=300, key=f"c{pid}")
                
                if st.button("🚀 Publish Now", key=f"p{pid}", type="primary"):
                    success, resp = publish_to_wp(f_title, f_content, img, desc, cat)
                    if success:
                        # STATUS UPDATE: Data ko Pending se hatakar Published mein dalna
                        cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                        conn.commit()
                        st.success("Mubarak ho! Article live ho gaya.")
                        time.sleep(1)
                        st.rerun() # Refresh tabs
                    else:
                        st.error(f"Publish Fail: {resp}")

    # --- TAB 2: PUBLISHED (Yahan data dikhega) ---
    with tab2:
        cursor.execute("SELECT title, category FROM news_articles WHERE status='published' ORDER BY id DESC")
        published_rows = cursor.fetchall()
        if not published_rows:
            st.warning("Koi bhi article abhi tak publish nahi hua.")
        for t, c in published_rows:
            st.success(f"✔️ **[{c}]** {t}")

    conn.close()
