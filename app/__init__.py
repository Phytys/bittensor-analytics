from flask import Flask
from flask_caching import Cache
from app.config import CACHE_TYPE, CACHE_DIR, CACHE_DEFAULT_TIMEOUT
from app.views import main
from app.dash_app import init_dashboard

cache = Cache(config={
    'CACHE_TYPE': CACHE_TYPE,
    'CACHE_DIR': CACHE_DIR,
    'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT
})

def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

def create_app():
    app = Flask(__name__)
    cache.init_app(app)
    app.register_blueprint(main)
    init_dashboard(app, cache)
    
    # Add security headers middleware
    app.after_request(add_security_headers)
    
    return app
