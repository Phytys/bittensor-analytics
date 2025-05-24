# Bittensor Subnet Analytics Dashboard

_A modern, open-source dashboard and research journal for exploring Bittensor subnet performance, validator economics, and protocol analytics._

![Python](https://img.shields.io/badge/python-3.11-blue)
![Heroku](https://img.shields.io/badge/deployed-Heroku-green)
![License](https://img.shields.io/badge/license-MIT-blue)

🔗 **Live App**: [bittensor-analytics on Heroku](https://bittensor-analytics-03fff415a1ae.herokuapp.com/)

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [File & Folder Overview](#file--folder-overview)
- [Data Collection Pipeline](#data-collection-pipeline)
- [Dash Pages & Visualizations](#dash-pages--visualizations)
- [Flask Endpoints](#flask-endpoints)
- [Security](#security)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- **Subnet Metrics Page:**
  - APY distribution boxplots per subnet (with outlier filtering, log scale toggle)
  - Scatter plot: Subnet mean APY vs. TAO market cap (color/size by price change)
  - Validator distribution by org, vTrust, and stake (top 64, top 10 orgs)
  - Emission rate chart: % of TAO emitted to subnet reward pool vs. market cap
  - All charts use protocol-accurate metrics and language
  - Responsive, professional UI with Plotly and Dash Bootstrap Components
- **CoinGecko Integration:**
  - Daily TAO price caching for accurate USD calculations
- **Data Pipeline:**
  - Aggregates, caches, and joins data from Bittensor APIs and CoinGecko
  - Protocol-accurate APY, emission, and validator metrics
- **Blog & Research:**
  - Markdown-based blog for research posts and protocol analysis
- **Security:**
  - Rate limiting, API key management, secure error handling

---

## Project Structure

```
bittensor-dashboard/
├── app/
│   ├── __init__.py
│   ├── views.py
│   ├── dash_app/
│   │   ├── __init__.py
│   │   ├── layout.py
│   │   └── pages/
│   │       ├── overview.py
│   │       └── subnet_metrics_page.py
│   ├── subnet_metrics.py
│   ├── blog_utils.py
│   ├── logic.py
│   ├── utils.py
│   ├── models.py
│   ├── config.py
│   ├── limiter.py
│   ├── static/
│   ├── templates/
│   └── scripts/
│       ├── run_apy_warmup.py
│       └── warmup_base.py
├── tests/
│   ├── __init__.py
│   ├── test_subnet_metrics.py
│   └── test_utils.py
├── blog/
├── data/
├── cache/
├── requirements.txt
├── Procfile
├── runtime.txt
├── wsgi.py
├── README.md
```

---

## File & Folder Overview

### `app/`
- Core logic, Dash app, and Flask backend.
- `subnet_metrics.py`: Data aggregation and protocol metrics
- `dash_app/pages/subnet_metrics_page.py`: Main subnet metrics dashboard page

### `tests/`
- Unit and integration tests for core logic and data collection.

### `blog/`
- Markdown blog posts and research articles.

### `data/`, `cache/`
- Local data storage and cache (including TAO price, API responses, and APY data).

---

## Data Collection Pipeline

```
[TAO.app API, CoinGecko API]
     ↓
[fetch_and_cache_json(), fetch_and_cache_tao_price()]
     ↓
[Cache Tables: subnet_info, subnet_screener, tao_price]
     ↓
[Aggregation: subnet_apy (validator-level, subnet-level), emission rates, price changes]
     ↓
[Dash/Flask: Visualizations, Tables, Endpoints]
```
- **APY data**: Aggregated per subnet, with validator-level stats (min, max, mean, median, std, count)
- **TAO price**: Fetched daily from CoinGecko, cached for up to 1 year
- **All USD calculations**: Use global TAO price for accuracy

---

## Dash Pages & Visualizations

- **Overview**: High-level protocol stats, TAO price, and network summary
- **Subnet Metrics**:
  - APY distribution boxplots (per subnet, validator-level)
  - Scatter: Subnet mean APY vs. TAO market cap (color/size by price change)
  - Validator distribution by org, vTrust, and stake (top 64, top 10 orgs)
  - Emission rate chart: % of TAO emitted to subnet reward pool vs. market cap
  - All charts: Responsive, log scale toggles, outlier filtering, protocol-accurate tooltips
- **Blog**: Markdown-based research posts and protocol analysis

---

## Flask Endpoints

- `/` – Landing page
- `/blog` – Blog index
- `/blog/<slug>` – View blog post
- `/health` – Health check
- `/about-bittensor` – Redirects to main Bittensor blog post
- `/api/tao_price` – Cached TAO price endpoint
- `/api/subnet_metrics` – Aggregated subnet metrics (APY, emission, etc.)

---

## Security

- Rate limiting (Flask-Limiter)
- API key management (via `.env`)
- Secure error pages
- Dependency pinning (`requirements.txt`)
- Never expose sensitive keys or credentials in logs or UI

---

## Local Development

```bash
git clone https://github.com/yourusername/bittensor-dashboard.git
cd bittensor-dashboard
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Set up .env with TAO_APP_API_KEY, COINGECKO_API_KEY, FLASK_ENV, DATABASE_URL
python -m flask run
```

---

## Deployment

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set TAO_APP_API_KEY=your_key
heroku config:set COINGECKO_API_KEY=your_key
heroku config:set FLASK_ENV=production
heroku config:set DATABASE_URL=your_db_url
# Push code
git push heroku main
```

---

## Contributing

Contributions are welcome! Please open issues or pull requests for bug fixes, new features, or documentation improvements.
- Follow PEP8 and best practices for Python and Dash
- Add/maintain docstrings and type hints
- Write tests for new features (`tests/`)
- Keep protocol language and metrics accurate

---

## License

MIT License

---

## Contact

- Twitter/X: [@_landgren_](https://twitter.com/_landgren_)
- For questions, open an issue or contact via Twitter/X

---

_This dashboard is built to explore, visualize, and communicate the evolving landscape of decentralized AI networks using Bittensor. For a deep dive into subnet metrics, see our upcoming blog post._