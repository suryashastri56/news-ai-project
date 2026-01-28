import sqlite3
import os
from groq import Groq
from dotenv import load_dotenv

# Path setups
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')
load_dotenv(os.path.join(BASE_DIR, '..', '.env'))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def rewrite_news():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, raw_content FROM news_articles WHERE status='pending' AND rewritten_content IS NULL")
    articles = cursor.fetchall()

    for art_id, title, raw_content in articles:
        print(f"✍️ Processing: {title}")
        
        prompt = f"""
        Headline: {title}
        Original: {raw_content}
        Task: Rewrite in English (300 words), assign category [Technology, Business, Sports, Entertainment, Health], and provide SEO meta.
        
        Format:
        CONTENT: [Article text]
        CATEGORY: [Select one]
        META: [Description]
        TAGS: [5 keywords]
        PROMPT: [Image prompt]
        """

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            response = chat_completion.choices[0].message.content

            # Safer Parsing Logic
            content = response.split("CONTENT:")[1].split("CATEGORY:")[0].strip()
            category = response.split("CATEGORY:")[1].split("META:")[0].strip()
            meta = response.split("META:")[1].split("TAGS:")[0].strip()
            tags = response.split("TAGS:")[1].split("PROMPT:")[0].strip()
            img_p = response.split("PROMPT:")[1].strip()

            img_url = f"https://pollinations.ai/p/{img_p.replace(' ', '_')}?width=1024&height=768&model=flux"

            # Database Update with category
            cursor.execute('''
                UPDATE news_articles 
                SET rewritten_content=?, category=?, seo_description=?, seo_tags=?, image_url=?
                WHERE id=?
            ''', (content, category, meta, tags, img_url, art_id))
            
            conn.commit()
            print(f"✅ Success! Article {art_id} categorized as {category}")

        except Exception as e:
            print(f"❌ Error in article {art_id}: {e}")

    conn.close()

if __name__ == "__main__":
    rewrite_news()
