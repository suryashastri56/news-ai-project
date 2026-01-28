import streamlit as st
import requests
import base64

def publish_to_wp(title, content, img_url, excerpt, cat_name):
    """WordPress REST API call function"""
    # Secrets se credentials lena
    WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
    WP_USER = st.secrets["WP_USERNAME"]
    WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
    
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {
        'Authorization': f'Basic {token}', 
        'Content-Type': 'application/json'
    }
    
    # Category ID Mapping (Apne hisaab se check karein)
    mapping = {"Technology": 1, "Business": 6, "India": 2, "Sports": 7}
    cat_id = mapping.get(cat_name, 1)

    # HTML Body structure
    html_body = f'<figure class="wp-block-image"><img src="{img_url}"/></figure><div style="text-align:justify">{content.replace("\n", "<br>")}</div>'
    
    post_data = {
        'title': title,
        'content': html_body,
        'excerpt': excerpt,
        'categories': [cat_id],
        'status': 'publish'
    }
    
    try:
        url = f"{WP_SITE_URL}/wp-json/wp/v2/posts"
        r = requests.post(url, headers=headers, json=post_data, timeout=30)
        return r.status_code == 201, r.text
    except Exception as e:
        return False, str(e)

def show_editor(pid, title, content, img, cat, desc, tags, cursor, conn):
    with st.expander(f"📦 [{cat}] - {title}", expanded=False):
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            if img: st.image(img, width="stretch")
            f_cat = st.selectbox("Category", ["Technology", "Business", "India", "Sports"], key=f"cat_{pid}")
            f_desc = st.text_area("Meta Description", value=str(desc), key=f"desc_{pid}")
            f_tags = st.text_input("SEO Tags", value=str(tags), key=f"tags_{pid}")
            
        with col2:
            f_title = st.text_input("Headline", value=title, key=f"tit_{pid}")
            f_content = st.text_area("Body", value=content, height=400, key=f"con_{pid}")
            
            if st.button("🚀 Publish to WordPress", key=f"pub_{pid}", type="primary", width="stretch"):
                # 1. PEHLE WORDPRESS PAR BHEJEIN
                success, error_msg = publish_to_wp(f_title, f_content, img, f_desc, f_cat)
                
                if success:
                    # 2. AGAR WP PAR SUCCESS HUA, TABHI DATABASE UPDATE KAREIN
                    cursor.execute("""
                        UPDATE news_articles 
                        SET title=?, rewritten_content=?, category=?, seo_description=?, seo_tags=?, status='published' 
                        WHERE id=?
                    """, (f_title, f_content, f_cat, f_desc, f_tags, pid))
                    conn.commit()
                    st.success("✅ WordPress par live ho gaya!")
                    st.rerun()
                else:
                    # 3. AGAR ERROR AAYA TOH DIKHAYEIN
                    st.error(f"❌ WordPress Error: {error_msg}")
