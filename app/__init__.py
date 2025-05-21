from flask import Flask
from flask_caching import Cache
from app.config import CACHE_TYPE, CACHE_DIR, CACHE_DEFAULT_TIMEOUT
from app.views import main
from app.dash_app import init_dashboard
from app.limiter import limiter
from app.models import init_db

# Initialize cache
cache = Cache()

def create_app():
    app = Flask(__name__)
    
    # Configure cache
    app.config.update(
        CACHE_TYPE=CACHE_TYPE,
        CACHE_DIR=CACHE_DIR,
        CACHE_DEFAULT_TIMEOUT=CACHE_DEFAULT_TIMEOUT
    )
    
    # Initialize cache with app
    cache.init_app(app)
    
    # Initialize Dash app
    dash_app = init_dashboard(app)
    
    # Register blueprints
    app.register_blueprint(main)
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Add security headers middleware
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
    app.after_request(add_security_headers)
    
    return app
