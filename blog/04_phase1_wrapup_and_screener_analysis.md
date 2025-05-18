---
title: "Chapter 4: Wrapping Up Phase 1 — Foundations, Scores, and What's Next"
date: "2024-03-20"
description: "A comprehensive review of Phase 1: building a scalable analytics dashboard, implementing subnet scoring, and laying the groundwork for advanced market analysis in Bittensor's decentralized AI ecosystem."
author: "Bittensor Analytics Team"
tags: ["bittensor", "analytics", "phase 1", "dashboard", "scoring", "market analysis", "decentralized AI", "roadmap", "screener"]
---

# Chapter 4: Wrapping Up Phase 1 — Foundations, Scores, and What's Next

With Phase 1 complete, we've established a scalable dashboard with real-time insights into Bittensor subnets. We've introduced a scoring model that merges fundamentals and trend signals. And we did it with caching, persistence, and a clean UI.

But that brings us to an important question...

> Why did we include these specific metrics in the score? What about all the other fields available?

Let's dive deeper.

---

## 🔍 Screener API: Field Overview

From `/api/beta/subnet_screener`, we get a wide array of fields. Here's a subset:

| Column                        | Description |
|------------------------------|-------------|
| `netuid`                     | Unique subnet ID |
| `subnet_name`                | Human-readable name |
| `price`                      | Alpha token price in TAO |
| `tao_in`                     | Total TAO committed to the subnet |
| `price_1h_pct_change`        | Price % change over 1 hour |
| `price_1d_pct_change`        | Price % change over 1 day |
| `price_7d_pct_change`        | Price % change over 7 days |
| `price_1m_pct_change`        | Price % change over 30 days |
| `alpha_in` / `alpha_out`     | Volume of Alpha tokens in/out |
| `realized_pnl` / `unrealized_pnl` | Profit/loss tracking |
| `github_repo`, `subnet_website`, `discord` | External metadata |

---

## ✅ Why We Chose These Fields for the Score

| Field              | Reason |
|--------------------|--------|
| `tao_in`           | Represents investor/staker confidence |
| `price × tao_in` (market cap) | Reflects value-weighted interest |
| `price_7d_pct_change` | Captures short-term trend momentum |
| `github_repo`      | Proxy for development transparency |
| `subnet_website`   | Signals maturity, legitimacy |

---

## 🧠 Why We Excluded the Rest (for Now)

- **Short-term price swings** (`1h`, `1d`) are too noisy for our score's purpose
- **PnL metrics** require more context (wallet size, time in market)
- **Alpha volume** is interesting — but we may want to look at liquidity ratios instead
- **Root emissions** and emission percent could be valuable later — but we're starting simple

> We're building a **foundation**, not a finished product.

---

## 📌 What We've Built

- 🔗 Real-time subnet data (cached and merged)
- 🧠 A normalized, transparent scoring function
- 🗂️ SQL-based caching with fallback to API
- 📊 A clean, user-facing dashboard with interactive plots
- 📘 Chapters 0–4 to document the journey

This is Phase 1. A milestone. But not the end.

---

## 🚀 Looking Ahead

Phase 2 will include:

- 🪙 Alpha APY (yield)
- 🐋 Holder and decentralization data
- 📈 Historical trend lines (OHLC)
- ♻️ Emission sustainability scores
- 💡 Customizable scoring models

With each addition, our score — and our understanding — will grow.

