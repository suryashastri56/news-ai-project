import streamlit as st

def generate_article_image(image_prompt):
    """Content se related AI image URL banana"""
    try:
        if not image_prompt or "Not Generated" in image_prompt:
            # Fallback image agar prompt fail ho jaye
            return "https://pollinations.ai/p/news_breaking_news_global_updates?width=1024&height=768&seed=42"
        
        # URL friendly prompt banana
        clean_prompt = image_prompt.replace(" ", "_").strip()
        
        # Pollinations Flux Model
        image_url = f"https://pollinations.ai/p/{clean_prompt}?width=1024&height=768&model=flux&nologo=true"
        return image_url
    except:
        return "https://pollinations.ai/p/news_headline_background?width=1024&height=768"
