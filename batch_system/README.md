# Batch System - CoinGlass v4 Integration

**Status:** ⚠️ AWAITING SMOKE TEST VALIDATION  
**Version:** 0.3.0-alpha  
**Date:** 2025-01-16

---

## 🚨 CRITICAL WARNING - FUNDING RATE SCALING

**The funding rate normalization uses a CONSERVATIVE HEURISTIC that requires validation with real API output.**

### Current Rule (TEMPORARY):
```python
if abs(rate_value) < 0.001:
    rate_percent = rate_value * 100
else:
    rate_percent = rate_value
```

### Why This Matters:
- CoinGlass v4 API may return funding rates in DECIMAL format (0.0001) or PERCENT format (0.01)
- The 0.001 threshold is an educated guess based on typical funding rates (bps range)
- **IF FIRST SMOKE TEST OUTPUT SHOWS ABSURD VALUES (e.g., 0.2-1.0% or higher for 8h funding), THIS IS LIKELY A SCALE ISSUE**

### What Happens Next:
1. Bartu runs smoke test → Gets funding rate value
2. If value looks wrong (too high/low by 10x-100x), Helm will:
   - Adjust threshold in helper function
   - Create new package
   - No manual file edits by Bartu

### Expected Ranges (for validation):
- **Normal 8h funding rate:** 0.001% to 0.05% (1-50 bps)
- **Extreme 8h funding rate:** 0.1% to 0.2% (100-200 bps, rare)
- **ABSURD (scale error):** >0.5% or <0.0001%

**If smoke test shows absurd values, DO NOT PANIC. Just send output to Helm for immediate fix.**

---

## 📦 Package Structure

```
batch_system/
├── batch2_engine/           # API client layer
│   ├── coinglass.py        # v4 API client (CG-API-KEY header)
│   ├── response_models.py  # HTTP + body.code validation
│   └── param_manager.py    # Parameter normalization
├── batch3_metrics_system/   # Metrics layer
│   ├── metric_definitions.py  # Metric models
│   ├── metric_registry.py     # 10 daily metrics
│   ├── normalizer.py          # 10 normalizer functions
│   ├── orchestrator.py        # Fetch + normalize pipeline
│   └── output.py              # JSON Contract v1 formatter
├── smoke_test.py            # Quick validation (3 metrics)
└── README.md                # This file
```

---

## 🎯 What's Implemented

### ✅ Batch 2 - API Client
- CoinGlass v4 API client with `CG-API-KEY` header
- Dual success validation: HTTP 2xx + body.code == "0"
- Rate limiting (0.1s default, configurable)
- Error handling (timeout, connection, parsing)

### ✅ Batch 3 - Daily Metrics (10 total)
1. **daily_01** - Total Open Interest (snapshot, billions USD)
2. **daily_02** - OI Change 1h (percent)
3. **daily_03** - OI Change 4h (percent)
4. **daily_04** - Weighted Funding Rate (percent, 8h)
5. **daily_05** - Funding Rate History (30 periods, 8h intervals)
6. **daily_06** - Long/Short Ratio Global (snapshot)
7. **daily_07** - Long/Short Ratio Hyperliquid (EXTERNAL_REQUIRED - placeholder)
8. **daily_08** - 24h Liquidations Total (with time range validation)
9. **daily_09** - Top Liquidation Intervals (synthetic from aggregated data)
10. **daily_10** - Coinbase Premium Index (snapshot)

### ⚠️ Known Limitations
- **daily_07 (Hyperliquid):** No exchange-specific endpoint found. Status = EXTERNAL_REQUIRED
- **daily_09 (Events):** Synthetic intervals from aggregated data, NOT real liquidation orders
- **Funding rate scale:** Conservative heuristic, needs first output validation

---

## 🚀 Quick Start (Smoke Test)

### Prerequisites
- Python 3.8+
- CoinGlass API key (v4)
- Required Python packages

⚠️ **SECURITY WARNING:** Never hardcode your API key in code. Always use the environment variable `COINGLASS_API_KEY` or pass it as a command-line argument.

### Install Dependencies
```bash
# Recommended: Use python3 -m pip (ensures correct Python version)
python3 -m pip install -r requirements.txt

# Or manually:
python3 -m pip install "requests>=2.28.0,<3.0.0"
```

### Run Smoke Test
```bash
# Method 1: Direct API key
python3 smoke_test.py YOUR_API_KEY

# Method 2: Environment variable
export COINGLASS_API_KEY=your_key
python3 smoke_test.py
```

### Expected Output
```
======================================================================
SMOKE TEST - 3 Critical Metrics
======================================================================

======================================================================
Testing: daily_01_total_open_interest
======================================================================
Status: OK
Value: 62.34
✅ PASS

======================================================================
Testing: daily_04_weighted_funding_rate
======================================================================
Status: OK
Value: 0.0123
✅ PASS

======================================================================
Testing: daily_10_coinbase_premium_index
======================================================================
Status: OK
Value: {'premium': 0.2345, 'change_1h': 0.0012}
✅ PASS

======================================================================
SMOKE TEST SUMMARY
======================================================================

RESULT: 3/3 PASSED
✅ daily_01_total_open_interest: PASS → 62.34
✅ daily_04_weighted_funding_rate: PASS → 0.0123
✅ daily_10_coinbase_premium_index: PASS → {'premium': 0.2345, 'change_1h': 0.0012}

======================================================================
```

### What to Send to Helm
**Copy the ENTIRE output above** (from "SMOKE TEST" to final "======") and send to Helm.

**CRITICAL:** If funding rate value (daily_04) looks wrong (e.g., >0.5% or <0.0001%), mention it explicitly.

---

## 🔧 Technical Details

### Timestamp Standard
- **Input:** API returns milliseconds (1704067200000)
- **Normalization:** Convert to epoch seconds (ms // 1000 → 1704067200)
- **Output:** Integer epoch seconds (contract-stable)

### Data Ordering
- **All normalizers sort by "time" field:** `sorted(data_list, key=lambda x: x.get("time", 0), reverse=True)`
- **This ensures deterministic results** regardless of API response order

### 24h Liquidations Validation
- Checks time span between first and last datapoint
- Valid range: 20-28 hours (±4h tolerance)
- Returns None if data gaps detected

### Funding Rate Helper
- Single source of truth: `normalize_funding_rate_value()`
- Used by: daily_04, daily_05
- Current threshold: 0.001 (CONSERVATIVE, may need adjustment)

---

## 🐛 Troubleshooting

### Smoke Test Fails with "API key missing"
- Check API key is correct (v4 format)
- Verify key has permissions for all endpoints

### Smoke Test Shows MISSING for daily_04
- Check funding rate endpoint accessibility
- Verify API response format matches v4

### Funding Rate Value Looks Wrong
- **Too high (>0.5%):** Likely scale issue, threshold too high
- **Too low (<0.0001%):** Likely scale issue, threshold too low
- **Send output to Helm immediately** - do NOT edit files

### daily_07 Shows EXTERNAL_REQUIRED
- **This is CORRECT behavior** - Hyperliquid endpoint not found
- Status should be EXTERNAL_REQUIRED, not MISSING
- If shows MISSING, send to Helm for fix

---

## 📋 Checklist Before GitHub PR Merge

- [ ] Smoke test passes (3/3 PASSED)
- [ ] Funding rate value in expected range (0.001-0.2%)
- [ ] daily_07 shows EXTERNAL_REQUIRED (not MISSING)
- [ ] No absurd values in any metric
- [ ] Lupo review complete
- [ ] All critical warnings addressed

**DO NOT MERGE PR until all checkboxes checked.**

---

## 🔗 Links

- **CoinGlass v4 API Docs:** https://coinglass.com/api-docs (check latest)
- **GitHub PR:** [Will be added when created]
- **Contract Spec:** JSON Contract v1 (internal doc)

---

## 📞 Contact

**Questions/Issues:** Report to Helm  
**Scale Issues:** DO NOT edit files, report to Helm  
**Package Updates:** Wait for new package from Helm

---

**Last Updated:** 2025-01-16  
**Next Milestone:** Smoke test validation + funding rate confirmation
