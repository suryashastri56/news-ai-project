import streamlit as st
import sqlite3
import os
import requests
import base64
import json
from dotenv import load_dotenv

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
load_dotenv(os.path.join(BASE_DIR, '.env'))

# WordPress Credentials from Secrets/Env
SITE_URL = os.getenv("WP_SITE_URL", "").strip("/")
WP_URL = f"{SITE_URL}/wp-json/wp/v2/posts"
WP_USER = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

st.set_page_config(page_title="AI News Admin", layout="wide")
st.title("🤖 AI News Content Manager")

# --- HELPER FUNCTIONS ---

def get_category_id(cat_name):
    """WordPress Category Name to ID Mapping"""
    # NOTE: Replace these numbers with your actual WordPress Category IDs
    mapping = {
        "Technology": 123, 
        "Business": 125,
        "Sports": 126,
        "Science": 124,
        "General": 1
    }
    return mapping.get(cat_name.strip(), 1)

def get_posts_by_status(status):
    """Database se articles fetch karna"""
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Category column ko include kiya gaya hai
    cursor.execute("""
        SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category 
        FROM news_articles WHERE status=?
    """, (status,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_status(pid, new_status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE news_articles SET status=? WHERE id=?", (new_status, pid))
    conn.commit()
    conn.close()

def publish_to_wp(title, content, img_url, excerpt, tags, category_name):
    """WordPress REST API Publishing"""
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode())
    headers = {
        'Authorization': f'Basic {token.decode()}', 
        'Content-Type': 'application/json'
    }
    
    # HTML Body with Image
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><p>{str(content).replace("\n", "<br>")}</p>'
    
    # Post Data with Category ID
    post_data = {
        'title': title,
        'content': html_body,
        'excerpt': f"{excerpt}\n\nKeywords: {tags}",
        'categories': [get_category_id(category_name)],
        'status': 'publish'
    }
    
    try:
        response = requests.post(WP_URL, headers=headers, data=json.dumps(post_data), timeout=30)
        return response.status_code == 201, response.text
    except Exception as e:
        return False, str(e)

# --- UI TABS ---
tab1, tab2, tab3 = st.tabs(["⏳ Pending Articles", "✅ Published", "❌ Rejected"])

with tab1:
    posts = get_posts_by_status('pending')
    if not posts:
        st.info("Abhi koi pending news nahi hai. Automation ka intezar karein.")
    
    for pid, title, content, img_url, seo_desc, seo_tags, category in posts:
        # Title ke sath Category badge
        with st.expander(f"📦 [{category}] - {title}", expanded=False):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if img_url: st.image(img_url, use_container_width=True)
                st.info(f"📂 **Target Category:** {category}")
                
                st.subheader("SEO Meta Details")
                final_desc = st.text_area("Meta Description:", str(seo_desc), key=f"d_{pid}")
                final_tags = st.text_input("Tags:", str(seo_tags), key=f"t_{pid}")
                
                if st.button(f"🗑️ Reject", key=f"rej_{pid}"):
                    update_status(pid, 'rejected')
                    st.rerun()
            
            with col2:
                edited_content = st.text_area("Edit Content:", str(content), height=400, key=f"ed_{pid}")
                if st.button(f"🚀 Publish to {category}", key=f"pub_{pid}"):
                    success, msg = publish_to_wp(title, edited_content, img_url, final_desc, final_tags, category)
                    if success:
                        update_status(pid, 'published')
                        st.success(f"Mubarak ho! Article '{category}' page par live hai.")
                        st.rerun()
                    else:
                        st.error(f"WordPress Error: {msg}")

with tab2:
    for pid, title, content, img_url, d, t, cat in get_posts_by_status('published'):
        st.write(f"✅ **[{cat}]** {title}")

with tab3:
    for pid, title, content, img_url, d, t, cat in get_posts_by_status('rejected'):
        st.write(f"❌ **[{cat}]** {title}")
