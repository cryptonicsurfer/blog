import os
from datetime import datetime
import frontmatter
from openai import OpenAI
from git import Repo
import yaml
from pathlib import Path

class BlogAutomation:
    def __init__(self, blog_dir, github_token, gemini_api_key, site_url, app_name):
        self.blog_dir = Path(blog_dir).resolve()
        self.posts_dir = self.blog_dir / '_posts'
        self.github_token = github_token
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=gemini_api_key
        )
        self.site_url = site_url
        self.app_name = app_name
        
        # Ensure posts directory exists
        self.posts_dir.mkdir(exist_ok=True)

    def setup_github_pages(self):
        """Setup necessary files for GitHub Pages"""
        config_content = f"""
title: {self.app_name}
description: An AI-powered blog
baseurl: "/blog"
url: "https://cryptonicsurfer.github.io"
theme: minima

plugins:
  - jekyll-feed
  - jekyll-sitemap

permalink: /:year/:month/:day/:title/
"""
        config_file = self.blog_dir / '_config.yml'
        config_file.write_text(config_content)
        
        index_content = """---
layout: home
title: Welcome
---

Welcome to my AI-powered blog! Check out my latest posts below:
"""
        index_file = self.blog_dir / 'index.md'
        index_file.write_text(index_content)

    def generate_post(self, topic):
        """Generate a new blog post"""
        prompt = f"""Write a blog post about {topic}. The post should be:
- Clear and engaging
- Professional but conversational
- Well-structured with clear paragraphs
- Include an introduction and conclusion
- Approximately 500 words in length

Please write the blog post following these guidelines."""

        print("\nGenerating blog post about:", topic)
        
        try:
            completion = self.client.chat.completions.create(
                model="gemini-2.0-flash-exp",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            if completion and completion.choices:
                return completion.choices[0].message.content
            else:
                raise ValueError("No content received from API")
                
        except Exception as e:
            print(f"Error generating post: {str(e)}")
            raise

    def create_post_file(self, content, topic):
        """Create a new markdown file with frontmatter"""
        today = datetime.now().strftime('%Y-%m-%d')
        slug = topic.lower().replace(' ', '-')
        
        # Parse the generated content to separate title and body
        lines = content.strip().split('\n')
        title = lines[0].replace('# ', '').replace('Title: ', '')
        body = '\n'.join(lines[1:])
        
        # Create frontmatter
        post = frontmatter.Post(
            body,
            title=title,
            date=today,
            slug=slug,
            layout='post'
        )
        
        # Save to file
        file_path = self.posts_dir / f"{today}-{slug}.md"
        with open(file_path, 'wb') as f:
            frontmatter.dump(post, f)
            
        return file_path

    def publish_to_github(self, file_path, commit_message):
        """Push new post to GitHub repository"""
        try:
            repo = Repo(self.blog_dir)
            repo.index.add([str(file_path.relative_to(self.blog_dir))])
            repo.index.commit(commit_message)
            repo.remote('origin').push()
        except Exception as e:
            print(f"Error publishing to GitHub: {str(e)}")
            raise

    def run_automation(self, topic):
        """Run the full automation process"""
        # Setup GitHub Pages if not already set up
        if not (self.blog_dir / '_config.yml').exists():
            self.setup_github_pages()
        
        # Generate and publish post
        content = self.generate_post(topic)
        file_path = self.create_post_file(content, topic)
        commit_message = f"Add new blog post: {topic}"
        self.publish_to_github(file_path, commit_message)
        
        print(f"\nBlog post published successfully!")
        print(f"View your blog at: https://cryptonicsurfer.github.io/blog/")
        print(f"New post: {file_path}")
        
        return file_path


if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    automation = BlogAutomation(
        blog_dir=config['blog_dir'],
        github_token=config['github_token'],
        gemini_api_key=config['gemini_api_key'],
        site_url=config['site_url'],
        app_name=config['app_name']
    )
    
    topic = input("Enter blog post topic: ")
    new_post_path = automation.run_automation(topic)