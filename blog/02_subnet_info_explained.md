---
title: "Chapter 2: Dissecting the Subnet Info API"
date: "2024-03-20"
description: "A deep dive into Bittensor's subnet analytics using the tao.app API. Learn how to access and interpret subnet data through the /api/beta/analytics/subnets/info endpoint, from validator counts to emission rates, and understand what these metrics mean for network health."
author: "Bittensor Analytics Team"
tags: ["bittensor", "tao.app", "API", "subnet", "data", "analytics", "metrics", "network health", "validators", "emission"]
---

# Chapter 2: Dissecting the Subnet Info API

In this chapter, we'll explore how we use the `tao.app` API to gather subnet data for our analytics dashboard. The `/api/beta/analytics/subnets/info` endpoint provides us with a complete snapshot of all active subnets in the network.

## Understanding the Subnet Info Endpoint

Each row in the `/api/beta/analytics/subnets/info` response corresponds to a **subnet** — a specialized mini-network within Bittensor. Here's what each field tells us about a subnet:

| Field              | Description |
|--------------------|-------------|
| `netuid`           | Unique ID of the subnet. All on-chain data references this identifier. |
| `subnet_name`      | Optional human-readable name (registered by subnet owner). |
| `price`            | Current market price of the subnet's ALPHA token in TAO. |
| `tao_in`           | Total TAO staked into this subnet. A proxy for trust and capital allocation. |
| `alpha_in`         | Alpha tokens entering the subnet from users or validators. |
| `alpha_out`        | Alpha tokens withdrawn from the subnet. Useful for flow analysis. |
| `root_prop`        | Proportion of global TAO emissions allocated to this subnet. |
| `owner_hotkey`     | Hotkey identity of the operator (on-chain). |
| `owner_coldkey`    | Coldkey identity of the owner (can be linked to external wallets). |
| `github_repo`      | Self-declared GitHub repo. Not validated, but useful for fundamental research. |
| `subnet_website`   | Website link (optional). Can be used to extract more info about team/project. |
| `discord`          | Community or operator Discord server (if available). |
| `tempo`            | On-chain setting related to block timing / emission control. |
| `symbol`           | Symbol of the subnet's ALPHA token (not always populated). |

Together, these form the **fundamental profile** of each subnet.

In the next chapter, we'll build the logic to fetch, clean, and visualize this data — and begin identifying patterns that hint at quality, risk, or early opportunity.
