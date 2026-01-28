import sqlite3
import os
import re
import time
import streamlit as st
from groq import Groq

# FIX: st.secrets syntax
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')

def safe_parse(text, label, next_label=None):
    """Safe extraction logic to avoid index errors"""
    try:
        pattern = f"{label}:(.*?)(?={next_label}:|$)" if next_label else f"{label}:(.*)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "Not Generated"
    except: return "Not Generated"

def rewrite_news():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Batch size of 5 to avoid 429 errors
    cursor.execute("SELECT id, title, raw_content FROM news_articles WHERE status='pending' AND rewritten_content IS NULL LIMIT 5")
    
    for art_id, old_title, raw_content in cursor.fetchall():
        prompt = f"Rewrite NEW_TITLE and 500-word CONTENT for: {old_title}. Strict: No sources (Reuters/TOI). Format: NEW_TITLE:, CONTENT:, CATEGORY:, META:, TAGS:, IMAGE_PROMPT:"
        try:
            res = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.1-8b-instant").choices[0].message.content
            
            ntitle = safe_parse(res, "NEW_TITLE", "CONTENT")
            ncontent = safe_parse(res, "CONTENT", "CATEGORY")
            cat = safe_parse(res, "CATEGORY", "META")
            meta = safe_parse(res, "META", "TAGS")
            tags = safe_parse(res, "TAGS", "IMAGE_PROMPT")
            img_p = safe_parse(res, "IMAGE_PROMPT")

            img_url = f"https://pollinations.ai/p/{img_p.replace(' ','_')}?width=1024&height=768&model=flux&seed=99"

            cursor.execute("UPDATE news_articles SET title=?, rewritten_content=?, category=?, seo_description=?, seo_tags=?, image_url=? WHERE id=?", 
                           (ntitle, ncontent, cat, meta, tags, img_url, art_id))
            conn.commit()
            print(f"✅ Success: {ntitle}")
            time.sleep(20) # Essential for Rate Limit avoidance
        except Exception as e: print(f"❌ Error: {e}")
    conn.close()

if __name__ == "__main__":
    rewrite_news()
