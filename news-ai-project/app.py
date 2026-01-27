import streamlit as st
import sqlite3
import os
import requests
import base64
import json
from dotenv import load_dotenv

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
load_dotenv(os.path.join(BASE_DIR, '.env'))

SITE_URL = os.getenv("WP_SITE_URL", "").strip("/")
WP_URL = f"{SITE_URL}/wp-json/wp/v2/posts"
WP_USER = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

st.set_page_config(page_title="AI News Admin", layout="wide")
st.title("🤖 AI News Content Manager")

# --- DB FUNCTIONS ---
def get_posts_by_status(status):
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # SEO Description aur Tags fetch karna
    cursor.execute("SELECT id, title, rewritten_content, image_url, seo_description, seo_tags FROM news_articles WHERE status=?", (status,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_status(pid, new_status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE news_articles SET status=? WHERE id=?", (new_status, pid))
    conn.commit()
    conn.close()

def publish_to_wp(title, content, img_url, excerpt, tags):
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode())
    headers = {'Authorization': f'Basic {token.decode()}', 'Content-Type': 'application/json'}
    
    # Block-style HTML for WordPress
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><p>{str(content).replace("\n", "<br>")}</p>'
    
    # WordPress API fix: 'tags' field ko hata diya gaya hai kyunki wo IDs mangta hai
    # Tags ko hum 'excerpt' ke end mein add kar rahe hain SEO ke liye
    full_excerpt = f"{excerpt}\n\nKeywords: {tags}"
    
    post_data = {
        'title': title,
        'content': html_body,
        'excerpt': full_excerpt,
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
    pending_posts = get_posts_by_status('pending')
    if not pending_posts:
        st.info("No pending articles found.")
    for pid, title, content, img_url, seo_desc, seo_tags in pending_posts:
        with st.expander(f"📝 {title}", expanded=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                # Use standard Pollinations if current image fails
                if img_url: st.image(img_url, width=350)
                
                st.subheader("SEO Meta Details")
                # Handle 'None' values safely
                disp_desc = str(seo_desc) if seo_desc else "No description generated."
                disp_tags = str(seo_tags) if seo_tags else "news, trending"
                
                final_seo_desc = st.text_area("Meta Description:", disp_desc, height=100, key=f"seo_{pid}")
                final_tags = st.text_input("Tags:", disp_tags, key=f"tags_{pid}")
                
                if st.button(f"🗑️ Reject", key=f"rej_{pid}"):
                    update_status(pid, 'rejected')
                    st.rerun()
            
            with col2:
                edited_content = st.text_area("Content:", str(content), height=350, key=f"ed_{pid}")
                if st.button(f"🚀 Publish to WordPress", key=f"pub_{pid}"):
                    success, msg = publish_to_wp(title, edited_content, img_url, final_seo_desc, final_tags)
                    if success:
                        update_status(pid, 'published')
                        st.success("Mubarak ho! Post live ho gaya.")
                        st.rerun()
                    else: st.error(f"Error: {msg}")

with tab2:
    for pid, title, content, img_url, d, t in get_posts_by_status('published'):
        st.write(f"✅ **{title}**")