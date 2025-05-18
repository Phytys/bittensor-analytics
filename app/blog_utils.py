import os
import markdown2
import logging
import yaml
from datetime import datetime
import re

BLOG_DIR = "blog"

def get_file_date(filepath):
    """Get the last modification date of a file."""
    timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

def parse_front_matter(content):
    """Parse YAML front matter from markdown content."""
    if not content.startswith('---'):
        return {}, content
    
    try:
        # Split front matter from content
        _, front_matter, content = content.split('---', 2)
        # Parse YAML
        metadata = yaml.safe_load(front_matter)
        return metadata, content.strip()
    except Exception as e:
        logging.error(f"Error parsing front matter: {str(e)}")
        return {}, content

def load_blog_post(slug):
    filepath = os.path.join(BLOG_DIR, f"{slug}.md")
    if not os.path.exists(filepath):
        return None, None
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse front matter
    metadata, content = parse_front_matter(content)
    
    # Set default metadata
    metadata.setdefault('title', 'Untitled')
    # Use file's last modification date
    metadata['date'] = get_file_date(filepath)
    metadata.setdefault('description', '')
    metadata.setdefault('author', 'Bittensor Analytics Team')
    metadata.setdefault('tags', [])
    
    # Remove the title from content if it matches metadata title
    content_lines = content.splitlines()
    if content_lines and content_lines[0].strip().startswith('# '):
        title_in_content = content_lines[0].strip().replace('# ', '').strip()
        if title_in_content == metadata['title'] or title_in_content == metadata['title'].split(':', 1)[1].strip():
            content = '\n'.join(content_lines[1:]).strip()
    
    # Convert markdown to HTML
    html = markdown2.markdown(
        content,
        extras=["fenced-code-blocks", "tables"]
    )
    
    return html, metadata

def list_blog_posts():
    logging.info(f"Listing blog posts from directory: {os.path.abspath(BLOG_DIR)}")
    posts = []
    try:
        for filename in sorted(os.listdir(BLOG_DIR)):
            if filename.endswith(".md"):
                logging.info(f"Found blog post: {filename}")
                slug = filename.replace(".md", "")
                filepath = os.path.join(BLOG_DIR, filename)
                
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    metadata, _ = parse_front_matter(content)
                    
                    # Extract chapter number from filename if it starts with a number
                    chapter_match = re.match(r'^(\d+)_', filename)
                    if chapter_match:
                        metadata['chapter'] = f"Chapter {chapter_match.group(1)}"
                    
                    # Ensure required metadata
                    if 'title' not in metadata:
                        # Fallback to first h1 if no title in metadata
                        for line in content.splitlines():
                            if line.strip().startswith('# '):
                                metadata['title'] = line.strip().replace('# ', '').strip()
                                break
                        if 'title' not in metadata:
                            metadata['title'] = 'Untitled'
                    
                    # Use file's last modification date
                    metadata['date'] = get_file_date(filepath)
                    
                    # Set other default metadata
                    metadata.setdefault('description', '')
                    metadata.setdefault('author', 'Bittensor Analytics Team')
                    metadata.setdefault('tags', [])
                    
                    # Add slug to metadata
                    metadata['slug'] = slug
                
                posts.append(metadata)
                logging.info(f"Added post: {slug} with title: {metadata.get('title')}")
    except Exception as e:
        logging.error(f"Error listing blog posts: {str(e)}")
    logging.info(f"Total posts found: {len(posts)}")
    return posts
