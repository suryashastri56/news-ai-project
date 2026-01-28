import streamlit as st
import sqlite3
import os

# --- CONFIG ---
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

st.set_page_config(page_title="News Admin", layout="wide")
st.title("🗞️ News Manager (Category Fix)")

# Sidebar Action Center
with st.sidebar:
    st.header("Admin Panel")
    if st.button("📡 Fetch New News", width="stretch"):
        from agents.news_fetcher import fetch_news
        fetch_news()
        st.rerun()

tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with tab1:
        # Category column ko query mein shamil kiya gaya
        cursor.execute("""
            SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category 
            FROM news_articles 
            WHERE status='pending' AND rewritten_content IS NOT NULL
        """)
        posts = cursor.fetchall()
        
        if not posts:
            st.info("No rewritten articles found. Sidebar se 'Rewrite' dabayein.")
            
        for pid, title, content, img, desc, tags, cat in posts:
            # Category ko Expandable Title mein add kiya
            with st.expander(f"📦 [{cat}] - {title}", expanded=True):
                
                # Category Dropdown Selection
                all_cats = ["Technology", "Business", "Sports", "India", "General", "Entertainment", "Health"]
                try:
                    cat_index = all_cats.index(cat) if cat in all_cats else 0
                except: cat_index = 0
                
                new_cat = st.selectbox("Update Category:", all_cats, index=cat_index, key=f"cat_{pid}")
                
                col1, col2 = st.columns([1, 1.5])
                with col1:
                    if img: st.image(img, width="stretch")
                    st.subheader("SEO Meta")
                    f_desc = st.text_area("Meta Desc", value=str(desc), key=f"d_{pid}")
                    f_tags = st.text_input("SEO Tags", value=str(tags), key=f"tg_{pid}")
                
                with col2:
                    st.subheader("Article Body")
                    f_title = st.text_input("Edit Headline", value=title, key=f"t_{pid}")
                    f_content = st.text_area("Edit Content", value=str(content), height=400, key=f"c_{pid}")
                    
                    if st.button(f"🚀 Publish to {new_cat}", key=f"pub_{pid}", type="primary"):
                        # Publishing logic yahan category ke saath jayegi
                        cursor.execute("UPDATE news_articles SET status='published', category=? WHERE id=?", (new_cat, pid))
                        conn.commit()
                        st.rerun()
    conn.close()
