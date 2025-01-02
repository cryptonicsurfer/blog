import os
from datetime import datetime
import frontmatter
import markdown
from openai import OpenAI
from git import Repo
import yaml
from pathlib import Path

class BlogAutomation:
    def __init__(self, blog_dir, github_token, gemini_api_key, site_url, app_name):
        # Expand ~ to the actual home directory and make path absolute
        self.blog_dir = Path(blog_dir).expanduser().resolve()
        self.blogs_dir = self.blog_dir / '_posts'  # Changed from 'blogs' to '_posts' for Jekyll
        self.github_token = github_token
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=gemini_api_key
        )
        self.site_url = site_url
        self.app_name = app_name
        
        # Ensure posts directory exists
        self.blogs_dir.mkdir(parents=True, exist_ok=True)

    def setup_github_pages(self):
        """Setup necessary files for GitHub Pages"""
        # Create _config.yml for Jekyll
        config_content = f"""
title: {self.app_name}
description: An automated blog using AI
theme: minima
plugins:
  - jekyll-feed
  - jekyll-sitemap

permalink: /:year/:month/:day/:title/
"""
        config_file = self.blog_dir / '_config.yml'
        config_file.write_text(config_content)
        
        # Create index.md
        index_content = f"""---
layout: home
title: Welcome to {self.app_name}
---

Welcome to my automated blog! Here you'll find all my posts about various topics.
"""
        index_file = self.blog_dir / 'index.md'
        index_file.write_text(index_content)
        
    def get_github_pages_url(self):
        """Get the GitHub Pages URL based on the repository"""
        try:
            repo = Repo(self.blog_dir)
            remote_url = repo.remotes.origin.url
            
            if 'github.com' in remote_url:
                if remote_url.startswith('git@'):
                    # SSH URL format
                    path = remote_url.split(':')[1].replace('.git', '')
                else:
                    # HTTPS URL format
                    path = remote_url.split('github.com/')[1].replace('.git', '')
                
                username, repo_name = path.split('/')
                return f"https://{username}.github.io/{repo_name}"
        except Exception as e:
            print(f"Could not determine GitHub Pages URL: {e}")
            return None
        
    def get_default_style_guide(self):
        """Provide default style guidelines when no existing posts are available"""
        return """
Title: Understanding Blockchain Technology
Date: 2025-01-01

Blockchain technology has revolutionized the way we think about digital transactions and data security. In this post, we'll explore the fundamental concepts and their implications for the future.

The core principle behind blockchain is decentralization. Rather than relying on a central authority, transactions are verified by a network of participants. This creates a system that's both transparent and secure.

Let's break this down into practical terms. When you make a transaction on a blockchain, it's grouped with others into a 'block'. This block is then verified by network participants through complex mathematical calculations. Once verified, it's added to the chain of previous blocks - hence the name 'blockchain'.

The implications of this technology extend far beyond cryptocurrency. From supply chain management to digital identity verification, blockchain is reshaping how we handle data and trust in the digital age.

In future posts, we'll dive deeper into specific applications and explore emerging trends in this fascinating field.
"""

    def analyze_existing_posts(self, num_posts=5):
        """Analyze recent posts to understand the writing style"""
        posts = []
        post_files = sorted(self.blogs_dir.glob("*.md"), reverse=True)
        
        if not post_files:  # If no existing posts, use default style guide
            default_post = {
                'title': 'Style Guide',
                'content': self.get_default_style_guide(),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            return [default_post]
        
        for post_file in post_files[:num_posts]:
            with open(post_file) as f:
                post = frontmatter.load(f)
                posts.append({
                    'title': post.metadata.get('title'),
                    'content': post.content,
                    'date': post.metadata.get('date')
                })
        return posts

    def generate_post(self, topic, existing_posts):
        """Generate a new blog post maintaining consistent style"""
        style_examples = "\n\n".join([
            f"Title: {post['title']}\n{post['content']}" 
            for post in existing_posts[:2]
        ])
        
        is_first_post = len(list(self.blogs_dir.glob("*.md"))) == 0
        
        if is_first_post:
            prompt = f"""You are writing the first post for a new blog about {topic}.
The style should be:
- Clear and engaging
- Professional but conversational
- Well-structured with clear paragraphs
- Include an introduction and conclusion
- Approximately 500 words in length

Please write a blog post about {topic} following these guidelines."""
        else:
            prompt = f"""Based on these previous blog posts that show my writing style:

{style_examples}

Please write a new blog post about {topic} that maintains a similar tone, style, and format.
The post should include a title and maintain similar paragraph length and structure."""

        print("\nSending request to API with prompt:", prompt[:200], "...")
        
        try:
            completion = self.client.chat.completions.create(
                model="gemini-2.0-flash-exp",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            print("\nAPI Response received:")
            print("Response type:", type(completion))
            print("Response content:", completion)
            
            if completion and completion.choices:
                return completion.choices[0].message.content
            else:
                raise ValueError("No content received from API")
                
        except Exception as e:
            print(f"Error in generate_post: {type(e).__name__} - {str(e)}")
            raise

    def create_post_file(self, content, topic):
        """Create a new markdown file with proper frontmatter"""
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
        
        # Save to file in blogs directory
        file_path = self.blogs_dir / f"{today}-{slug}.md"
        with open(file_path, 'wb') as f:
            frontmatter.dump(post, f)
            
        return file_path

    def publish_to_github(self, file_path, commit_message):
        """Push new post to GitHub repository"""
        try:
            repo = Repo(self.blog_dir)
        except:
            # Initialize repository if it doesn't exist
            repo = Repo.init(self.blog_dir)
            
        repo.index.add([str(file_path.relative_to(self.blog_dir))])
        repo.index.commit(commit_message)
        
        try:
            origin = repo.remote('origin')
        except ValueError:
            print("No remote 'origin' found. Please set up your GitHub remote manually.")
            return
            
        origin.push()

    def run_automation(self, topic):
        """Run the full automation process"""
        # Setup GitHub Pages if not already set up
        if not (self.blog_dir / '_config.yml').exists():
            self.setup_github_pages()
            
        existing_posts = self.analyze_existing_posts()
        new_content = self.generate_post(topic, existing_posts)
        file_path = self.create_post_file(new_content, topic)
        commit_message = f"Add new blog post: {topic}"
        self.publish_to_github(file_path, commit_message)
        
        # Get and display the GitHub Pages URL
        pages_url = self.get_github_pages_url()
        if pages_url:
            print(f"\nYour blog is available at: {pages_url}")
            print("Note: It may take a few minutes for GitHub Pages to build and deploy your site.")
        
        return file_path


# Example usage
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
    
    topic = "The Future of AI in Content Creation - in Swedish ONLY"
    new_post_path = automation.run_automation(topic)
    print(f"Published new post: {new_post_path}")