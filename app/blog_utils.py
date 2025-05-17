import os
import markdown2
import logging

BLOG_DIR = "blog"

def load_blog_post(slug):
    filepath = os.path.join(BLOG_DIR, f"{slug}.md")
    if not os.path.exists(filepath):
        return None, None
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    html = markdown2.markdown(content, extras=["fenced-code-blocks", "tables", "metadata"])
    # Find first non-empty line that starts with # for title
    for line in content.splitlines():
        if line.strip().startswith('#'):
            return html, line.strip().replace('#', '').strip()
    return html, "Untitled"  # Fallback if no title found

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
                    # Find first non-empty line that starts with # for title
                    title = "Untitled"  # Default title
                    for line in content.splitlines():
                        if line.strip().startswith('#'):
                            title = line.strip().replace('#', '').strip()
                            break
                posts.append({"slug": slug, "title": title})
                logging.info(f"Added post: {slug} with title: {title}")
    except Exception as e:
        logging.error(f"Error listing blog posts: {str(e)}")
    logging.info(f"Total posts found: {len(posts)}")
    return posts
