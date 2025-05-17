
# Chapter 2: Dissecting the Subnet Info API

Our first step is understanding `/api/beta/analytics/subnets/info` — the gateway to all active subnets.

Each row in this endpoint corresponds to a **subnet**, a specialized mini-network within Bittensor. Here's what the fields mean:

| Field              | Description |
|--------------------|-------------|
| `netuid`           | Unique ID of the subnet. All on-chain data references this. |
| `subnet_name`      | Optional human-readable name (registered by subnet owner). |
| `price`            | Current market price of the subnet’s ALPHA token in TAO. |
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
| `symbol`           | Symbol of the subnet’s ALPHA token (not always populated). |

Together, these form the **fundamental profile** of each subnet.

In the next chapter, we’ll build the logic to fetch, clean, and visualize this data — and begin identifying patterns that hint at quality, risk, or early opportunity.
