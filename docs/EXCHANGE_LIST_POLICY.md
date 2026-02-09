# Exchange List Policy (CoinGlass v4)

## Why this exists
Some CoinGlass v4 endpoints **require** the `exchange_list` query parameter. If it is missing, the API can return an error like:
- `Required String parameter 'exchange_list' is not present`

This repo uses a deterministic, documented policy so the CLI outputs remain stable and reproducible.

---

## Current usage in this repo (as of 2026-02-09)

### Daily
- `daily_08_liquidations_24h_total`
  - endpoint: `/api/futures/liquidation/aggregated-history`
  - exchange_list: `Binance,OKX,Bybit`

- `daily_09_top_liquidation_events`
  - endpoint: `/api/futures/liquidation/aggregated-history`
  - exchange_list: `Binance,OKX,Bybit`

### Weekly
- `weekly_06_long_liquidations`
  - endpoint: `/api/futures/liquidation/aggregated-history`
  - exchange_list: `Binance,OKX,Bybit,Bitget,Gate`

- `weekly_07_short_liquidations`
  - endpoint: `/api/futures/liquidation/aggregated-history`
  - exchange_list: `Binance,OKX,Bybit,Bitget,Gate`

- `weekly_13_major_exchange_volume`
  - endpoint: `/api/futures/aggregated-taker-buy-sell-volume/history`
  - exchange_list: `Binance,OKX,Bybit,Bitget,Gate`

- `weekly_14_perp_volume_change`
  - endpoint: `/api/futures/aggregated-taker-buy-sell-volume/history`
  - exchange_list: `Binance,OKX,Bybit,Bitget,Gate`

---

## Policy rules

### Rule 1 — Prefer “Major venues” sets
We maintain two canonical sets:

**MAJOR_3 (daily-critical, low-noise)**
- `Binance,OKX,Bybit`

**MAJOR_5 (weekly aggregate, broader coverage)**
- `Binance,OKX,Bybit,Bitget,Gate`

Rationale:
- Daily is optimized for speed/stability and lower variance.
- Weekly aggregates benefit from broader market coverage.

### Rule 2 — Do not auto-expand silently
Do not change `exchange_list` values “just to try” without:
- documenting the change in this file, and
- updating the relevant metric definition(s) in `batch3_metrics_system/metric_registry.py`

### Rule 3 — Parameter normalization
`exchange_list` is passed as a **comma-separated string** (no spaces) exactly as in the metric registry:
- ✅ `Binance,OKX,Bybit`
- ❌ `Binance, OKX, Bybit`

### Rule 4 — When to introduce a new exchange
Only add an exchange if:
1) It is supported by CoinGlass for that endpoint/asset, and
2) It materially improves coverage, and
3) It does not degrade reliability (timeouts / frequent missing data)

When adding:
- update this doc
- update `metric_registry.py`
- run `btc` and verify no regressions in Daily Minimal

---

## Future improvement (optional)
A next step could be adding a small helper/constant registry (e.g., `EXCHANGE_LISTS = {...}`) so `metric_registry.py` references a single source of truth.
Not required right now—current approach is “explicit in registry” for clarity.
