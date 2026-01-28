import streamlit as st
import sqlite3
import os
from sidebar_actions import render_sidebar 

st.set_page_config(page_title="News Admin Pro", layout="wide")

# Sidebar Actions call karein
render_sidebar() 

st.title("🗞️ AI News Content Manager")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # PENDING ARTICLES
        with tab1:
            cursor.execute("SELECT id, title, rewritten_content, image_url, category, seo_description, seo_tags FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
            posts = cursor.fetchall()
            if not posts: st.info("Abhi koi pending news nahi hai.")
            for pid, title, content, img, cat, desc, tags in posts:
                with st.expander(f"📦 [{cat}] - {title}"):
                    # IMAGE FIX: No more DeltaGenerator code
                    if img and img != "Not Generated":
                        st.image(img, width="stretch") # Updated param
                    
                    # Headline & Content display
                    st.text_input("Headline", value=title, key=f"t{pid}")
                    st.text_area("Content", value=content, height=300, key=f"c{pid}")
                    
                    # Buttons
                    c1, c2 = st.columns(2)
                    if c1.button("🚀 Publish", key=f"p{pid}", type="primary"):
                        # Logic yahan aayegi
                        st.rerun()
    except Exception as e:
        st.error(f"Operational Error: {e}. Please click 'Repair Database' in sidebar.")
    conn.close()
