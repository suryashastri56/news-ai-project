import sqlite3
import os
from groq import Groq
from dotenv import load_dotenv

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')
load_dotenv(os.path.join(BASE_DIR, '..', '.env'))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def rewrite_news():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Sirf pending articles uthana jinme content abhi nahi hai
    cursor.execute("SELECT id, title, raw_content FROM news_articles WHERE status='pending' AND rewritten_content IS NULL")
    articles = cursor.fetchall()

    for art_id, title, raw_content in articles:
        print(f"✍️ Rewriting: {title}")
        
        # AI Prompt with Category Detection
        prompt = f"""
        Headline: {title}
        Original Content: {raw_content}

        Task 1: Rewrite this into a professional SEO news article in English (300 words).
        Task 2: Select ONE category from: [Technology, Business, Sports, Entertainment, Health].
        Task 3: Create a 150-character SEO Meta Description.
        Task 4: Provide 5 SEO tags (comma separated).
        Task 5: Create a 15-word English prompt for an image.

        Format your response EXACTLY like this:
        CONTENT: [Article Text]
        CATEGORY: [Selected Category]
        META: [Description]
        TAGS: [Keywords]
        PROMPT: [Image Prompt]
        """

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            response = chat_completion.choices[0].message.content

            # Parsing Logic
            rewritten_content = response.split("CONTENT:")[1].split("CATEGORY:")[0].strip()
            category = response.split("CATEGORY:")[1].split("META:")[0].strip()
            seo_desc = response.split("META:")[1].split("TAGS:")[0].strip()
            seo_tags = response.split("TAGS:")[1].split("PROMPT:")[0].strip()
            img_prompt = response.split("PROMPT:")[1].strip()

            # Image URL Generator (Flux Model)
            image_url = f"https://pollinations.ai/p/{img_prompt.replace(' ', '_')}?width=1024&height=768&model=flux"

            # Database Update
            cursor.execute('''
                UPDATE news_articles 
                SET rewritten_content=?, category=?, seo_description=?, seo_tags=?, image_url=?
                WHERE id=?
            ''', (rewritten_content, category, seo_desc, seo_tags, image_url, art_id))
            
            conn.commit()
            print(f"✅ Success: {title} processed under {category}")

        except Exception as e:
            print(f"❌ Error processing article {art_id}: {e}")

    conn.close()

if __name__ == "__main__":
    rewrite_news()
