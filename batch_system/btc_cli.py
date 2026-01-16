import os
import sys
from datetime import datetime

from batch2_engine.coinglass import CoinGlassAPI
from batch3_metrics_system.orchestrator import MetricOrchestrator
from batch3_metrics_system.metric_registry import PANEL_REGISTRY
from batch3_metrics_system.output import TextFormatter
from batch3_metrics_system.metric_definitions import MetricStatus

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

def pick_daily_minimal_metrics():
    metrics = PANEL_REGISTRY.get("daily", [])
    metric_map = {m.id: m for m in metrics}
    picked = []
    for mid in DAILY_MINIMAL_IDS:
        m = metric_map.get(mid)
        if m is not None:
            picked.append(m)
    return picked

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
    print(f"SUMMARY: {ok_count}/{len(results)} metrics OK")
    print("=" * 70)

if __name__ == "__main__":
    main()
