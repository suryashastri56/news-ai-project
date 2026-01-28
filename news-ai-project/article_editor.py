import streamlit as st
import requests
import base64

def publish_to_wp(title, content, img_url, excerpt, cat_name):
    """
    WordPress REST API call logic
    """
    try:
        # Secrets se credentials fetch karna
        WP_SITE_URL = st.secrets["WP_SITE_URL"].strip("/")
        WP_USER = st.secrets["WP_USERNAME"]
        WP_APP_PASSWORD = st.secrets["WP_APP_PASSWORD"]
        
        # Auth Token banana
        token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
        headers = {
            'Authorization': f'Basic {token}', 
            'Content-Type': 'application/json'
        }
        
        # Category Mapping
        mapping = { "Business": 6,
        "Entertainment":13,
                   "Technology":5,
        "Health":14, 
        "Sports": 7,
        "Science": 8,
        "General": 1,
        "World":10,
        "India":2
}
        cat_id = mapping.get(cat_name, 1)

        # HTML Body with Justified Content
        html_body = f"""
        <figure class="wp-block-image size-large"><img src="{img_url}" alt="{title}"/></figure>
        <div style="text-align:justify; line-height:1.6;">
            {content.replace('\n', '<br>')}
        </div>
        """
        
        post_data = {
            'title': title,
            'content': html_body,
            'excerpt': excerpt,
            'categories': [cat_id],
            'status': 'publish'
        }
        
        url = f"{WP_SITE_URL}/wp-json/wp/v2/posts"
        r = requests.post(url, headers=headers, json=post_data, timeout=30)
        
        return r.status_code == 201, r.text
    except Exception as e:
        return False, str(e)

def show_editor(pid, title, content, img, cat, desc, tags, cursor, conn):
    """
    Modular Article Editor UI
    """
    with st.expander(f"📦 [{cat}] - {title}", expanded=False):
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            # AI Generated Image Preview
            if img and "http" in str(img):
                st.image(img, width="stretch", caption="📸 AI Featured Image")
            else:
                st.warning("🖼️ Image URL missing.")
            
            st.divider()
            st.subheader("🛠️ SEO & Meta")
            f_cat = st.selectbox("Category", ["Technology", "Business", "India", "Sports", "Health", "Entertainment"], 
                                 index=0, key=f"cat_{pid}")
            f_desc = st.text_area("Meta Description", value=str(desc), height=100, key=f"desc_{pid}")
            f_tags = st.text_input("SEO Tags", value=str(tags), key=f"tags_{pid}")
            
        with col2:
            st.subheader("🖋️ Content Editor")
            f_title = st.text_input("Headline Editor", value=title, key=f"tit_{pid}")
            f_content = st.text_area("Article Body", value=content, height=450, key=f"con_{pid}")
            
            st.divider()
            
            # Action Buttons
            b1, b2 = st.columns(2)
            
            if b1.button("🚀 Publish to WordPress", key=f"pub_{pid}", type="primary", width="stretch"):
                with st.spinner("Publishing to WordPress..."):
                    success, response = publish_to_wp(f_title, f_content, img, f_desc, f_cat)
                    
                    if success:
                        # Database update only if API success
                        cursor.execute("""
                            UPDATE news_articles 
                            SET title=?, rewritten_content=?, category=?, seo_description=?, seo_tags=?, status='published' 
                            WHERE id=?
                        """, (f_title, f_content, f_cat, f_desc, f_tags, pid))
                        conn.commit()
                        st.success("✅ Article is LIVE on WordPress!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ WordPress Error: {response}")

            if b2.button("🗑️ Reject", key=f"rej_{pid}", width="stretch"):
                cursor.execute("UPDATE news_articles SET status='rejected' WHERE id=?", (pid,))
                conn.commit()
                st.info("Article Rejected.")
                st.rerun()
