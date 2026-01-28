import streamlit as st
import sqlite3
import os

# --- PATHS ---
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

st.set_page_config(page_title="SEO News Admin", layout="wide")

# Sidebar for manual repair
if st.sidebar.button("🛠️ Repair DB & Columns"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table ko naye columns ke saath ensure karna
    cursor.execute('''CREATE TABLE IF NOT EXISTS news_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, raw_content TEXT, 
        rewritten_content TEXT, image_url TEXT, seo_description TEXT, 
        seo_tags TEXT, category TEXT, status TEXT DEFAULT 'pending'
    )''')
    conn.commit()
    conn.close()
    st.sidebar.success("Database structure fixed!")

st.title("🗞️ News SEO Manager")

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # FIX: Saare columns ko SELECT query mein add kiya
    cursor.execute("""
        SELECT id, title, rewritten_content, image_url, seo_description, seo_tags, category 
        FROM news_articles 
        WHERE status='pending' AND rewritten_content IS NOT NULL
    """)
    posts = cursor.fetchall()
    
    if not posts:
        st.info("Pending articles with AI content nahi mile. Pehle 'Rewrite' chalaein.")
    
    for pid, title, content, img, desc, tags, cat in posts:
        with st.expander(f"📦 [{cat}] - {title}", expanded=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Featured Image
                if img and img != "Not Generated":
                    st.image(img, width="stretch", caption="AI Image")
                else:
                    st.warning("🖼️ Image URL missing.")
                
                # SEO Meta Fields
                st.subheader("🛠️ SEO & Meta")
                new_cat = st.text_input("Category", value=str(cat), key=f"cat_{pid}")
                new_desc = st.text_area("Meta Description", value=str(desc), key=f"desc_{pid}")
                new_tags = st.text_input("SEO Tags", value=str(tags), key=f"tags_{pid}")
                
            with col2:
                # Content Editor
                st.subheader("🖋️ Article Body")
                new_title = st.text_input("Edit Headline", value=title, key=f"tit_{pid}")
                new_content = st.text_area("Edit Body", value=content, height=400, key=f"con_{pid}")
                
                if st.button("🚀 Publish", key=f"pub_{pid}", type="primary"):
                    # WordPress publishing logic here...
                    cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                    conn.commit()
                    st.rerun()
    conn.close()
