"""
Metric Registry - Batch 3
Central registry for all panel metrics with contract-stable IDs

CRITICAL RULES:
- IDs are CONTRACT-STABLE: Never renumber or rename once defined
- New metrics are ALWAYS added to the END of their section (weekly/monthly)
- Metric order in this file determines display order in UI
- ALL params use STRING format: interval="1h", limit="30", symbol="BTC"

DAILY MINIMAL SPECIFICATION (DO NOT DRIFT):
The 10 daily metrics are CONTRACT-LOCKED based on Daily Minimal requirements:
1. OI snapshot (total)
2. OI change 1h
3. OI change 4h
4. Weighted funding 8h
5. Funding history 8h*30
6. L/S global
7. L/S Hyperliquid
8. Liquidations totals 24h (combined: long/short/total/percent)
9. Top liquidation events (top 10, 24h)
10. Coinbase premium index snapshot

IMPORT-TIME VALIDATION:
- validate_unique_ids() is called automatically when this module loads
- Duplicate IDs will cause immediate import failure (fail-fast)
- This ensures contract integrity before any code runs

METRIC COUNTS (CONTRACT):
- Daily: 10 metrics (daily_01 → daily_10) - IMPLEMENTED
- Weekly: 18 metrics (weekly_01 → weekly_18) - REGISTRY ONLY
- Monthly: 15 metrics (monthly_01 → monthly_15) - REGISTRY ONLY
- Total: 43 metrics
"""

from typing import Dict, List
from batch3_metrics_system.metric_definitions import (
    MetricDefinition,
    MetricStatus,
    create_daily_metric,
    create_registry_metric,
    APIConfidence,
    DataSource,
    PlanTier
)


# ============================================================================
# DAILY METRICS - BATCH 3 IMPLEMENTATION (10 metrics)
# ============================================================================
# These metrics are fully implemented with normalizers
# IDs: daily_01 → daily_10 (CONTRACT-LOCKED)
# Based on DAILY MINIMAL list - DO NOT DRIFT from this specification

DAILY_METRICS: List[MetricDefinition] = [
    # daily_01 - Total Open Interest (snapshot)
    create_daily_metric(
        daily_id="daily_01_total_open_interest",
        name="Total Open Interest",
        timeframe="snapshot",
        category="open_interest",
        endpoint="/api/futures/open-interest/aggregated-history",
        params={"interval": "8h", "limit": "1", "symbol": "BTC"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_total_oi",
        unit="billion_usd",
        description="Current total open interest across all exchanges",
        implementation_notes="Latest value from 8h candles; uses close field from v4 OHLC data"
    ),
    
    # daily_02 - OI Change (1h)
    create_daily_metric(
        daily_id="daily_02_oi_change_1h",
        name="OI Change (1h)",
        timeframe="1h",
        category="open_interest",
        endpoint="/api/futures/open-interest/aggregated-history",
        params={"interval": "1h", "limit": "5", "symbol": "BTC"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_oi_change_1h",
        unit="percent",
        description="1-hour percentage change in open interest",
        implementation_notes="Compare last 2 datapoints (1h interval); v4 uses close field"
    ),
    
    # daily_03 - OI Change (4h)
    create_daily_metric(
        daily_id="daily_03_oi_change_4h",
        name="OI Change (4h)",
        timeframe="4h",
        category="open_interest",
        endpoint="/api/futures/open-interest/aggregated-history",
        params={"interval": "4h", "limit": "2", "symbol": "BTC"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_oi_change_4h",
        unit="percent",
        description="4-hour percentage change in open interest",
        implementation_notes="Compare last 2 datapoints (4h interval); v4 uses close field"
    ),
    
    # daily_04 - Weighted Funding Rate (8h snapshot)
    create_daily_metric(
        daily_id="daily_04_weighted_funding_rate",
        name="Weighted Funding Rate",
        timeframe="snapshot",
        category="funding",
        endpoint="/api/futures/funding-rate/oi-weight-history",
        params={"interval": "8h", "limit": "1", "symbol": "BTC"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_weighted_funding",
        unit="percent",
        description="Current weighted average funding rate",
        implementation_notes="Latest 8h funding rate; v4 endpoint per docs"
    ),
    
    # daily_05 - Funding Rate History (8h * 30 candles)
    create_daily_metric(
        daily_id="daily_05_funding_rate_history",
        name="Funding Rate History",
        timeframe="8h",
        category="funding",
        endpoint="/api/futures/funding-rate/oi-weight-history",
        params={"interval": "8h", "limit": "30", "symbol": "BTC"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_funding_history",
        unit="time_series",
        description="30-period funding rate history (8h intervals)",
        implementation_notes="Returns list[dict] with timestamp (epoch seconds) and value; v4 endpoint per docs"
    ),
    
    # daily_06 - Long/Short Ratio (Global)
    create_daily_metric(
        daily_id="daily_06_long_short_global",
        name="Long/Short Ratio (Global)",
        timeframe="1h",
        category="long_short",
        endpoint="/api/futures/global-long-short-account-ratio/history",
        params={"interval": "1h", "limit": "1", "symbol": "BTCUSDT", "exchange": "Binance"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_long_short_global",
        unit="ratio",
        description="Global long/short account ratio",
        implementation_notes="Returns dict with long, short, ratio; v4 global endpoint"
    ),
    
    # daily_07 - Long/Short Ratio (Hyperliquid) - PLACEHOLDER (implemented=False)
    MetricDefinition(
        id="daily_07_long_short_hyperliquid",
        name="Long/Short Ratio (Hyperliquid)",
        timeframe="snapshot",
        category="long_short",
        endpoint="/api/futures/global-long-short-account-ratio/history",
        params={"interval": "1h", "limit": "1", "symbol": "BTC"},
        api_confidence=APIConfidence.UNVERIFIED,
        normalizer="normalize_long_short_hyperliquid",
        unit="ratio",
        description="Hyperliquid exchange long/short ratio (PLACEHOLDER - needs exchange-specific endpoint)",
        implementation_notes="PLACEHOLDER: No Hyperliquid-specific endpoint found. Returns EXTERNAL_REQUIRED status.",
        implemented=False,  # CRITICAL: Not implemented - prevents fetch attempts
        default_status=MetricStatus.EXTERNAL_REQUIRED,  # DETERMINISTIC: Shows as external requirement, not error
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP
    ),
    
    # daily_08 - 24h Liquidations Total (combined)
    create_daily_metric(
        daily_id="daily_08_liquidations_24h_total",
        name="24h Liquidations (Total)",
        timeframe="24h",
        category="liquidations",
        endpoint="/api/futures/liquidation/aggregated-history",
        params={"interval": "4h", "limit": "6", "symbol": "BTC", "exchange_list": "ApeX Omni,Aster,Binance,BingX,Bitfinex,Bitget,Bitmex,Bitunix,Bybit,CME,CoinEx,Coinbase,Crypto.com,Deribit,Drift,EdgeX,Extended,Gate,Gemini,HTX,Hyperliquid,Kraken,KuCoin,LBank,Lighter,MEXC,OKX,Paradex,WhiteBIT,dYdX"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_liquidations_total",
        unit="million_usd",
        description="24-hour liquidation summary (long/short/total)",
        implementation_notes="Returns dict: {long, short, total, long_percent, short_percent}; v4 aggregated endpoint"
    ),
    
    # daily_09 - Top Liquidation Events (24h, top 10) - LOCKED (requires plan upgrade)
    MetricDefinition(
        id="daily_09_top_liquidation_events",
        name="Top Liquidation Events",
        timeframe="24h",
        category="liquidations",
        endpoint="/api/futures/liquidation/order",
        params={"symbol": "BTC", "exchange_list": "Binance,OKX,Bybit", "limit": "10"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_liquidation_events",
        unit="events",
        description="Top 10 largest liquidation orders in last 24h (plan-locked on Startup)",
        implementation_notes="LOCKED: /api/futures/liquidation/order returns 'Upgrade plan' on Startup. Requires PlanTier.STANDARD (or above).",
        implemented=False,
        default_status=MetricStatus.LOCKED,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STANDARD
    ),

# daily_10 - Coinbase Premium Index (snapshot)
    create_daily_metric(
        daily_id="daily_10_coinbase_premium_index",
        name="Coinbase Premium Index",
        timeframe="snapshot",
        category="premium",
        endpoint="/api/coinbase-premium-index",
        params={"interval": "1h", "limit": "2", "symbol": "BTC"},
        api_confidence=APIConfidence.CONFIRMED,
        normalizer="normalize_coinbase_premium",
        unit="percent",
        description="Coinbase premium/discount vs global exchanges",
        implementation_notes="Returns dict: {premium, change_1h} - latest value + 1h change; v4 indicator endpoint"
    ),

    create_daily_metric(
        daily_id="daily_13_binance_funding_rate_last",
        name="Funding Rate (latest, Binance Futures)",
        timeframe="8h",
        category="funding",
        endpoint="/fapi/v1/fundingRate",
        params={"symbol": "BTCUSDT", "limit": "1"},
        api_confidence=APIConfidence.UNVERIFIED,
        normalizer="normalize_binance_funding_rate_last",
        unit="percent",
        description="Latest BTCUSDT funding rate from Binance Futures (most recent funding entry).",
        implementation_notes="Free-mode provider: Binance Futures public endpoint /fapi/v1/fundingRate; normalized to percent + fundingTime.",
    ),
    create_daily_metric(
        daily_id="daily_14_binance_open_interest",
        name="Open Interest (snapshot, Binance Futures)",
        timeframe="snapshot",
        category="open_interest",
        endpoint="/fapi/v1/openInterest",
        params={"symbol": "BTCUSDT"},
        api_confidence=APIConfidence.UNVERIFIED,
        normalizer="normalize_binance_open_interest",
        unit="BTC",
        description="Binance Futures BTCUSDT perpetual open interest (base asset units).",
        implementation_notes="Free-mode provider: Binance Futures public endpoint /fapi/v1/openInterest; normalized to float.",
    ),
    create_daily_metric(
        daily_id="daily_15_binance_oi_change_1h",
        name="OI Change (1h, Binance Futures)",
        timeframe="1h",
        category="open_interest",
        endpoint="/futures/data/openInterestHist",
        params={"symbol": "BTCUSDT", "period": "1h", "limit": "2"},
        api_confidence=APIConfidence.UNVERIFIED,
        normalizer="normalize_binance_oi_change_1h",
        unit="percent",
        description="1-hour percentage change in BTCUSDT open interest (Binance Futures).",
        implementation_notes="Binance endpoint /futures/data/openInterestHist; uses sumOpenInterestValue when available; compares last 2 points.",
    ),
    create_daily_metric(
        daily_id="daily_16_binance_oi_change_4h",
        name="OI Change (4h, Binance Futures)",
        timeframe="4h",
        category="open_interest",
        endpoint="/futures/data/openInterestHist",
        params={"symbol": "BTCUSDT", "period": "4h", "limit": "2"},
        api_confidence=APIConfidence.UNVERIFIED,
        normalizer="normalize_binance_oi_change_4h",
        unit="percent",
        description="4-hour percentage change in BTCUSDT open interest (Binance Futures).",
        implementation_notes="Binance endpoint /futures/data/openInterestHist; uses sumOpenInterestValue when available; compares last 2 points.",
    ),
]


# ============================================================================
# WEEKLY METRICS - REGISTRY ONLY (18 metrics)
# ============================================================================
# These metrics are NOT implemented in Batch 3 - display only
# IDs: weekly_01 → weekly_18 (CONTRACT-LOCKED, DO NOT RENUMBER)
# New weekly metrics must be added to the END with weekly_19, weekly_20, etc.

WEEKLY_METRICS: List[MetricDefinition] = [
    # weekly_01 - OI Trend (7d) (IMPLEMENTED)
    MetricDefinition(
        id="weekly_01_oi_trend",
        name="OI Trend (7d)",
        timeframe="7d",
        category="open_interest",
        endpoint="/api/futures/open-interest/aggregated-history",
        params={"symbol": "BTC", "interval": "1d", "limit": "14"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_oi_trend_7d",
        unit="billion_usd",
        description="7-day open interest trend (current OI + 7d delta)",
        implementation_notes="CoinGlass aggregated-history; returns {value, change_7d} in billions USD"
    ),    # weekly_02 - CME OI (7d) (IMPLEMENTED via CFTC COT)
    MetricDefinition(
        id="weekly_02_cme_oi",
        name="CME OI (7d)",
        timeframe="7d",
        category="open_interest",
        endpoint="cftc://legacy/futonly/6dca-aqww/cme-bitcoin",
        params={"limit": "1"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.CFTC,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_cme_cftc_open_interest",
        unit="contracts",
        description="CME Bitcoin futures open interest (CFTC COT legacy futures-only)",
        implementation_notes="Source: CFTC publicreporting (Socrata) dataset 6dca-aqww; market_and_exchange_names='BITCOIN - CHICAGO MERCANTILE EXCHANGE'"
    ),    # weekly_03 - CME Long/Short (IMPLEMENTED via CFTC COT)
    MetricDefinition(
        id="weekly_03_cme_long_short",
        name="CME Long/Short",
        timeframe="7d",
        category="long_short",
        endpoint="cftc://legacy/futonly/6dca-aqww/cme-bitcoin",
        params={"limit": "1"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.CFTC,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_cme_cftc_long_short",
        unit="ratio",
        description="CME positioning ratios derived from CFTC COT (Non-Commercial / Commercial / Non-Reportable)",
        implementation_notes="Computes L/S ratios from noncomm_positions_* , comm_positions_* , nonrept_positions_*"
    ),
    # weekly_04 - Basis Spread (7d) (IMPLEMENTED)
    MetricDefinition(
        id="weekly_04_basis_spread",
        name="Basis Spread (7d)",
        timeframe="7d",
        category="premium",
        endpoint="/api/futures/basis/history",
        params={"exchange": "Binance", "symbol": "BTCUSDT", "interval": "1d", "limit": "14"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_basis_spread",
        unit="percent",
        description="Average spot-futures gap over 7 days",
        implementation_notes="CoinGlass /api/futures/basis/history; Binance BTCUSDT; returns {value, change_7d}"
    ),
    
    # weekly_05 - Funding Rate Avg (7d) (IMPLEMENTED)
    MetricDefinition(
        id="weekly_05_funding_rate_avg",
        name="Funding Rate Avg (7d)",
        timeframe="7d",
        category="funding",
        endpoint="/api/futures/funding-rate/history",
        params={"exchange": "Binance", "symbol": "BTCUSDT", "interval": "1d", "limit": "14"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_funding_rate_avg_7d",
        unit="percent",
        description="7-day average funding rate",
        implementation_notes="CoinGlass /api/futures/funding-rate/history; 14 daily bars; returns {value, change_7d}"
    ),
    
    # weekly_06 - Long Liquidations (7d) (IMPLEMENTED)
    MetricDefinition(
        id="weekly_06_long_liquidations",
        name="Long Liquidations (7d)",
        timeframe="7d",
        category="liquidations",
        endpoint="/api/futures/liquidation/aggregated-history",
        params={"symbol": "BTC", "interval": "1d", "limit": "14", "exchange_list": "Binance,OKX,Bybit,Bitget,Gate"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_long_liquidations_7d",
        unit="million_usd",
        description="Total long liquidation volume over 7 days",
        implementation_notes="CoinGlass aggregated-history; returns {value, change_7d} in millions USD"
    ),

    # weekly_07 - Short Liquidations (7d) (IMPLEMENTED)
    MetricDefinition(
        id="weekly_07_short_liquidations",
        name="Short Liquidations (7d)",
        timeframe="7d",
        category="liquidations",
        endpoint="/api/futures/liquidation/aggregated-history",
        params={"symbol": "BTC", "interval": "1d", "limit": "14", "exchange_list": "Binance,OKX,Bybit,Bitget,Gate"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_short_liquidations_7d",
        unit="million_usd",
        description="Total short liquidation volume over 7 days",
        implementation_notes="CoinGlass aggregated-history; returns {value, change_7d} in millions USD"
    ),
    
    # weekly_08 - Net Flow (7d)
    create_registry_metric(
        registry_id="weekly_08_net_flow",
        name="Net Flow (7d)",
        timeframe="7d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STANDARD,
        unit="btc",
        description="Net exchange inflow/outflow over 7 days",
        implementation_notes="Requires on-chain data (Glassnode/CryptoQuant)"
    ),
    
    # weekly_09 - Large Holder Acc (7d)
    create_registry_metric(
        registry_id="weekly_09_large_holder_acc",
        name="Large Holder Acc (7d)",
        timeframe="7d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STANDARD,
        unit="percent",
        description="Whale accumulation trend over 7 days",
        implementation_notes="Requires on-chain data"
    ),
    
    # weekly_10 - Active Addresses (7d) (IMPLEMENTED)
    MetricDefinition(
        id="weekly_10_active_addresses",
        name="Active Addresses (7d)",
        timeframe="7d",
        category="open_interest",
        endpoint="/api/index/bitcoin-active-addresses",
        params={},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_active_addresses_7d",
        unit="thousand_addresses",
        description="7-day avg active addresses (k); change is absolute vs prior 7d (k)",
        implementation_notes="CoinGlass returns full history; API ignores limit param. Normalizer slices last14 and computes 7d/7d averages."
    ),
    
    # weekly_11 - BTC Dominance Change (IMPLEMENTED)
    MetricDefinition(
        id="weekly_11_btc_dominance_change",
        name="BTC Dominance Change",
        timeframe="7d",
        category="open_interest",
        endpoint="/api/index/bitcoin-dominance",
        params={},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_btc_dominance_change",
        unit="percent",
        description="Change in BTC market cap dominance",
        implementation_notes="CoinGlass /api/index/bitcoin-dominance; returns {value, change_7d}"
    ),
    
    # weekly_12 - ETH/BTC Ratio Change (IMPLEMENTED - multi-endpoint)
    MetricDefinition(
        id="weekly_12_eth_btc_ratio_change",
        name="ETH/BTC Ratio Change",
        timeframe="7d",
        category="open_interest",
        endpoint=None,  # Uses fetch_plan instead
        params=None,
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_eth_btc_ratio",
        fetch_plan=[
            {"name": "eth", "endpoint": "/api/spot/price/history", "params": {"exchange": "Binance", "symbol": "ETHUSDT", "interval": "1d", "limit": "8"}},
            {"name": "btc", "endpoint": "/api/spot/price/history", "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "1d", "limit": "8"}}
        ],
        unit="ratio",
        description="ETH relative strength vs BTC",
        implementation_notes="Multi-endpoint: spot/price/history for ETH + BTC; returns {value, change_7d}"
    ),
    
    # weekly_13 - Major Exchange Volume (IMPLEMENTED)
    MetricDefinition(
        id="weekly_13_major_exchange_volume",
        name="Major Exchange Volume (7d)",
        timeframe="7d",
        category="open_interest",
        endpoint="/api/futures/aggregated-taker-buy-sell-volume/history",
        params={"symbol": "BTC", "interval": "1d", "limit": "14", "exchange_list": "Binance,OKX,Bybit,Bitget,Gate"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_major_exchange_volume_7d",
        unit="billion_usd",
        description="7-day taker volume on major exchanges (proxy for perp volume)",
        implementation_notes="Startup plan limitation: uses aggregated taker buy/sell volume as proxy for exchange volume. Returns {value, change_7d} in billions USD."
    ),

    # weekly_14 - Perp Volume Change (IMPLEMENTED)
    MetricDefinition(
        id="weekly_14_perp_volume_change",
        name="Perp Volume Change (7d)",
        timeframe="7d",
        category="open_interest",
        endpoint="/api/futures/aggregated-taker-buy-sell-volume/history",
        params={"symbol": "BTC", "interval": "1d", "limit": "14", "exchange_list": "Binance,OKX,Bybit,Bitget,Gate"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_perp_volume_change_7d",
        unit="percent",
        description="7-day change in perpetual futures volume (percent)",
        implementation_notes="Startup plan limitation: uses aggregated taker buy/sell volume as proxy for perp volume. Returns {value, change_7d} where change_7d is PERCENT."
    ),
    
    # weekly_15 - USDT Premium (7d) (IMPLEMENTED)
    MetricDefinition(
        id="weekly_15_usdt_premium",
        name="USDT Premium (7d)",
        timeframe="7d",
        category="premium",
        endpoint="/api/spot/price/history",
        params={"exchange": "Binance", "symbol": "USDCUSDT", "interval": "1d", "limit": "14"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_usdt_premium_7d",
        unit="percent",
        description="USDT Premium (7d) via USDCUSDT peg proxy",
        implementation_notes="Startup plan limitation: spot USDCUSDT on Binance used as proxy for USDT premium/discount. premium_pct=(close-1)*100"
    ),
    
    # weekly_16 - Fear & Greed Index (IMPLEMENTED)
    MetricDefinition(
        id="weekly_16_fear_greed_index",
        name="Fear & Greed Index",
        timeframe="7d",
        category="open_interest",
        endpoint="/api/index/fear-greed-history",
        params={},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_fear_greed_index",
        unit="index",
        description="Market sentiment indicator (0-100)",
        implementation_notes="CoinGlass /api/index/fear-greed-history; returns {value, label, change_7d}"
    ),
    
    # weekly_17 - Options Put/Call Ratio (EXTERNAL_REQUIRED)
    create_registry_metric(
        registry_id="weekly_17_options_put_call_ratio",
        name="Options Put/Call Ratio",
        timeframe="7d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STARTUP,
        unit="ratio",
        description="Options positioning indicator",
        implementation_notes="EXTERNAL_REQUIRED: CoinGlass options endpoints (/api/option/info, /api/option/exchange-oi-history, /api/option/exchange-vol-history) do not expose put/call split under Startup plan. Requires external source: Deribit API, Laevitas, Amberdata, or similar options data provider."
    ),
    
    # weekly_18 - Market Cap Rank Changes
    create_registry_metric(
        registry_id="weekly_18_market_cap_rank_changes",
        name="Market Cap Rank Changes",
        timeframe="7d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STARTUP,
        unit="count",
        description="Top 100 ranking movements",
        implementation_notes="CMC/CoinGecko rankings"
    )
]


# ============================================================================
# MONTHLY METRICS - REGISTRY ONLY (15 metrics)
# ============================================================================
# These metrics are NOT implemented in Batch 3 - display only
# IDs: monthly_01 → monthly_15 (CONTRACT-LOCKED, DO NOT RENUMBER)
# New monthly metrics must be added to the END with monthly_16, monthly_17, etc.

MONTHLY_METRICS: List[MetricDefinition] = [
    
    # monthly_01 - Volatility (30d) (IMPLEMENTED)
    MetricDefinition(
        id="monthly_01_volatility",
        name="Volatility (30d)",
        timeframe="30d",
        category="open_interest",
        endpoint="/api/spot/price/history",
        params={"exchange": "Binance", "symbol": "BTCUSDT", "interval": "1d", "limit": "35"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_volatility_30d",
        unit="percent",
        description="30-day realized volatility from BTC spot daily closes",
        implementation_notes="Uses /api/spot/price/history (Binance BTCUSDT 1d). Vol=stdev(log returns) annualized with sqrt(365)."
    ),
    # monthly_02 - MVRV Ratio
    create_registry_metric(
        registry_id="monthly_02_mvrv_ratio",
        name="MVRV Ratio",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STANDARD,
        unit="ratio",
        description="Market value to realized value ratio",
        implementation_notes="Requires on-chain data"
    ),
    
    # monthly_03 - NVT Ratio
    create_registry_metric(
        registry_id="monthly_03_nvt_ratio",
        name="NVT Ratio",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STANDARD,
        unit="ratio",
        description="Network value to transactions ratio",
        implementation_notes="Requires on-chain data"
    ),
    
    # monthly_04 - Supply on Exchanges
    create_registry_metric(
        registry_id="monthly_04_supply_on_exchanges",
        name="Supply on Exchanges",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STANDARD,
        unit="percent",
        description="Percentage of supply on exchanges",
        implementation_notes="Requires on-chain data"
    ),
    
    # monthly_05 - Miner Reserve
    create_registry_metric(
        registry_id="monthly_05_miner_reserve",
        name="Miner Reserve",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STANDARD,
        unit="btc",
        description="Bitcoin held by miners",
        implementation_notes="Requires on-chain data"
    ),
    
    # monthly_06 - Long-Term Holder Supply
    create_registry_metric(
        registry_id="monthly_06_long_term_holder_supply",
        name="Long-Term Holder Supply",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STANDARD,
        unit="percent",
        description="Supply held by HODLers (>155 days)",
        implementation_notes="Requires on-chain data"
    ),
    
    # monthly_07 - Hash Rate Growth
    create_registry_metric(
        registry_id="monthly_07_hash_rate_growth",
        name="Hash Rate Growth",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STARTUP,
        unit="percent",
        description="30-day mining power change",
        implementation_notes="Blockchain.com or similar"
    ),
    
    # monthly_08 - Realized Cap Change
    create_registry_metric(
        registry_id="monthly_08_realized_cap_change",
        name="Realized Cap Change",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.STANDARD,
        unit="percent",
        description="30-day capital inflow indicator",
        implementation_notes="Requires on-chain data"
    ),
    
    # monthly_09 - Stablecoin Market Cap (IMPLEMENTED)
    MetricDefinition(
        id="monthly_09_stablecoin_market_cap",
        name="Stablecoin Market Cap",
        timeframe="30d",
        category="open_interest",
        endpoint="/api/index/stableCoin-marketCap-history",
        params={},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_stablecoin_market_cap",
        unit="billion_usd",
        description="Total stablecoin supply (sideline capital)",
        implementation_notes="CoinGlass /api/index/stableCoin-marketCap-history; sum USDT+USDC+DAI+BUSD+TUSD+FDUSD+USDE"
    ),
    
    
    # monthly_10 - Futures OI Growth (IMPLEMENTED)
    MetricDefinition(
        id="monthly_10_futures_oi_growth",
        name="Futures OI Growth",
        timeframe="30d",
        category="open_interest",
        endpoint="/api/futures/open-interest/aggregated-history",
        params={"interval": "1d", "limit": "35", "symbol": "BTC"},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_futures_oi_growth_30d",
        unit="percent",
        description="30-day derivatives market growth (BTC aggregated OI)",
        implementation_notes="Compute % change: last_close vs close_30d_ago from /api/futures/open-interest/aggregated-history interval=1d"
    ),
    # monthly_11 - Options Volume Growth (IMPLEMENTED)
    MetricDefinition(
        id="monthly_11_options_vol_growth",
        name="Options Volume Growth",
        timeframe="30d",
        category="open_interest",
        endpoint="/api/option/exchange-vol-history",
        params={"symbol": "BTC", "exchange": "All", "range": "60d", "interval": "1d", "limit": "60", "unit": "usd"},
        api_confidence=APIConfidence.UNVERIFIED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_options_volume_growth_30d",
        unit="percent",
        description="30-day options volume growth (total vs prior 30d, USD)",
        implementation_notes="CoinGlass /api/option/exchange-vol-history; sum last 30 points across exchanges and compare to prior 30 points"
    ),
    
    # monthly_12 - ETF Holdings (IMPLEMENTED)
    MetricDefinition(
        id="monthly_12_etf_holdings",
        name="ETF Holdings",
        timeframe="30d",
        category="open_interest",
        endpoint="/api/etf/bitcoin/list",
        params={},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_etf_bitcoin_holdings_total",
        unit="btc",
        description="Total BTC held by spot Bitcoin ETFs (sum of holding_quantity)",
        implementation_notes="CoinGlass /api/etf/bitcoin/list; sum asset_details.holding_quantity; filter fund_type=Spot region=us"
    ),
    
    # monthly_13 - Grayscale/Institutional (IMPLEMENTED)
    MetricDefinition(
        id="monthly_13_grayscale_institutional",
        name="Grayscale/Institutional",
        timeframe="30d",
        category="open_interest",
        endpoint="/api/etf/bitcoin/list",
        params={},
        api_confidence=APIConfidence.CONFIRMED,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer="normalize_grayscale_us_holdings_total",
        unit="btc",
        description="Grayscale US products (name contains Grayscale) total BTC holdings",
        implementation_notes="CoinGlass /api/etf/bitcoin/list; filter region=us AND name contains grayscale"
    ),
    
    # monthly_14 - Social Volume
    create_registry_metric(
        registry_id="monthly_14_social_volume",
        name="Social Volume",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.PREMIUM,
        unit="index",
        description="Social media activity indicator",
        implementation_notes="Twitter/Reddit mentions (LunarCrush etc)"
    ),
    
    # monthly_15 - Developer Activity
    create_registry_metric(
        registry_id="monthly_15_developer_activity",
        name="Developer Activity",
        timeframe="30d",
        category="open_interest",
        data_source=DataSource.EXTERNAL,
        min_plan=PlanTier.PREMIUM,
        unit="commits",
        description="30-day GitHub commit count",
        implementation_notes="Bitcoin Core + Lightning repos"
    )
]


# ============================================================================
# PANEL REGISTRY - COMPLETE METRIC COLLECTION
# ============================================================================

# daily_11 - Funding Regime (8h, derived) - uses funding history series to produce decision-grade summary
DAILY_METRICS.append(
    create_daily_metric(
        "daily_11_funding_regime_8h",
        "Funding Regime (8h, derived)",
        "8h",
        "funding",
        "/api/futures/funding-rate/oi-weight-history",
        {"interval": "8h", "limit": "30", "symbol": "BTC"},
        APIConfidence.CONFIRMED,
        "normalize_funding_regime",
        "funding_regime",
        "Derived regime summary from last 30 funding points (8h) to make series decision-grade.",
        "Derived metric: uses funding history series and summarizes mean/vol/z/flip/slope/carry style features."
    )
)

# daily_p01 - Price (BTCUSDT) Last Close (1h) - public Binance
DAILY_METRICS.append(
    create_daily_metric(
        "daily_12_price_last_close",
        "BTCUSDT Last Close (1h)",
        "1h",
        "price",
        "/api/v3/klines",
        {"symbol": "BTCUSDT", "interval": "1h", "limit": "2"},
        APIConfidence.CONFIRMED,
        "normalize_price_last_close",
        "usd",
        "Last close price from Binance 1h klines (public, no key).",
        "Provider: BinancePublicAPI. Uses last kline close."
    )
)

PANEL_REGISTRY: Dict[str, List[MetricDefinition]] = {
    'daily': DAILY_METRICS,
    'weekly': WEEKLY_METRICS,
    'monthly': MONTHLY_METRICS
}


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_unique_ids() -> None:
    """
    Validate that all metric IDs are unique across the entire registry
    
    This function is called at import time to ensure contract integrity.
    If duplicate IDs are found, the import will fail immediately.
    
    Raises:
        ValueError: If duplicate IDs are found
    """
    all_ids = []
    
    # Collect all IDs
    for timeframe, metrics in PANEL_REGISTRY.items():
        for metric in metrics:
            all_ids.append((timeframe, metric.id))
    
    # Check for duplicates
    seen = set()
    duplicates = []
    
    for timeframe, metric_id in all_ids:
        if metric_id in seen:
            duplicates.append(metric_id)
        seen.add(metric_id)
    
    # Fail immediately if duplicates found
    if duplicates:
        # Sort duplicates for deterministic error messages (aids debugging)
        duplicates_sorted = sorted(set(duplicates))
        raise ValueError(
            f"CRITICAL: Duplicate metric IDs found in registry: {duplicates_sorted}. "
            f"All metric IDs must be unique across daily/weekly/monthly. "
            f"This is a CONTRACT VIOLATION - fix immediately before proceeding."
        )


def validate_numbering_sequence() -> None:
    """
    Validate that metric numbering is sequential and contiguous
    
    Weekly: weekly_01 → weekly_18 (no gaps)
    Monthly: monthly_01 → monthly_15 (no gaps)
    
    This is a soft validation - emits warnings but does not fail import.
    Future enhancement: Could be controlled by environment flag.
    
    Raises:
        UserWarning: If numbering gaps or misordering is detected
    """
    import warnings
    import re
    
    # Extract number from ID (e.g., "weekly_05_..." → 5)
    def extract_number(metric_id: str) -> int:
        match = re.search(r'_(\d{2})_', metric_id)
        return int(match.group(1)) if match else -1
    
    # Check weekly numbering
    weekly_numbers = [extract_number(m.id) for m in WEEKLY_METRICS]
    expected_weekly = list(range(1, len(WEEKLY_METRICS) + 1))
    if weekly_numbers != expected_weekly:
        warnings.warn(
            f"Weekly metric numbering is not sequential: {weekly_numbers}. "
            f"Expected: {expected_weekly}. Check for gaps or misordering.",
            category=UserWarning,
            stacklevel=2
        )
    
    # Check monthly numbering
    monthly_numbers = [extract_number(m.id) for m in MONTHLY_METRICS]
    expected_monthly = list(range(1, len(MONTHLY_METRICS) + 1))
    if monthly_numbers != expected_monthly:
        warnings.warn(
            f"Monthly metric numbering is not sequential: {monthly_numbers}. "
            f"Expected: {expected_monthly}. Check for gaps or misordering.",
            category=UserWarning,
            stacklevel=2
        )


# ============================================================================
# IMPORT-TIME VALIDATION (CRITICAL)
# ============================================================================
# These validations run automatically when this module is imported.
# Duplicate IDs will cause immediate failure (fail-fast for contract safety).
# Numbering validation emits warnings but does not block import.

validate_unique_ids()        # CRITICAL: Fails on duplicate IDs
validate_numbering_sequence()  # Soft: Warns on numbering issues


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_metric_by_id(metric_id: str) -> MetricDefinition:
    """
    Retrieve a metric definition by its ID
    
    Args:
        metric_id: Metric ID (e.g., "daily_01_total_open_interest")
    
    Returns:
        MetricDefinition if found
    
    Raises:
        KeyError: If metric ID not found in registry
    """
    for metrics in PANEL_REGISTRY.values():
        for metric in metrics:
            if metric.id == metric_id:
                return metric
    
    raise KeyError(f"Metric ID '{metric_id}' not found in registry")


def get_metrics_by_timeframe(timeframe: str) -> List[MetricDefinition]:
    """
    Get all metrics for a specific timeframe
    
    Args:
        timeframe: 'daily', 'weekly', or 'monthly'
    
    Returns:
        List of MetricDefinition objects
    
    Raises:
        KeyError: If timeframe not recognized
    """
    if timeframe not in PANEL_REGISTRY:
        raise KeyError(
            f"Invalid timeframe '{timeframe}'. "
            f"Must be one of: {list(PANEL_REGISTRY.keys())}"
        )
    
    return PANEL_REGISTRY[timeframe]


def get_all_implemented_metrics() -> List[MetricDefinition]:
    """
    Get all implemented metrics (implemented=True)
    
    Returns:
        List of implemented metrics (currently only daily metrics in Batch 3)
    """
    implemented = []
    for metrics in PANEL_REGISTRY.values():
        implemented.extend([m for m in metrics if m.implemented])
    return implemented


def get_registry_stats() -> Dict[str, int]:
    """
    Get registry statistics
    
    Returns:
        Dict with counts: total, daily, weekly, monthly, implemented
    """
    total = sum(len(metrics) for metrics in PANEL_REGISTRY.values())
    implemented = len(get_all_implemented_metrics())
    
    return {
        'total': total,
        'daily': len(DAILY_METRICS),
        'weekly': len(WEEKLY_METRICS),
        'monthly': len(MONTHLY_METRICS),
        'implemented': implemented,
        'registry_only': total - implemented
    }
