import os
import sqlite3
import time
import urllib.parse
from groq import Groq
from dotenv import load_dotenv

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def rewrite_and_generate_full_seo():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file nahi mili!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # SEO aur Tags ke liye columns check karna (Safety layer)
    try:
        cursor.execute("ALTER TABLE news_articles ADD COLUMN seo_description TEXT")
        cursor.execute("ALTER TABLE news_articles ADD COLUMN seo_tags TEXT")
        conn.commit()
    except:
        pass

    cursor.execute("SELECT id, title FROM news_articles WHERE rewritten_content IS NULL")
    articles = cursor.fetchall()

    if not articles:
        print("All articles are already processed.")
        conn.close()
        return

    for article_id, title in articles:
        print(f"\nProcessing ID {article_id}: {title}")
        
        try:
            # 1. AI Prompt for Full SEO Package
            prompt = f"""
            Headline: {title}
            Task 1: Professional SEO news article in English (300-500 words).
            Task 2: Catchy SEO Meta Description (150 chars).
            Task 3: 5-7 relevant SEO Keywords/Tags (comma separated).
            Task 4: A 15-word English image prompt.
            
            Format:
            CONTENT: [The Article]
            META: [The Description]
            TAGS: [The Keywords]
            PROMPT: [The Image Prompt]
            """
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile", # Latest stable model
            )
            response = chat_completion.choices[0].message.content

            # Parsing logic
            try:
                rewritten_text = response.split("CONTENT:")[1].split("META:")[0].strip()
                seo_desc = response.split("META:")[1].split("TAGS:")[0].strip()
                seo_tags = response.split("TAGS:")[1].split("PROMPT:")[0].strip()
                image_description = response.split("PROMPT:")[1].strip()
            except:
                rewritten_text = response
                seo_desc = title
                seo_tags = "news, technology, update"
                image_description = title

            # 2. Image Generation URL
            encoded_prompt = urllib.parse.quote(image_description)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&model=flux&nologo=true"

            # 3. Database Update with all SEO fields
            cursor.execute('''
                UPDATE news_articles 
                SET rewritten_content = ?, image_url = ?, seo_description = ?, seo_tags = ?, status = 'pending' 
                WHERE id = ?
            ''', (rewritten_text, image_url, seo_desc, seo_tags, article_id))
            
            conn.commit()
            print(f"✅ Success: Article {article_id} SEO & Tags ready.")
            time.sleep(1) #

        except Exception as e:
            print(f"❌ Error on ID {article_id}: {e}")

    conn.close()

if __name__ == "__main__":
    rewrite_and_generate_full_seo()