# Example Run

> Real run against a 2026-Q1 hack victim address — funds traced from the compromised treasury through bridges and DEX swaps to terminal CEX deposits.
> Model: mimo-v2.5-pro · 7 agents · max_depth=6

## Source

```
Address: 0x7ab2...c9d1 (DeFi protocol treasury, drained 2026-04-18)
Loss: $4.2M USD (USDC + WETH)
Tag: hack_victim
```

## Hop expansion

| Depth | Type | From | To | Value USD | Primitive | Confidence |
|---:|---|---|---|---:|---|---:|
| 1 | direct | 0x7ab2...c9d1 | 0xdef0...0a45 | 4,180,000 | transfer | 0.99 |
| 2 | swap | 0xdef0...0a45 | (Curve 3pool) | 3,950,000 | USDC→USDT | 0.97 |
| 3 | bridge | 0xdef0...0a45 | Stargate USDT | 3,920,000 | bridge | 0.96 |
| 4 | direct | (arb) 0xfed1...321 | 0xa701...77b2 | 1,950,000 | transfer | 0.94 |
| 4 | direct | (arb) 0xfed1...321 | 0xc83c...9911 | 1,950,000 | transfer | 0.94 |
| 5 | swap | 0xa701...77b2 | (Uniswap v3) | 1,940,000 | USDT→ETH | 0.92 |
| 5 | swap | 0xc83c...9911 | (Uniswap v3) | 1,940,000 | USDT→ETH | 0.92 |
| 6 | direct | 0xa701...77b2 | 0xb1c0...e004 | 1,938,000 | cex_deposit | 0.88 |
| 6 | direct | 0xc83c...9911 | 0xa3f4...d011 | 1,938,000 | cex_deposit | 0.88 |

## Per-agent cost

| Agent | Calls | Tokens | Wall clock |
|---|---:|---:|---:|
| address_tagger | 1 | 3,200 | 1.6s |
| hop_walker | 38 | 118,400 | 14.0s |
| bridge_decoder | 11 | 91,300 | 12.4s |
| mixer_detector | 7 | 56,700 | 8.6s (zero hits, all branches kept walking) |
| swap_decoder | 24 | 142,800 | 18.3s |
| exchange_resolver | 12 | 67,200 | 8.0s |
| synthesis_reasoner | 1 | 22,400 | 5.1s |
| **Total** | **94** | **501,000** | **42s wall** |

## Synthesis output

```json
{
  "summary": "$4.18M drained from treasury 0x7ab2 split into two equal $1.94M branches after a Curve USDC->USDT swap and Stargate Ethereum->Arbitrum bridge. Both branches deposited to CEX (Bybit + OKX) within 2 hours of the bridge completion. High likelihood of partial recovery if reported to both exchanges within 24h.",
  "terminal_destinations": [
    {"exchange": "Bybit", "share_of_funds_pct": 46.4, "confidence": 0.88, "basis": "deposit address 0xb1c0...e004 funded only by known Bybit hot wallet 0x6e2c...c9b8"},
    {"exchange": "OKX", "share_of_funds_pct": 46.4, "confidence": 0.86, "basis": "deposit address 0xa3f4...d011 cluster matches OKX deposit pattern (single-source funder, daily sweep)"},
    {"exchange": "(unaccounted)", "share_of_funds_pct": 7.2, "basis": "gas + bridge fees + slippage"}
  ],
  "key_hops": [3, 4, 8, 9],
  "next_actions": [
    "File compliance request with Bybit referencing tx hash from depth 6, wallet 0xb1c0...e004",
    "File compliance request with OKX referencing tx hash from depth 6, wallet 0xa3f4...d011",
    "Monitor 0xfed1...321 on Arbitrum for any further outbound; appears now empty",
    "Cross-reference Stargate bridge nonces for additional same-attacker activity in the 48h window"
  ]
}
```

## reasoning_content snippet

```
Trace converges cleanly. The split at depth 4 (one bridge output → two
recipient addresses, exact 50/50 split) is consistent with known
attacker behavior to fragment a single seizure-action by an exchange.

Both branches reconverge on near-identical exit pattern:
  USDT → ETH (Uniswap v3) → CEX deposit

within 2 minutes of each other. This timing suggests automated
infrastructure, not manual.

CEX attribution confidence is 0.88 / 0.86 because the deposit addresses
have only ever been funded by a single hot wallet that matches known
Bybit and OKX patterns. Confidence lifts to 0.95+ if Bybit/OKX confirm
the address-cluster on KYC review.

Recommended primary action: file compliance reports with both exchanges
inside the 24h window. Recovery probability: 30-50% on the Bybit branch
(faster compliance team), 20-40% on OKX.
```

## Cost projection per workload

| Operator | Investigations / day | Daily tokens | Monthly |
|---|---:|---:|---:|
| Single analyst | 8 | 4M | 120M |
| Compliance firm (10 analysts) | 80 | 40M | 1.2B |
| Vendor (100 analysts) | 800 | 400M | 12B |

Plan Max (700M / month) lines up with **single-firm operating cadence**.
