import streamlit as st
import sqlite3
import os
import time
from sidebar_actions import render_sidebar 
from article_editor import show_editor      

# --- PAGE CONFIG ---
st.set_page_config(page_title="News AI Pro Admin", layout="wide")

# 1. SIDEBAR RENDER (Isse buttons wapas aa jayenge)
render_sidebar()

# 2. MAIN HEADER
st.title("🗞️ News AI Content Manager")

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# 3. UI TABS
tab1, tab2, tab3 = st.tabs(["⏳ Pending Review", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # PENDING TAB (SEO, Meta, aur Category ke saath)
        with tab1:
            cursor.execute("""
                SELECT id, title, rewritten_content, image_url, category, seo_description, seo_tags 
                FROM news_articles 
                WHERE status='pending' AND rewritten_content IS NOT NULL
            """)
            posts = cursor.fetchall()
            
            if not posts:
                st.info("Abhi koi pending rewritten news nahi hai. Sidebar se 'Rewrite' dabayein.")
            
            for post in posts:
                # article_editor.py se UI load karna
                show_editor(*post, cursor, conn)
                
        # PUBLISHED TAB
        with tab2:
            cursor.execute("SELECT title, category FROM news_articles WHERE status='published' ORDER BY id DESC")
            published_data = cursor.fetchall()
            if not published_data:
                st.warning("Koi article abhi tak publish nahi hua.")
            for t, c in published_data:
                st.success(f"✔️ **[{c}]** {t}")

        # REJECTED TAB
        with tab3:
            cursor.execute("SELECT id, title FROM news_articles WHERE status='rejected' ORDER BY id DESC")
            for rid, t in cursor.fetchall():
                st.error(f"❌ {t}")
                if st.button("Restore", key=f"res{rid}"):
                    cursor.execute("UPDATE news_articles SET status='pending' WHERE id=?", (rid,))
                    conn.commit()
                    st.rerun()

    except Exception as e:
        # Agar table nahi milti toh ye error handle karega
        st.error(f"⚠️ Database Error: {e}")
        st.info("Sidebar mein 'Repair Database' button dabayein.")
    
    finally:
        conn.close()
else:
    st.warning("Database file missing! Please click 'Fetch News' in the sidebar to create it.")
