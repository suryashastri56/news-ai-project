import streamlit as st
import sqlite3
import os
import requests
import base64
import json

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# FIX: Secrets syntax corrected (Square brackets instead of parenthesis)
SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
WP_URL = f"{SITE_URL}/wp-json/wp/v2/posts"
WP_USER = st.secrets["WP_USERNAME"]
WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]

st.set_page_config(page_title="AI News Admin", layout="wide")
st.title("🤖 AI News Content Manager")

# --- HELPER FUNCTIONS ---

def get_category_id(cat_name):
    """WordPress Category Name to ID Mapping"""
    mapping = {
        "Business": 6, "Entertainment": 13, "Health": 14, 
        "Sports": 7, "Science": 8, "General": 1,
        "World": 10, "India": 2, "Technology": 1
    }
    return mapping.get(cat_name.strip(), 1)

def get_posts_by_status(status):
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    token = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}', 
        'Content-Type': 'application/json'
    }
    
    # Justified Content Layout
    html_body = f"""
    <figure class="wp-block-image size-large"><img src="{img_url}" alt="{title}"/></figure><div style="text-align: justify; line-height: 1.8;">
        <p>{content.replace('\n', '<br>')}</p>
    </div>
    """
    
    post_data = {
        'title': title,
        'content': html_body,
        'excerpt': excerpt,
        'categories': [get_category_id(category_name)],
        'status': 'publish'
    }
    
    try:
        response = requests.post(WP_URL, headers=headers, json=post_data, timeout=30)
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
        with st.expander(f"📦 [{category}] - {title}", expanded=True):
            # NEW: Headline Rewrite Option
            final_title = st.text_input("Edit Headline (SEO Friendly):", value=title, key=f"t_{pid}")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # FIX: Streamlit image parameter warning resolved
                if img_url: 
                    st.image(img_url, width=450, caption="AI Image Preview")
                
                st.info(f"📂 **Target Category:** {category}")
                
                st.subheader("SEO Meta Details")
                final_desc = st.text_area("Meta Description (Excerpt):", str(seo_desc), key=f"d_{pid}", height=100)
                final_tags = st.text_input("Keywords:", str(seo_tags), key=f"tg_{pid}")
                
                if st.button(f"🗑️ Reject Article", key=f"rej_{pid}", use_container_width=True):
                    update_status(pid, 'rejected')
                    st.rerun()
            
            with col2:
                st.subheader("Edit Article Content")
                edited_content = st.text_area("Body:", str(content), height=450, key=f"ed_{pid}")
                
                if st.button(f"🚀 Publish to {category}", key=f"pub_{pid}", use_container_width=True):
                    success, msg = publish_to_wp(final_title, edited_content, img_url, final_desc, final_tags, category)
                    if success:
                        update_status(pid, 'published')
                        st.success(f"Article live hai!")
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")

with tab2:
    for pid, title, content, img_url, d, t, cat in get_posts_by_status('published'):
        st.success(f"✔️ **[{cat}]** {title}")

with tab3:
    for pid, title, content, img_url, d, t, cat in get_posts_by_status('rejected'):
        col_rej, col_res = st.columns([4, 1])
        col_rej.error(f"❌ **[{cat}]** {title}")
        if col_res.button("Restore", key=f"res_{pid}"):
            update_status(pid, 'pending')
            st.rerun()
