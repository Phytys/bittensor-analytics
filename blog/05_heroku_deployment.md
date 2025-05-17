# Chapter 5: Deployment and Going Public

After days of building, iterating, and refining our data-driven insights platform, we reached a pivotal milestone: **it's time to share it with the world.**

In this chapter, we walk through the practical — and philosophical — process of deploying the Bittensor Subnet Analytics project and what it means to take a research tool live.

---

## 🌐 The Goal

We set out to make a Bittensor analytics platform that was:

- **Open** — accessible to anyone interested in decentralized AI
- **Transparent** — powered by on-chain data, rendered with clarity
- **Scalable** — ready for public use and future features
- **Secure** — safe for users and sustainable to maintain

With our dashboard built and our blog written, the final piece was a robust, production-grade deployment.

---

## 🚀 Deployment Stack

We chose **Heroku** for its simplicity, scalability, and tight integration with Git and PostgreSQL. The architecture includes:

- Flask as the core web server
- Dash for the interactive dashboard
- PostgreSQL for persistent caching in production
- Static Markdown blog posts for performance and clarity
- Gunicorn as the production WSGI server

### 🧱 Files Added:

- `Procfile` – tells Heroku how to launch the app
- `wsgi.py` – production entry point
- `.env` (not committed) – stores API keys securely
- `runtime.txt` – sets Python version

---

## 🛡️ Securing the App

Before deploying, we implemented core security measures:

- **HTTP Security Headers**: HSTS, MIME-sniffing prevention, X-Frame protection
- **Environment Variable Validation**: Ensures `TAO_APP_API_KEY` is set
- **Error Pages**: Custom 404 and 500 templates with proper logging
- **Dependency Auditing**: All versions pinned and known vulnerabilities patched
- **Rate Limiting**: Simple in-memory rate limiting with Flask-Limiter

The rate limiting is intentionally simple:
- 60 requests/minute for the homepage
- 30 requests/minute for blog pages
- Health check endpoint is exempt from limits
- In-memory storage (sufficient for our single-dyno deployment)

---

## 🧪 Health and Monitoring

To keep things stable, we added:

- A `/health` endpoint that returns `{"status": "healthy"}` (used by Heroku for uptime checks)
- Basic error logging to Heroku's Logplex
- Rate limiting to prevent abuse
- Environment variable validation to fail fast if config is missing

The health check is particularly important for Heroku's platform. Note how we exempt it from rate limiting to ensure uptime monitoring isn't blocked:

```python
@main.route('/health')
@limiter.exempt  # ensures uptime monitoring isn't blocked
def health_check():
    return {"status": "healthy"}, 200
```

---

## 🖼️ The Final Result

The app now consists of:

- A sleek **landing page** with Tesla-inspired aesthetics
- A sortable, real-time **dashboard** at `/dashboard`
- A Markdown-powered **blog** of our research journey at `/blog`

![Live Dashboard Screenshot](/static/blog-images/dashboard_phase1.png)

_(Note: This screenshot captures the dashboard as deployed at the end of Phase 1.)_

---

## 📣 Going Public

With the app live at:

🔗 [https://bittensor-analytics-03fff415a1ae.herokuapp.com](https://bittensor-analytics-03fff415a1ae.herokuapp.com)

...we could finally share it on:
- Twitter / X
- Reddit's [r/bittensor_](https://www.reddit.com/r/bittensor_)
- Developer groups and Telegram chats

This wasn't just a technical deployment — it was a publishing event. The work we'd done was now visible, usable, and open to feedback.

---

## ⏭️ Next Up

With a stable platform and publishing pipeline in place, we're ready to return to the data itself. In Phase 2, we'll explore:

- **Alpha APY and emission analysis**
- **Subnet holder decentralization**
- **Sustainability metrics**
- **More robust scoring models**

This is just the beginning. 