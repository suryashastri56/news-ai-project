# main.py
import subprocess
import time

def run_automation():
    print("🚀 Fetching News...")
    subprocess.run(["python", "agents/news_fetcher.py"])
    
    print("🤖 Rewriting with AI & SEO...")
    subprocess.run(["python", "agents/ai_rewriter.py"])
    print("✅ All tasks completed!")

if __name__ == "__main__":
    run_automation()