import streamlit as st
import time

def render_sidebar():
    with st.sidebar:
        st.header("⚡ Admin Action Center")
        st.info("Yahan se saari processes control karein.")
        
        # 1. FETCH NEWS BUTTON
        if st.button("📡 Fetch New News", width="stretch"):
            with st.status("Google News se data aa raha hai..."):
                try:
                    from agents.news_fetcher import fetch_news
                    count = fetch_news()
                    st.success(f"Mubarak ho! {count} naye articles mile.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Fetch Error: {e}")

        # 2. REWRITE NEWS BUTTON
        if st.button("🪄 AI Rewrite (Bulk)", type="primary", width="stretch"):
            with st.status("AI Rewriting shuru hai... please wait."):
                try:
                    from agents.ai_rewriter import rewrite_news
                    rewrite_news()
                    st.success("Sare articles rewrite ho gaye!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"AI Error: {e}")

        st.divider()
        
        # 3. DATABASE REPAIR
        if st.button("🛠️ Repair Database", width="stretch"):
            try:
                import sqlite3
                import os
                DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, raw_content TEXT, 
                    rewritten_content TEXT, image_url TEXT, seo_description TEXT, 
                    seo_tags TEXT, category TEXT, status TEXT DEFAULT 'pending'
                )''')
                conn.commit()
                conn.close()
                st.success("Database columns fixed!")
            except Exception as e:
                st.error(f"DB Error: {e}")
