from flask import Blueprint, render_template, abort
from app.blog_utils import list_blog_posts, load_blog_post
import logging

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', title="Bittensor Subnet Analytics")

@main.route('/blog')
def blog_index():
    posts = list_blog_posts()
    logging.info(f"Loaded blog posts: {posts}")  # Debug log
    return render_template('blog_index.html', posts=posts, title="Blog")

@main.route('/blog/<slug>')
def blog_post(slug):
    html, title = load_blog_post(slug)
    if not html:
        abort(404)
    return render_template('blog_post.html', title=title, content=html)

