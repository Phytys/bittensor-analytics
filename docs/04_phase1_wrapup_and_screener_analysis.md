
# Chapter 4: Wrapping Up Phase 1 — Foundations, Scores, and What's Next

With Phase 1 complete, we've built a solid, scalable dashboard that integrates real-time subnet data from the Bittensor network. We introduced a scoring model, cleaned and normalized data, and cached everything locally for efficiency. 

But an important question remains: **Why did we choose those specific fields for the score?** What about the many other columns returned by the API?

This chapter answers that — and maps the terrain for future upgrades.

---

## 🔌 The Subnet Screener API: Field Reference

From `/api/beta/subnet_screener`, we receive a wide range of subnet metrics. Here's what they mean:

| Column                        | Description |
|------------------------------|-------------|
| `netuid`                     | Subnet identifier (primary key) |
| `subnet_name`                | Human-readable subnet name |
| `price`                      | Current Alpha token price (in TAO) |
| `price_1h_pct_change`        | Price % change over the last 1 hour |
| `price_1d_pct_change`        | Price % change over the last 1 day |
| `price_7d_pct_change`        | Price % change over the last 7 days |
| `price_1m_pct_change`        | Price % change over the last 30 days |
| `alpha_in`, `alpha_out`      | Volume in/out of Alpha tokens |
| `tao_in`                     | TAO staked into the subnet (TVL proxy) |
| `emission_pct`               | % of total TAO emissions going to this subnet |
| `unrealized_pnl`, `realized_pnl` | PnL metrics for Alpha holders |
| `github_repo`, `subnet_website`, `discord` | Project metadata |
| `root_prop`                  | Share of global root emissions |
| ...                          | (and a few others we may explore later) |

---

## ✅ Fields Included in Our Basic Score

We selected a small, meaningful subset to define an early subnet score:

| Feature             | Why We Included It |
|---------------------|---------------------|
| `tao_in`            | Capital allocation, community trust |
| `price`             | Value signal, demand proxy |
| `price_7d_pct_change` | Captures momentum, short-term trend |
| `github_repo`       | Open-source presence & credibility |
| `subnet_website`    | Communication, trust-building |

---

## 🤔 Why Not Use the Other Fields (Yet)?

Great question. We plan to — but thoughtfully, and incrementally.

Some fields (e.g., `price_1h_pct_change`) are noisy or hyper-volatile, better suited for real-time trading dashboards. Others like `unrealized_pnl` and `alpha_in/out` are extremely valuable — but only in context, or when combined into higher-order metrics like "Liquidity Stability Score."

By **starting simple**, we:
- Avoid overfitting or noisy metrics
- Build user trust by keeping the score interpretable
- Lay the groundwork for more sophisticated models in Phase 2 and beyond

---

## 🧱 What We've Built So Far

- 📥 Real-time data fetching from two key endpoints
- 🧠 A scoring function built on normalized signals
- 🗃️ Caching layer using SQLite and SQLAlchemy
- 🚀 Flask-Caching for interactive, responsive UX
- 📊 Plotly Dash frontend with graphs and tables
- 📸 Snapshot of the dashboard inserted into Chapter 3
- 📚 Documentation alongside development

This is our **baseline** — functional, fast, and extensible.

---

## 📘 Up Next

In Phase 2, we’ll begin expanding our analysis in these directions:
- 🪙 Alpha APY: Which subnets offer real yield?
- 🐳 Holders: Are whales dominating, or is ownership decentralized?
- ⚖️ Sustainability: Can emission rates be maintained long term?
- 📈 Time Series: Visual trendlines with OHLC data
- 🧠 Composite Index: Combine more metrics into tiered subnet profiles

> Our scoring model will evolve, but always remain explainable.

This book — and this codebase — will evolve with it.

