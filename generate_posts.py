import os
import openai
import requests
import feedparser
from datetime import datetime
import re
import subprocess
import json

# Load OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# Cache file for storing previously generated content
CACHE_FILE = "cache.json"

# Load cache
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Save cache
def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache, file)

# Fetch trending topics from Reddit
def get_reddit_trends():
    url = "https://www.reddit.com/r/popular.json"
    headers = {"User-Agent": "DailyBlogBot/0.1"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return [post['data']['title'] for post in data['data']['children']]
    return []

# Fetch trending topics from Google Trends
def get_google_trends():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries]

# Fetch trending topics from News API
def get_news_topics():
    # Load the News API key from the environment variable
    news_api_key = os.getenv("NEWS_API_KEY")
    if not news_api_key:
        raise ValueError("News API key not found. Please set the NEWS_API_KEY environment variable.")

    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={news_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [article['title'] for article in data['articles']]
    return []

# Generate blog content using OpenAI's GPT
def generate_blog_content(topic):
    cache = load_cache()
    if topic in cache:
        print(f"Using cached content for topic: {topic}")
        return cache[topic]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a blogger."},
                {"role": "user", "content": f"Write a short blog post about '{topic}'."}
            ],
            max_tokens=200,  # Reduced token limit to stay within free tier
            temperature=0.7
        )
        content = response['choices'][0]['message']['content']
        cache[topic] = content
        save_cache(cache)
        return content
    except Exception as e:
        print(f"An error occurred while generating content for '{topic}': {e}")
        return "No content generated due to API quota exceeded or other errors."

# Create a Markdown file for the blog post
def create_blog_post(title, content):
    # Sanitize the title to remove invalid characters
    safe_title = re.sub(r'[\\/*?:"<>|]', '', title)  # Remove invalid characters
    safe_title = safe_title.replace(" ", "-").lower()  # Replace spaces with hyphens and make lowercase

    # Truncate the title to a maximum length (e.g., 50 characters)
    max_length = 50
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length]

    # Format the date for the filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"_posts/{date_str}-{safe_title}.md"

    # Create the Markdown content
    markdown_content = f"""---
layout: post
title: "{title}"
date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
categories: trending
---

# {title}

{content}
"""

    # Write the content to the file
    with open(filename, "w", encoding="utf-8") as file:
        file.write(markdown_content)

    print(f"Blog post created: {filename}")

# Push changes to GitHub
def push_to_github():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Add new blog posts"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        print("Changes pushed to GitHub successfully!")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while pushing to GitHub: {e}")

# Main function
def main():
    # Fetch trending topics from all sources
    reddit_trends = get_reddit_trends()
    google_trends = get_google_trends()
    news_trends = get_news_topics()

    all_trends = reddit_trends + google_trends + news_trends

    # Generate a blog post for each topic (limit to 2 posts to stay within rate limits)
    for topic in all_trends[:2]:  # Limit to 2 posts instead of 5
        print(f"Generating blog post for topic: {topic}")
        content = generate_blog_content(topic)  # Use OpenAI to generate content
        create_blog_post(topic, content)

    # Push changes to GitHub
    push_to_github()

if __name__ == "__main__":
    main()