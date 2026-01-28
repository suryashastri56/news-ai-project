import streamlit as st
import sqlite3
import os
from sidebar_actions import render_sidebar 
from article_editor import show_editor      # Line ke shuruat mein koi space na rakhein

st.set_page_config(page_title="News AI Pro", layout="wide")

# Sidebar Action Center Render
render_sidebar()

st.title("🗞️ News AI Content Manager")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        with tab1:
            # Query explicitly selecting SEO columns
            cursor.execute("""
                SELECT id, title, rewritten_content, image_url, category, seo_description, seo_tags 
                FROM news_articles 
                WHERE status='pending' AND rewritten_content IS NOT NULL
            """)
            for post in cursor.fetchall():
                # Editor file ko call karna
                show_editor(*post, cursor, conn)
                
        with tab2:
            cursor.execute("SELECT title, category FROM news_articles WHERE status='published' ORDER BY id DESC")
            for t, c in cursor.fetchall():
                st.success(f"✔️ **[{c}]** {t}")
                
    except Exception as e:
        st.error(f"⚠️ Dashboard Error: {e}. Please use 'Repair Database' in sidebar.")
    
    conn.close()
