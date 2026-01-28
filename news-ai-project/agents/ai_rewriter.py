import sqlite3
import os
import re
import time
import streamlit as st
from groq import Groq

# Secrets se Groq API Key lena
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')

def safe_parse(text, label, next_label=None):
    """Safe extraction logic to avoid parsing errors"""
    try:
        pattern = f"{label}:(.*?)(?={next_label}:|$)" if next_label else f"{label}:(.*)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "Not Generated"
    except: return "Not Generated"

def rewrite_news():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ek baar mein sirf 3 articles process karein taaki limit na hit ho
    cursor.execute("SELECT id, title, raw_content FROM news_articles WHERE status='pending' AND rewritten_content IS NULL LIMIT 3")
    articles = cursor.fetchall()

    if not articles:
        print("📭 No pending articles to rewrite.")
        return

    for art_id, old_title, raw_content in articles:
        print(f"✍️ Rewriting: {old_title}")
        prompt = f"""
        Act as a professional independent news editor. 
        TITLE: {old_title}
        DATA: {raw_content}
        RULES: 
        1. NEW_TITLE: Create a catchy headline.
        2. CONTENT: Write a 500-word article. 
        3. NO REFERENCES: Strictly no mention of Reuters, TOI, Mint, etc.
        FORMAT:
        NEW_TITLE: [Headline]
        CONTENT: [Article Body]
        CATEGORY: [Tech/Business/Sports/Entertainment/Health]
        META: [SEO Description]
        TAGS: [8 keywords]
        IMAGE_PROMPT: [15 word photo prompt]
        """
        try:
            # Model switched to 8b-instant for higher limits
            res = client.chat.completions.create(
                messages=[{"role":"user","content":prompt}], 
                model="llama-3.1-8b-instant"
            ).choices[0].message.content
            
            ntitle = safe_parse(res, "NEW_TITLE", "CONTENT")
            ncontent = safe_parse(res, "CONTENT", "CATEGORY")
            cat = safe_parse(res, "CATEGORY", "META")
            meta = safe_parse(res, "META", "TAGS")
            tags = safe_parse(res, "TAGS", "IMAGE_PROMPT")
            img_p = safe_parse(res, "IMAGE_PROMPT")

            img_url = f"https://pollinations.ai/p/{img_p.replace(' ','_')}?width=1024&height=768&model=flux&seed=42"

            cursor.execute('''UPDATE news_articles 
                           SET title=?, rewritten_content=?, category=?, seo_description=?, seo_tags=?, image_url=? 
                           WHERE id=?''', 
                           (ntitle, ncontent, cat, meta, tags, img_url, art_id))
            conn.commit()
            print(f"✅ Success: {ntitle}")
            
            # ⏳ Har request ke baad 20 second ka gap
            print("⏳ Waiting 20 seconds to avoid Rate Limit...")
            time.sleep(20) 
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            if "429" in str(e):
                print("🛑 Limit reached. Stopping for now.")
                break
    conn.close()

if __name__ == "__main__":
    rewrite_news()
