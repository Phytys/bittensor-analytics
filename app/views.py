from flask import Blueprint, render_template, abort
from app.blog_utils import list_blog_posts, load_blog_post
from app.limiter import limiter
from app.config import RATE_LIMITS
import logging

main = Blueprint('main', __name__)

@main.route('/')
@limiter.limit(RATE_LIMITS["default"])
def index():
    return render_template('index.html', title="Bittensor Subnet Analytics")

@main.route('/blog')
@limiter.limit(RATE_LIMITS["blog"])
def blog_index():
    posts = list_blog_posts()
    logging.info(f"Loaded blog posts: {posts}")  # Debug log
    return render_template('blog_index.html', posts=posts, title="Blog")

@main.route('/blog/<slug>')
@limiter.limit(RATE_LIMITS["blog"])
def blog_post(slug):
    html, title = load_blog_post(slug)
    if not html:
        abort(404)
    return render_template('blog_post.html', title=title, content=html)

@main.route('/health')
@limiter.exempt  # Health checks should never be rate limited
def health_check():
    return {'status': 'healthy'}, 200

@main.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html', title="Page Not Found"), 404

@main.app_errorhandler(500)
def internal_error(error):
    logging.error(f"Server Error: {error}")
    return render_template('500.html', title="Server Error"), 500

