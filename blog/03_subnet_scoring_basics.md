
# Chapter 3: Subnet Scoring — Our First Model

In the previous chapter, we examined the fundamental structure of each subnet — from its TAO holdings and price to metadata like GitHub links and community presence. Now, we take our first step into building something more opinionated:

> A scoring model to assess and rank Bittensor subnets using a blend of fundamentals and momentum.

This score isn't meant to be perfect or absolute. It’s meant to be **interpretable**, **data-driven**, and evolve over time. Phase 1 focuses on a simple yet insightful version of this score.

---

## 🧮 What's in the Score?

The **score** is a weighted combination of signals we believe represent quality and potential. Here's what we're using:

| Feature                 | Why We Use It |
|-------------------------|-----------------------------|
| `tao_in_screener`       | Reflects stake and trust — how much TAO is committed to the subnet |
| `market_cap_proxy`      | TAO-in × price — captures value-weighted interest |
| `price_7d_pct_change`   | Measures recent trend and momentum |
| `github_repo_screener`  | Suggests transparency and open development |
| `subnet_website_screener` | Signals communication and project maturity |

Each field is normalized to a 0–1 scale before being combined into the final score.

---

## 🔢 The Scoring Formula

```python
score = (
    norm(tao_in)           * 0.20 +
    norm(market_cap)       * 0.15 +
    norm(price_7d_change)  * 0.10 +
    has_github             * 0.05 +
    has_website            * 0.05
)
```

These weights are configurable and stored in `config.py`, allowing for easy experimentation in Phase 2.

---

## 📊 The Dashboard in Action

The interactive dashboard now includes:

- A **dropdown** to explore different metrics
- A **bar chart** of the top 15 subnets by selected metric
- A **sortable table** showing all available columns
- A **cached backend** powered by SQLite and SQLAlchemy

_(📸 Screenshot of current dashboard here)_

---

## ⏭️ Up Next

Now that we’ve defined a baseline score and visualized it, the next step is to reflect on **why we chose these fields**, what the screener API offers, and how our model can grow.

In Chapter 4, we’ll break down the screener dataset and explain why we excluded many fields — for now.
