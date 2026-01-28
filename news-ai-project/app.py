import streamlit as st
import sqlite3
import os
import requests
import base64
import json

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# FIX: Secrets accessed with square brackets []
WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
WP_API_URL = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

st.set_page_config(page_title="SEO News Admin Pro", layout="wide")

# Database Initialization
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

# WordPress Category Mapping
def get_category_id(cat_name):
    mapping = {
        "Business": 6, "Entertainment": 13, "Health": 14, 
        "Sports": 7, "Science": 8, "India": 2, "Technology": 1
    }
    return mapping.get(cat_name.strip(), 1)

def publish_to_wp(title, content, img_url, excerpt, cat_name):
    """WordPress REST API Publishing with SEO Optimization"""
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}
    
    # Clean HTML Layout for WP
    html_body = f"""
    <figure class="wp-block-image size-large"><img src="{img_url}" alt="{title}"/></figure><div style="text-align: justify; line-height: 1.8;">
        <p>{content.replace('\n', '<br>')}</p>
    </div>
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
        return r.status_code == 201
    except: return False

init_db()
st.title("🤖 Advanced News SEO Manager")

# TABS for workflow
tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with tab1:
        # Fetching rewritten articles
        cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        posts = cursor.fetchall()
        
        if not posts:
            st.info("No rewritten articles found. Please run ai_rewriter.py first.")
            
        for pid, title, content, img, desc, tags, cat in posts:
            with st.container(border=True): # Cleaner UI container
                # Headline Editor
                f_title = st.text_input("📝 Headline (SEO Optimized)", value=title, key=f"t{pid}")
                
                col1, col2 = st.columns([1, 1.5]) # Balanced column layout
                
                with col1:
                    if img: st.image(img, use_container_width=True, caption="AI Generated Featured Image")
                    st.divider()
                    st.subheader("🛠️ SEO Meta Details")
                    f_cat = st.selectbox("Category", ["Business", "Entertainment", "Health", "Sports", "Science", "India", "Technology"], index=0, key=f"cat{pid}")
                    f_desc = st.text_area("Meta Description (Excerpt)", value=str(desc), height=100, key=f"d{pid}")
                    f_tags = st.text_input("SEO Keywords (Tags)", value=str(tags), key=f"tg{pid}")
                
                with col2:
                    st.subheader("🖋️ Article Content")
                    f_content = st.text_area("Body Editor", value=str(content), height=500, key=f"c{pid}")
                    
                    # Buttons layout
                    btn_col1, btn_col2 = st.columns(2)
                    if btn_col1.button("🚀 Publish to WordPress", key=f"pub{pid}", use_container_width=True, type="primary"):
                        if publish_to_wp(f_title, f_content, img, f_desc, f_cat):
                            cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                            conn.commit()
                            st.success("Mubarak ho! Article live hai.")
                            st.rerun()
                        else:
                            st.error("WordPress Publishing Failed.")

                    if btn_col2.button("🗑️ Reject", key=f"rej{pid}", use_container_width=True):
                        cursor.execute("UPDATE news_articles SET status='rejected' WHERE id=?", (pid,))
                        conn.commit()
                        st.rerun()
    conn.close()
