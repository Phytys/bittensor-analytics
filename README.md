# Bittensor Subnet Analytics

_A clean, open-source dashboard and research journal for exploring Bittensor subnet performance._

![Python](https://img.shields.io/badge/python-3.11-blue)
![Heroku](https://img.shields.io/badge/deployed-Heroku-green)
![License](https://img.shields.io/badge/license-MIT-blue)

🔗 **Live App**: [bittensor-analytics on Heroku](https://bittensor-analytics-03fff415a1ae.herokuapp.com/)

---

## Features

- 📊 **Interactive Dashboard**
  - Modern, responsive design with Tesla-inspired aesthetics
  - Collapsible sidebar navigation
  - Real-time subnet metrics visualization
  - Customizable metric selection
  - Sortable data tables with conditional formatting
  - Top subnet rankings
  - Multi-tab interface with subnet metrics analysis
  - APY tracking and stake distribution metrics
  - Economic sustainability indicators
  - Mobile-friendly layout

- 📚 **Research Blog**
  - Markdown-powered blog posts
  - Scoring methodology explained
  - Network trends and insights
  - Protocol analysis and comparisons

---

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Frontend**: Dash, Plotly, Bootstrap
- **Database**: PostgreSQL (Heroku) / SQLite (Dev)
- **Caching**: Flask-Caching (filesystem)
- **Deployment**: Heroku (Gunicorn + WSGI)
- **Styling**: Custom CSS with responsive design

---

## Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/bittensor-dashboard.git
cd bittensor-dashboard
```

2. **Set up and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create a `.env` file**
```bash
echo "TAO_APP_API_KEY=your_api_key" >> .env
echo "FLASK_ENV=development" >> .env
echo "DATABASE_URL=sqlite:///tao_cache.db" >> .env
```

5. **Run the app locally**
```bash
python -m flask run
```

Visit `http://localhost:5000` in your browser.

---

## Deployment (Heroku)

The app is deployed to:

🔗 [https://bittensor-analytics-03fff415a1ae.herokuapp.com](https://bittensor-analytics-03fff415a1ae.herokuapp.com)

### Heroku Setup Steps

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set TAO_APP_API_KEY=your_key_here
git push heroku main
```

Heroku will automatically detect Python and install via `requirements.txt`.

---

## Project Structure

```
bittensor-dashboard/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── views.py           # Flask routes (landing, blog)
│   ├── dash_app/          # Dashboard components
│   │   ├── __init__.py    # Dash app initialization
│   │   ├── layout.py      # Main dashboard layout
│   │   └── pages/         # Dashboard pages
│   │       ├── overview.py    # Overview metrics
│   │       └── metrics.py     # Subnet metrics (APY, stats)
│   ├── subnet_metrics.py  # Subnet metrics aggregation and APY logic
│   ├── blog_utils.py      # Markdown rendering
│   ├── logic.py           # Subnet scoring
│   ├── utils.py           # API integration and caching
│   ├── models.py          # Database models
│   ├── config.py          # Env config
│   ├── limiter.py         # Rate limiting
│   ├── static/            # Logo, favicon, CSS
│   └── templates/         # HTML pages
├── app/scripts/
│   └── run_apy_warmup.py  # Script to collect and store APY data
├── tests/                 # Test suite
│   ├── __init__.py        # Makes tests a package
│   └── test_fundamentals.py  # APY collection tests (may be renamed)
├── blog/                  # Markdown blog posts (book chapters)
├── data/                  # Data storage and cache
├── requirements.txt       # Dependency list
├── Procfile               # Heroku startup instruction
├── runtime.txt            # Python version
├── wsgi.py                # Production WSGI entry point
└── README.md             # This file
```

---

- The main dashboard page for subnet metrics is now `metrics.py` (was `fundamentals.py`).
- The backend logic for subnet APY and metrics is in `subnet_metrics.py` (was `fundamentals.py`).
- The APY warmup script is in `app/scripts/run_apy_warmup.py`.
- Update test file names if you wish for consistency (e.g., `test_subnet_metrics.py`).

If you have any questions or need to update other documentation, let me know!

---

## Security

The app implements key protections:

- ✅ HTTP security headers (HSTS, X-Frame, MIME-sniffing)
- ✅ Rate limiting with Flask-Limiter
- ✅ Environment variable validation
- ✅ Secure API key and database access
- ✅ Custom error pages (404, 500)
- ✅ Pinned & audited dependencies

---

## License

MIT License

---

## Contact

X: [@_landgren_](https://twitter.com/_landgren_)  

---

_This app was built to explore, visualize, and communicate the evolving landscape of decentralized AI networks using Bittensor._ 