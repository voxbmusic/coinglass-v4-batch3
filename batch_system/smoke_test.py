#!/usr/bin/env python3
"""
Smoke Test - Batch 3
Quick validation of 3 key metrics to catch schema/scale errors

Tests:
1. daily_01 - Total OI (billions)
2. daily_04 - Weighted Funding (percent) - CRITICAL FOR SCALE VALIDATION
3. daily_10 - Coinbase Premium (percent)

Usage:
    python3 smoke_test.py YOUR_API_KEY
    or
    export COINGLASS_API_KEY=your_key && python3 smoke_test.py
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import from batch2_engine
from batch2_engine.coinglass import CoinGlassAPI
from batch3_metrics_system.orchestrator import MetricOrchestrator
from batch3_metrics_system.metric_registry import PANEL_REGISTRY

def get_metric_by_id(metric_id):
    """Helper to find metric by ID"""
    for timeframe, metrics in PANEL_REGISTRY.items():
        for metric in metrics:
            if metric.id == metric_id:
                return metric
    return None

def smoke_test(api_key: str):
    """Run smoke test on 3 critical metrics"""
    
    print("=" * 70)
    print("SMOKE TEST - 3 Critical Metrics")
    print("=" * 70)
    
    # Initialize
    api = CoinGlassAPI(api_key=api_key)
    orchestrator = MetricOrchestrator(api)
    
    # Test metrics
    test_metrics = [
        "daily_01_total_open_interest",
        "daily_04_weighted_funding_rate",
        "daily_10_coinbase_premium_index"
    ]
    
    results = []
    
    for metric_id in test_metrics:
        print(f"\n{'='*70}")
        print(f"Testing: {metric_id}")
        print(f"{'='*70}")
        
        try:
            metric = get_metric_by_id(metric_id)
            if metric is None:
                print(f"❌ FAIL - Metric not found in registry")
                results.append(("FAIL", metric_id, None))
                continue
                
            result = orchestrator.fetch_and_normalize(metric)
            
            print(f"Status: {result.status.value}")
            print(f"Value: {result.value}")
            if result.error:
                print(f"Error: {result.error}")
            
            # Validation
            if result.status.value == "ok":
                if result.value is not None:
                    print("✅ PASS")
                    results.append(("PASS", metric_id, result.value))
                else:
                    print("❌ FAIL - Value is None but status is OK")
                    results.append(("FAIL", metric_id, None))
            else:
                print(f"⚠️ NOT OK - Status: {result.status.value}")
                results.append(("NOT_OK", metric_id, None))
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(("EXCEPTION", metric_id, None))
    
    # Summary
    print(f"\n{'='*70}")
    print("SMOKE TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for r in results if r[0] == "PASS")
    print(f"\nRESULT: {passed}/{len(results)} PASSED")
    
    for status, metric_id, value in results:
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        value_str = f" → {value}" if value is not None else ""
        print(f"{emoji} {metric_id}: {status}{value_str}")
    
    print("\n" + "="*70)
    
    # CRITICAL WARNING for funding rate
    if any(r[1] == "daily_04_weighted_funding_rate" and r[0] == "PASS" for r in results):
        funding_value = next(r[2] for r in results if r[1] == "daily_04_weighted_funding_rate" and r[0] == "PASS")
        print("\n⚠️ FUNDING RATE SCALE CHECK:")
        if isinstance(funding_value, (int, float)):
            if abs(funding_value) > 0.5:
                print(f"❌ SUSPICIOUS: {funding_value}% is TOO HIGH (expected <0.2%)")
                print("   → Likely scale issue. Send output to Helm immediately.")
            elif abs(funding_value) < 0.0001:
                print(f"❌ SUSPICIOUS: {funding_value}% is TOO LOW (expected >0.001%)")
                print("   → Likely scale issue. Send output to Helm immediately.")
            else:
                print(f"✅ OK: {funding_value}% is in expected range (0.001-0.2%)")
        print("="*70)
    
    return passed == len(results)

if __name__ == "__main__":
    # Get API key from environment or argument
    api_key = os.environ.get("COINGLASS_API_KEY")
    
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("❌ Error: API key required")
        print("\nUsage:")
        print("  python3 smoke_test.py YOUR_API_KEY")
        print("  or")
        print("  export COINGLASS_API_KEY=your_key && python3 smoke_test.py")
        sys.exit(1)
    
    success = smoke_test(api_key)
    sys.exit(0 if success else 1)
