import requests
import feedparser
import wikipediaapi
import re
from datetime import datetime
import subprocess


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
def get_news_topics(api_key):
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [article['title'] for article in data['articles']]
    return []

def get_wikipedia_summary(topic):
    wiki = wikipediaapi.Wikipedia(
        language='en',
        user_agent='DailyTrendingBlog/1.0 (chandravinnakota3@gmail.com)'  # Replace with your email or identifier
    )
    page = wiki.page(topic)
    if page.exists():
        return page.summary
    return "No information found on Wikipedia."

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

# Push the changes to GitHub
def push_to_github():
    try:
        # Stage all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit the changes
        subprocess.run(["git", "commit", "-m", "Add new blog posts"], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "master"], check=True)
        
        print("Changes pushed to GitHub successfully!")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while pushing to GitHub: {e}")

# Main function to fetch topics and generate posts
def main():
    # Fetch trending topics from all sources
    reddit_trends = get_reddit_trends()
    google_trends = get_google_trends()
    news_api_key = "f0a5319f3d4849539cf681ae8783bc25"
    news_trends = get_news_topics(news_api_key)

    all_trends = reddit_trends + google_trends + news_trends

    # Generate a blog post for each topic
    for topic in all_trends[:5]:  # Limit to 5 posts for testing
        summary = get_wikipedia_summary(topic)
        create_blog_post(topic, summary)
    
    push_to_github()

if __name__ == "__main__":
    main()