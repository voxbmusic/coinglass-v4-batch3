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

# Environment check (optional - helps debug dependency issues)
try:
    import requests
    print(f"Python: {sys.version.split()[0]} | Requests: {requests.__version__}")
except ImportError:
    print("⚠️ Warning: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

# Add batch_system root directory to sys.path for absolute imports
# This is the directory where smoke_test.py lives
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from batch2_engine.coinglass import CoinGlassAPI
from batch3_metrics_system.orchestrator import MetricOrchestrator
from batch3_metrics_system.metric_registry import PANEL_REGISTRY

def get_metric_by_id(metric_id: str):
    """Helper to find metric by ID in registry"""
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
            result = orchestrator.fetch_and_normalize(metric)
            
            # DEBUG: For funding rate metrics only, print raw response if missing
            if metric_id in ["daily_04_weighted_funding_rate", "daily_05_funding_rate_history"] and result.status.value.lower() == "missing":
                print(f"🔍 DEBUG - Fetching raw response for {metric_id}...")
                debug_api = None
                try:
                    from batch2_engine.coinglass import CoinGlassAPI
                    debug_api = CoinGlassAPI(api_key=api_key)
                    
                    # Show endpoint and params being called
                    print(f"   Endpoint: {metric.endpoint}")
                    print(f"   Params: {metric.params}")
                    
                    # CoinGlassAPI.fetch already calls normalize_params internally
                    debug_response = debug_api.fetch(metric.endpoint, metric.params)
                    
                    if debug_response and debug_response.success:
                        response_data = debug_response.data
                        
                        # Type guard: ensure response_data is dict (v4 format)
                        if not isinstance(response_data, dict):
                            print(f"   ⚠️ Unexpected response shape: {type(response_data)}")
                            print(f"   Raw data: {response_data}")
                        else:
                            # Print compact summary: code + first data item (if exists)
                            code = response_data.get("code", "unknown")
                            data_list = response_data.get("data", [])
                            first_item = data_list[0] if data_list else None
                            
                            print(f"   Response code: {code}")
                            print(f"   Data length: {len(data_list)}")
                            if first_item:
                                print(f"   First item: {first_item}")
                            else:
                                print(f"   Data is empty")
                    else:
                        print(f"   Fetch failed: success={debug_response.success if debug_response else 'None'}")
                except Exception as debug_error:
                    print(f"   Debug fetch error: {debug_error}")
                finally:
                    # Cleanup: CoinGlassAPI.close() is recommended for proper resource management
                    if debug_api is not None:
                        try:
                            debug_api.close()
                        except Exception:
                            pass  # Ignore cleanup errors
            
            print(f"Status: {result.status.value}")
            print(f"Value: {result.value}")
            if result.error:
                print(f"Error: {result.error}")
            
            # Validation (case-insensitive)
            status_str = str(result.status.value).lower()
            if status_str == "ok":
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
