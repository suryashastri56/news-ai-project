import sqlite3
import os
import re
import time
import streamlit as st # Secrets access karne ke liye
from groq import Groq

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')

# Streamlit Secrets se Groq API Key lena
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def safe_parse(text, label, next_label=None):
    """Regex parsing logic to prevent 'index out of range' errors"""
    try:
        pattern = f"{label}:(.*?)(?={next_label}:|$)" if next_label else f"{label}:(.*)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "Not Generated"
    except:
        return "Not Generated"

def rewrite_news():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 429 Rate Limit se bachne ke liye ek baar mein sirf 5 articles
    cursor.execute("""
        SELECT id, title, raw_content FROM news_articles 
        WHERE status='pending' AND rewritten_content IS NULL LIMIT 5
    """)
    articles = cursor.fetchall()

    if not articles:
        print("📭 No pending articles to rewrite.")
        return

    for art_id, old_title, raw_content in articles:
        print(f"✍️ Rebranding & Rewriting: {old_title}")
        
        # Strict instructions for 300-400 words and no references
        prompt = f"""
        Act as an expert independent journalist.
        ORIGINAL TITLE: {old_title}
        SOURCE DATA: {raw_content}
        
        STRICT RULES:
        1. NEW_TITLE: Create a completely new, engaging, and SEO-friendly headline.
        2. CONTENT: Write a high-quality article strictly between 300 to 400 words.
        3. NO REFERENCES: Do not mention any sources like Reuters, TOI, BBC, Mint, etc.
        4. TONE: Informative, authoritative, and unique.

        FORMAT:
        NEW_TITLE: [Your new headline]
        CONTENT: [Your 300-400 word article]
        CATEGORY: [Technology, Business, Sports, Entertainment, Health, India]
        META: [160 character SEO description]
        TAGS: [8 comma-separated keywords]
        IMAGE_PROMPT: [15 word descriptive prompt for AI image]
        """

        try:
            # Using 8b-instant for better rate limits
            res = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            ).choices[0].message.content

            # Extracting all parts using safe regex
            new_title = safe_parse(res, "NEW_TITLE", "CONTENT")
            content = safe_parse(res, "CONTENT", "CATEGORY")
            category = safe_parse(res, "CATEGORY", "META")
            meta = safe_parse(res, "META", "TAGS")
            tags = safe_parse(res, "TAGS", "IMAGE_PROMPT")
            img_p = safe_parse(res, "IMAGE_PROMPT")

            if content == "Not Generated":
                print(f"⚠️ Skipping {old_title}: AI failed to generate content.")
                continue

            # Pollinations AI for featured images
            image_url = f"https://pollinations.ai/p/{img_p.replace(' ', '_')}?width=1024&height=768&model=flux&nologo=true&seed=88"

            # Database update
            cursor.execute("""
                UPDATE news_articles 
                SET title=?, rewritten_content=?, category=?, seo_description=?, seo_tags=?, image_url=? 
                WHERE id=?
            """, (new_title, content, category, meta, tags, image_url, art_id))
            
            conn.commit()
            print(f"✅ Success: {new_title}")
            
            # ⏳ Har request ke baad gap taaki 429 error na aaye
            print("⏳ Cooling down for 15 seconds...")
            time.sleep(15)

        except Exception as e:
            print(f"❌ Error during rewrite: {e}")
            if "429" in str(e):
                print("🛑 Rate limit hit. Stopping batch.")
                break

    conn.close()

if __name__ == "__main__":
    rewrite_news()
