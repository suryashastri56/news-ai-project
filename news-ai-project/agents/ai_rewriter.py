import sqlite3
import os
import re
import time
import streamlit as st
from groq import Groq

# CONFIG & PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def safe_parse(text, label, next_label=None):
    try:
        pattern = f"{label}:(.*?)(?={next_label}:|$)" if next_label else f"{label}:(.*)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "Not Generated"
    except: return "Not Generated"

def rewrite_news():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Har category ki list jinhe humein process karna hai
    categories = ["Technology", "Business", "Sports", "India", "General"]
    
    for cat in categories:
        st.write(f"🔄 Processing Category: {cat}")
        # Har category se sirf 2 pending articles uthana
        cursor.execute("""
            SELECT id, title, raw_content FROM news_articles 
            WHERE status='pending' AND rewritten_content IS NULL AND category=? 
            LIMIT 2
        """, (cat,))
        articles = cursor.fetchall()

        for art_id, old_title, raw_content in articles:
            prompt = f"""
            Act as an independent journalist.
            TITLE: {old_title} | DATA: {raw_content}
            RULES: 
            1. NEW_TITLE: Catchy headline.
            2. CONTENT: Strictly 300-400 words. No agency names (Reuters/TOI/Mint).
            FORMAT: NEW_TITLE:, CONTENT:, CATEGORY:, META:, TAGS:, IMAGE_PROMPT:
            """
            try:
                res = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant" # Better rate limits
                ).choices[0].message.content

                ntitle = safe_parse(res, "NEW_TITLE", "CONTENT")
                ncontent = safe_parse(res, "CONTENT", "CATEGORY")
                meta = safe_parse(res, "META", "TAGS")
                tags = safe_parse(res, "TAGS", "IMAGE_PROMPT")
                img_p = safe_parse(res, "IMAGE_PROMPT")

                img_url = f"https://pollinations.ai/p/{img_p.replace(' ','_')}?width=1024&height=768&model=flux&nologo=true"

                cursor.execute("""
                    UPDATE news_articles 
                    SET title=?, rewritten_content=?, category=?, seo_description=?, seo_tags=?, image_url=? 
                    WHERE id=?
                """, (ntitle, ncontent, cat, meta, tags, img_url, art_id))
                conn.commit()
                st.write(f"✅ Success: {ntitle}")
                
                # Rate limit cooldown
                time.sleep(12) 
            except Exception as e:
                st.error(f"Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    rewrite_news()
