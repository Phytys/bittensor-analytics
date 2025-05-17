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

def create_app():
    app = Flask(__name__)
    cache.init_app(app)
    app.register_blueprint(main)
    init_dashboard(app, cache)
    return app
