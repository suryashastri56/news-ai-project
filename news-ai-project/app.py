import streamlit as st
import sqlite3
import os
from sidebar_actions import render_sidebar # Nayi file include ki

# --- PAGE CONFIG ---
st.set_page_config(page_title="News Admin Pro", layout="wide")

# --- SIDEBAR BUTTONS ---
render_sidebar() # Ye line saare buttons ko wapas le aayegi

# --- MAIN DASHBOARD ---
st.title("🗞️ News AI Content Manager")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

tab1, tab2, tab3 = st.tabs(["⏳ Pending", "✅ Published", "❌ Rejected"])

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # PENDING TAB
    with tab1:
        cursor.execute("SELECT id, title, rewritten_content, image_url, category, seo_description, seo_tags FROM news_articles WHERE status='pending' AND rewritten_content IS NOT NULL")
        for pid, title, content, img, cat, desc, tags in cursor.fetchall():
            with st.expander(f"📦 [{cat}] - {title}"):
                st.image(img, width="stretch") if img else None
                f_title = st.text_input("Headline", value=title, key=f"t{pid}")
                f_content = st.text_area("Content", value=content, height=300, key=f"c{pid}")
                
                col1, col2 = st.columns(2)
                if col1.button("🚀 Publish", key=f"p{pid}", type="primary"):
                    # WordPress publishing logic yahan call karein
                    cursor.execute("UPDATE news_articles SET status='published' WHERE id=?", (pid,))
                    conn.commit()
                    st.rerun()
                if col2.button("❌ Reject", key=f"r{pid}"):
                    cursor.execute("UPDATE news_articles SET status='rejected' WHERE id=?", (pid,))
                    conn.commit()
                    st.rerun()

    # PUBLISHED TAB
    with tab2:
        cursor.execute("SELECT title, category FROM news_articles WHERE status='published' ORDER BY id DESC")
        for t, c in cursor.fetchall():
            st.success(f"✔️ **[{c}]** {t}")

    # REJECTED TAB
    with tab3:
        cursor.execute("SELECT id, title FROM news_articles WHERE status='rejected' ORDER BY id DESC")
        for rid, t in cursor.fetchall():
            st.error(f"❌ {t}")
            if st.button("Restore", key=f"res{rid}"):
                cursor.execute("UPDATE news_articles SET status='pending' WHERE id=?", (rid,))
                conn.commit(); st.rerun()

    conn.close()
