import os
import sys
from datetime import datetime

from batch2_engine.coinglass import CoinGlassAPI
from batch3_metrics_system.orchestrator import MetricOrchestrator
from batch3_metrics_system.metric_registry import PANEL_REGISTRY
from batch3_metrics_system.output import TextFormatter
from batch3_metrics_system.metric_definitions import MetricStatus, DataSource, PlanTier

DAILY_MINIMAL_IDS = [
    "daily_01_total_open_interest",
    "daily_02_oi_change_1h",
    "daily_03_oi_change_4h",
    "daily_04_weighted_funding_rate",
    "daily_05_funding_rate_history",
    "daily_06_long_short_global",
    "daily_07_long_short_hyperliquid",
    "daily_08_liquidations_24h_total",
    "daily_09_top_liquidation_events",
    "daily_10_coinbase_premium_index",
]

WEEKLY_SKELETON_IDS = [
    "weekly_01_oi_trend",
    "weekly_02_cme_oi",
    "weekly_03_cme_long_short",
    "weekly_04_basis_spread",
    "weekly_05_funding_rate_avg",
    "weekly_06_long_liquidations",
    "weekly_07_short_liquidations",
    "weekly_08_net_flow",
    "weekly_09_large_holder_acc",
    "weekly_10_active_addresses",
    "weekly_11_btc_dominance_change",
    "weekly_12_eth_btc_ratio_change",
    "weekly_13_major_exchange_volume",
    "weekly_14_perp_volume_change",
    "weekly_15_usdt_premium",
    "weekly_16_fear_greed_index",
    "weekly_17_options_put_call_ratio",
    "weekly_18_market_cap_rank_changes",
]

def pick_daily_minimal_metrics():
    metrics = PANEL_REGISTRY.get("daily", [])
    metric_map = {m.id: m for m in metrics}
    picked = []
    for mid in DAILY_MINIMAL_IDS:
        m = metric_map.get(mid)
        if m is not None:
            picked.append(m)
    return picked

def pick_weekly_skeleton_metrics():
    metrics = PANEL_REGISTRY.get("weekly", [])
    metric_map = {m.id: m for m in metrics}
    picked = []
    for mid in WEEKLY_SKELETON_IDS:
        m = metric_map.get(mid)
        if m is not None:
            picked.append(m)
    return picked

def get_skeleton_status(metric):
    """
    Determine status for skeleton display (no API call).
    Rules:
    - EXTERNAL source -> EXTERNAL_REQUIRED
    - COINGLASS + plan > STARTUP -> LOCKED
    - COINGLASS + STARTUP + not implemented -> MISSING
    - implemented + data OK -> OK (not applicable for skeleton)
    """
    if metric.data_source == DataSource.EXTERNAL:
        return "🔗", "EXTERNAL_REQUIRED"

    if metric.min_plan != PlanTier.STARTUP:
        return "🔒", "LOCKED"

    if not metric.implemented:
        return "❌", "MISSING"

    return "✅", "OK"

def main():
    api_key = os.getenv("COINGLASS_API_KEY", "").strip()
    if not api_key:
        print("ERROR: COINGLASS_API_KEY is not set.")
        print("Usage:")
        print("  export COINGLASS_API_KEY=your_key")
        print("  python3 -m batch_system.btc_cli")
        print("  or")
        print("  python3 batch_system/btc_cli.py")
        sys.exit(1)

    api = CoinGlassAPI(api_key)
    orchestrator = MetricOrchestrator(api)
    metrics = pick_daily_minimal_metrics()
    
    if not metrics:
        print("ERROR: Could not find Daily Minimal metric IDs in PANEL_REGISTRY['daily'].")
        print("Next step: verify IDs in batch_system/batch3_metrics_system/metric_registry.py")
        sys.exit(2)
    
    results = []
    for metric in metrics:
        results.append(orchestrator.fetch_and_normalize(metric))
    
    print("=" * 70)
    print("  BTC - GUNLUK SAVAS PANELI (DAILY MINIMAL)")
    print("=" * 70)
    print("Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    panel_text = TextFormatter.format_timeframe("daily", results, verbose=False)
    print(panel_text)
    
    ok_count = sum(1 for r in results if r.status == MetricStatus.OK)
    print("\n" + "=" * 70)
    print(f"DAILY SUMMARY: {ok_count}/{len(results)} metrics OK")
    print("=" * 70)

    # ========================================================================
    # WEEKLY PANEL (HYBRID: IMPLEMENTED METRICS FETCH, OTHERS SKELETON)
    # ========================================================================
    print("\n" + "=" * 70)
    print("  BTC - HAFTALIK SAVAS PANELI (WEEKLY)")
    print("=" * 70)

    weekly_metrics = pick_weekly_skeleton_metrics()
    weekly_ok = 0
    weekly_missing = 0
    weekly_external = 0
    weekly_locked = 0

    if not weekly_metrics:
        print("  [No weekly metrics found in registry]")
    else:
        for metric in weekly_metrics:
            if metric.implemented:
                # Fetch real data for implemented metrics
                result = orchestrator.fetch_and_normalize(metric)
                if result.status == MetricStatus.OK:
                    weekly_ok += 1
                    print(f"  ✅ {metric.name}: {result.value}")
                else:
                    weekly_missing += 1
                    print(f"  ❌ {metric.name}: N/A [MISSING]")
            else:
                # Skeleton display for non-implemented metrics
                symbol, status_text = get_skeleton_status(metric)
                if status_text == "EXTERNAL_REQUIRED":
                    weekly_external += 1
                elif status_text == "LOCKED":
                    weekly_locked += 1
                else:
                    weekly_missing += 1
                print(f"  {symbol} {metric.name}: N/A [{status_text}]")

    print("\n" + "-" * 70)
    print(f"  WEEKLY SUMMARY: {weekly_ok}/{len(weekly_metrics)} metrics OK")
    print(f"  ✅ OK: {weekly_ok} | ❌ MISSING: {weekly_missing} | 🔗 EXTERNAL: {weekly_external} | 🔒 LOCKED: {weekly_locked}")
    print("=" * 70)

    # ========================================================================
    # MONTHLY PANEL (HYBRID: IMPLEMENTED METRICS FETCH, OTHERS SKELETON)
    # ========================================================================
    print("\n" + "=" * 70)
    print("  BTC - AYLIK SAVAS PANELI (MONTHLY)")
    print("=" * 70)
    print("MONTHLY METRICS")

    monthly_metrics = PANEL_REGISTRY.get("monthly", [])
    monthly_ok = 0
    monthly_missing = 0
    monthly_external = 0
    monthly_locked = 0

    if not monthly_metrics:
        print("  [No monthly metrics found in registry]")
    else:
        for metric in monthly_metrics:
            if metric.implemented:
                # Fetch real data for implemented metrics
                result = orchestrator.fetch_and_normalize(metric)
                if result.status == MetricStatus.OK:
                    monthly_ok += 1
                    print(f"  ✅ {metric.name}: {result.value}")
                else:
                    monthly_missing += 1
                    print(f"  ❌ {metric.name}: N/A [MISSING]")
            else:
                # Skeleton display for non-implemented metrics
                symbol, status_text = get_skeleton_status(metric)
                if status_text == "EXTERNAL_REQUIRED":
                    monthly_external += 1
                elif status_text == "LOCKED":
                    monthly_locked += 1
                else:
                    monthly_missing += 1
                print(f"  {symbol} {metric.name}: N/A [{status_text}]")

    print("\n" + "-" * 70)
    print(f"  MONTHLY SUMMARY: {monthly_ok}/{len(monthly_metrics)} metrics OK")
    print(f"  ✅ OK: {monthly_ok} | ❌ MISSING: {monthly_missing} | 🔗 EXTERNAL: {monthly_external} | 🔒 LOCKED: {monthly_locked}")
    print("=" * 70)


if __name__ == "__main__":
    main()
