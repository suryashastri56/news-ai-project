import sqlite3
import os
import time
import re
from groq import Groq
import streamlit as st
from agents.image_generator import generate_article_image # Image module link

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=GROQ_API_KEY)

def rewrite_news():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Sirf wahi articles uthao jo abhi tak rewrite nahi huye
    cursor.execute("SELECT id, title, raw_content, category FROM news_articles WHERE rewritten_content IS NULL")
    articles = cursor.fetchall()

    if not articles:
        st.info("Sabhi articles pehle se hi rewritten hain.")
        return

    for art_id, title, raw_content, category in articles:
        st.write(f"✍️ Rewriting: {title[:50]}...")
        
        prompt = f"""
        You are a professional news editor. Rewrite the following news article into a high-quality, 
        SEO-friendly article of 300-400 words in English.
        
        Original Title: {title}
        Raw Context: {raw_content}
        Category: {category}

        STRICT FORMAT:
        NEW_TITLE: [Catchy Headline]
        CONTENT: [300-400 words article with paragraphs]
        META_DESC: [160 character SEO description]
        SEO_TAGS: [8-10 comma separated keywords]
        IMAGE_PROMPT: [A detailed artistic prompt for an AI image related to this news]
        """

        try:
            # Groq API Call
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
            
            res = chat_completion.choices[0].message.content

            # --- REGEX PARSING (Error hatane ke liye) ---
            def safe_extract(label):
                pattern = f"{label}:(.*?)(?=\n[A-Z_]+:|$)"
                match = re.search(pattern, res, re.DOTALL | re.IGNORECASE)
                return match.group(1).strip() if match else "Not Generated"

            ntitle = safe_extract("NEW_TITLE")
            ncontent = safe_extract("CONTENT")
            nmeta = safe_extract("META_DESC")
            ntags = safe_extract("SEO_TAGS")
            nimg_prompt = safe_extract("IMAGE_PROMPT")

            # --- IMAGE GENERATION TRIGGER ---
            # image_generator.py ko use karke URL banana
            final_image_url = generate_article_image(nimg_prompt)

            # --- DATABASE UPDATE ---
            cursor.execute("""
                UPDATE news_articles 
                SET title=?, rewritten_content=?, seo_description=?, seo_tags=?, image_url=?, status='pending'
                WHERE id=?
            """, (ntitle, ncontent, nmeta, ntags, final_image_url, art_id))
            
            conn.commit()
            st.success(f"✅ Finished: {ntitle[:40]}...")

            # Rate Limit Protection (Groq free tier ke liye zaruri)
            time.sleep(10) 

        except Exception as e:
            st.error(f"Error in rewriting ID {art_id}: {e}")
            continue

    conn.close()
