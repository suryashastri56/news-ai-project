import os

def generate_article_image(image_prompt):
    """
    Article ke description se unique AI image URL generate karna
    """
    if not image_prompt or image_prompt == "Not Generated":
        # Default image agar prompt miss ho jaye
        return "https://images.unsplash.com/photo-1504711432869-5d39a7402ca2?q=80&w=1000"
    
    # Clean the prompt for URL
    clean_prompt = image_prompt.replace(" ", "_").replace("'", "").replace('"', "")
    
    # Using Pollinations AI with Flux model for high quality
    image_url = f"https://pollinations.ai/p/{clean_prompt}?width=1024&height=768&model=flux&nologo=true&seed=88"
    
    return image_url
