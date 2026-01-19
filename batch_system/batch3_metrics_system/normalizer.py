"""
Normalizer Functions - Batch 3 (v4 API Compliant)
Transform CoinGlass API v4 raw data into clean, contract-compliant values

CRITICAL RULES:
- 10 normalizer functions (daily_01 → daily_10)
- Single Responsibility: One function per metric
- Error Handling: NEVER throw exceptions - return None on any error
- Return Types: JSON-serializable only (float | dict | list | None)
- Input: APIResponse.data (Dict[str, Any]) from Batch 2

V4 API FORMAT:
- All responses: {"code": "0", "data": [...]}
- OHLC data: data[] contains objects with time, open, high, low, close
- Timestamp: milliseconds (convert to seconds: ms // 1000)
- Numeric values: may be strings, convert to float

TIMESTAMP STANDARD (CONTRACT):
- ALL timestamps MUST be integer epoch-seconds (NOT milliseconds)
- Example: 1704067200 (correct) vs 1704067200000 (incorrect - ms)
- If API returns milliseconds, normalize once in normalizer: ms // 1000
- Output layer NEVER modifies timestamps - only transports them
- This ensures consistent timestamp handling across all metrics

CONTRACT GUARANTEES:
1. Each function handles exactly one metric (SRP)
2. No exceptions raised - always return None on error
3. Returns are JSON-serializable: float | dict | list | None
4. Orchestrator handles status logic (None → MISSING, value → OK)
5. Timestamps are always integer epoch-seconds
"""

from typing import Dict, Any, Optional, List


# ============================================================================
# NORMALIZER 1: Total Open Interest (daily_01)
# ============================================================================

def normalize_total_oi(data: Dict[str, Any]) -> Optional[float]:
    """
    Normalize total open interest across all exchanges
    
    Metric: daily_01_total_open_interest
    Endpoint: /api/futures/open-interest/aggregated-history
    Params: interval=8h, limit=1, symbol=BTC
    
    V4 Response Format:
        {"code": "0", "data": [
            {"time": 1768550400000, "open": "63337761090", 
             "high": "63414094305", "low": "61941074334", 
             "close": 62342795495.894}
        ]}
    
    Args:
        data: Raw API response data from CoinGlass v4
    
    Returns:
        Float value in billions USD (e.g., 62.34 for $62.34B)
        None if error or invalid data
    
    Logic:
        1. Check code is "0" (success)
        2. Extract data list
        3. Get last item's close value (total OI)
        4. Convert to billions (divide by 1e9)
        5. Round to 2 decimals
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None
        
        # Extract data list
        data_list = data.get("data", [])
        if not data_list:
            return None
        
        # Get latest datapoint (last item in list)
        latest = data_list[-1]
        
        # Get close value (total OI)
        close_value = latest.get("close")
        if close_value is None:
            return None
        
        # Convert to float if string
        if isinstance(close_value, str):
            close_value = float(close_value)
        
        # Validate
        if close_value <= 0:
            return None
        
        # Convert to billions and round
        total_billions = close_value / 1e9
        return round(total_billions, 2)
        
    except Exception:
        return None


# ============================================================================
# NORMALIZER 2: OI Change 1h (daily_02)
# ============================================================================

def normalize_oi_change_1h(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate 1-hour percentage change in open interest

    Metric: daily_02_oi_change_1h
    Endpoint: /api/futures/open-interest/aggregated-history
    Params: interval=1h, limit=2, symbol=BTC

    V4 Response Format (can be ASC or DESC):
        {"code": "0", "data": [
            {"time": 1768546800000, "close": 62100000000.0},
            {"time": 1768550400000, "close": 62342795495.894}
        ]}

    CRITICAL: Data ordering can vary (ASC or DESC).
    Must sort by timestamp and pick last 2 valid points.

    Args:
        data: Raw API response with 2+ datapoints

    Returns:
        Float percent change (e.g., 2.45 for +2.45%, -1.23 for -1.23%)
        None if error or insufficient data

    Logic:
        1. Filter valid (time, close) pairs
        2. Sort by timestamp ascending
        3. Take last 2 points (prev, latest)
        4. Calculate: ((latest - prev) / prev) * 100
        5. Round to 2 decimals
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None

        # Extract data list
        data_list = data.get("data", [])
        if len(data_list) < 2:
            return None

        # Build valid (time, close) pairs - filter out invalid rows
        pairs = []
        for row in data_list:
            ts = row.get("time")
            close = row.get("close")
            if ts is None or close is None:
                continue
            try:
                close_val = float(close)
                if close_val > 0:
                    pairs.append((int(ts), close_val))
            except (ValueError, TypeError):
                continue

        if len(pairs) < 2:
            return None

        # Sort by timestamp ascending
        pairs_sorted = sorted(pairs, key=lambda x: x[0])

        # Take last 2 points
        prev_ts, prev_value = pairs_sorted[-2]
        latest_ts, latest_value = pairs_sorted[-1]

        # Calculate percent change
        percent_change = ((latest_value - prev_value) / prev_value) * 100
        return round(percent_change, 2)

    except Exception:
        return None


# ============================================================================
# NORMALIZER 3: OI Change 4h (daily_03)
# ============================================================================

def normalize_oi_change_4h(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate 4-hour percentage change in open interest

    Metric: daily_03_oi_change_4h
    Endpoint: /api/futures/open-interest/aggregated-history
    Params: interval=4h, limit=2, symbol=BTC

    CRITICAL: Data ordering can vary (ASC or DESC).
    Must sort by timestamp and pick last 2 valid points.

    Args:
        data: Raw API response with 2+ datapoints

    Returns:
        Float percent change
        None if error or insufficient data

    Logic: Same as normalize_oi_change_1h - timestamp-safe
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None

        # Extract data list
        data_list = data.get("data", [])
        if len(data_list) < 2:
            return None

        # Build valid (time, close) pairs - filter out invalid rows
        pairs = []
        for row in data_list:
            ts = row.get("time")
            close = row.get("close")
            if ts is None or close is None:
                continue
            try:
                close_val = float(close)
                if close_val > 0:
                    pairs.append((int(ts), close_val))
            except (ValueError, TypeError):
                continue

        if len(pairs) < 2:
            return None

        # Sort by timestamp ascending
        pairs_sorted = sorted(pairs, key=lambda x: x[0])

        # Take last 2 points
        prev_ts, prev_value = pairs_sorted[-2]
        latest_ts, latest_value = pairs_sorted[-1]

        # Calculate percent change
        percent_change = ((latest_value - prev_value) / prev_value) * 100
        return round(percent_change, 2)

    except Exception:
        return None


# ============================================================================
# NORMALIZER 4: Weighted Funding Rate (daily_04)
# ============================================================================

def normalize_weighted_funding(data: Dict[str, Any]) -> Optional[float]:
    """
    Extract current weighted average funding rate
    
    Metric: daily_04_weighted_funding_rate
    Endpoint: /api/futures/fundingRate/oi-weight-ohlc-history
    Params: interval=8h, limit=1, symbol=BTC
    
    V4 Response Format:
        {"code": "0", "data": [
            {"time": 1768550400000, "close": 0.00012345}
        ]}
    
    Args:
        data: Raw API response with latest funding rate datapoint
    
    Returns:
        Float funding rate as percent (e.g., 0.0123 for 0.0123%)
        None if error or missing data
    
    Logic:
        1. Extract latest datapoint
        2. Get close value (weighted funding rate)
        3. Convert to percent (multiply by 100 if < 1)
        4. Round to 4 decimals
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None
        
        # Extract data list
        data_list = data.get("data", [])
        if not data_list:
            return None
        
        # Get latest datapoint
        latest = data_list[-1]
        
        # Get close value (funding rate)
        funding_rate = latest.get("close")
        if funding_rate is None:
            return None
        
        # Convert to float
        rate_value = float(funding_rate)
        
        # If value is very small (< 1), assume it's already in decimal form
        # Multiply by 100 to get percentage
        if abs(rate_value) < 1:
            rate_percent = rate_value * 100
        else:
            rate_percent = rate_value
        
        return round(rate_percent, 4)
        
    except Exception:
        return None


# ============================================================================
# NORMALIZER 5: Funding Rate History (daily_05)
# ============================================================================

def normalize_funding_history(data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Extract funding rate time series (30 periods, 8h intervals)
    
    Metric: daily_05_funding_rate_history
    Endpoint: /api/futures/fundingRate/oi-weight-ohlc-history
    Params: interval=8h, limit=30, symbol=BTC
    
    V4 Response Format:
        {"code": "0", "data": [
            {"time": 1768550400000, "close": 0.00012345},
            {"time": 1768521600000, "close": 0.00011234},
            ...
        ]}
    
    Args:
        data: Raw API response with 30 datapoints
    
    Returns:
        List of dicts with timestamp and value:
        [{"timestamp": 1704067200, "value": 0.0123}, ...]
        None if error or insufficient data (less than 5 datapoints)
    
    Logic:
        1. Extract all datapoints from data list
        2. For each, extract timestamp (ms -> seconds) and funding rate
        3. Build list ordered by timestamp (oldest to newest)
        4. Return None if less than 5 datapoints (too sparse)
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None
        
        # Extract data list
        data_list = data.get("data", [])
        if len(data_list) < 5:  # Minimum threshold
            return None
        
        history = []
        for datapoint in data_list:
            # Extract timestamp (convert ms to seconds)
            timestamp_ms = datapoint.get("time")
            if timestamp_ms is None:
                continue
            
            timestamp = int(timestamp_ms) // 1000  # Convert to seconds
            
            # Extract funding rate (close value)
            rate = datapoint.get("close")
            if rate is None:
                continue
            
            # Convert rate to percentage
            rate_value = float(rate)
            if abs(rate_value) < 1:
                rate_percent = rate_value * 100
            else:
                rate_percent = rate_value
            
            history.append({
                "timestamp": timestamp,
                "value": round(rate_percent, 4)
            })
        
        # Validate we have enough datapoints
        if len(history) < 5:
            return None
        
        # Sort by timestamp (oldest to newest)
        history.sort(key=lambda x: x["timestamp"])
        
        return history
        
    except Exception:
        return None


# ============================================================================
# NORMALIZER 6: Long/Short Ratio Global (daily_06)
# ============================================================================

def normalize_long_short_global(data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extract global long/short account ratio
    
    Metric: daily_06_long_short_global
    Endpoint: /api/futures/global-long-short-account-ratio/history
    Params: interval=1h, limit=1, symbol=BTC
    
    V4 Response Format:
        {"code": "0", "data": [
            {
                "time": 1741604400000,
                "global_account_long_percent": 73.88,
                "global_account_short_percent": 26.12,
                "global_account_long_short_ratio": 2.83
            }
        ]}
    
    Args:
        data: Raw API response with long/short ratios
    
    Returns:
        Dict with long, short, ratio:
        {"long": 52.3, "short": 47.7, "ratio": 1.096}
        None if error or missing data
    
    Logic:
        1. Extract latest datapoint
        2. Get global long and short percentages
        3. Get or calculate ratio: long / short
        4. Return dict with all values
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None
        
        # Extract data list
        data_list = data.get("data", [])
        if not data_list:
            return None
        
        # Get latest datapoint
        latest = data_list[-1]
        
        # Extract values
        long_pct = latest.get("global_account_long_percent")
        short_pct = latest.get("global_account_short_percent")
        ratio = latest.get("global_account_long_short_ratio")
        
        if long_pct is None or short_pct is None:
            return None
        
        long_value = float(long_pct)
        short_value = float(short_pct)
        
        # Validate short is not zero
        if short_value <= 0:
            return None
        
        # Use provided ratio or calculate it
        if ratio is not None:
            ratio_value = float(ratio)
        else:
            ratio_value = long_value / short_value
        
        return {
            "long": round(long_value, 2),
            "short": round(short_value, 2),
            "ratio": round(ratio_value, 3)
        }
        
    except Exception:
        return None


# ============================================================================
# NORMALIZER 7: Long/Short Ratio Hyperliquid (daily_07)
# ============================================================================

def normalize_long_short_hyperliquid(data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extract Hyperliquid exchange long/short ratio
    
    Metric: daily_07_long_short_hyperliquid
    Endpoint: /api/futures/global-long-short-account-ratio/history
    Params: interval=1h, limit=1, symbol=BTC, exchange=Hyperliquid
    
    Note: For v4, this uses the same global endpoint with exchange filter.
    If Hyperliquid-specific data is not available, returns None.
    
    Args:
        data: Raw API response with per-exchange long/short ratios
    
    Returns:
        Dict with long, short, ratio for Hyperliquid
        None if Hyperliquid data not found or error
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None
        
        # Extract data list
        data_list = data.get("data", [])
        if not data_list:
            return None
        
        # Get latest datapoint
        latest = data_list[-1]
        
        # Try to find Hyperliquid-specific fields
        # (This may need adjustment based on actual API response)
        long_pct = latest.get("long_percent") or latest.get("longAccount")
        short_pct = latest.get("short_percent") or latest.get("shortAccount")
        
        if long_pct is None or short_pct is None:
            # If no specific data, return None
            return None
        
        long_value = float(long_pct)
        short_value = float(short_pct)
        
        if short_value <= 0:
            return None
        
        ratio = long_value / short_value
        
        return {
            "long": round(long_value, 2),
            "short": round(short_value, 2),
            "ratio": round(ratio, 3)
        }
        
    except Exception:
        return None


# ============================================================================
# NORMALIZER 8: 24h Liquidations Total (daily_08)
# ============================================================================

def normalize_liquidations_total(data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Calculate 24-hour liquidation summary (long/short/total)
    
    Metric: daily_08_liquidations_24h_total
    Endpoint: /api/futures/liquidation/aggregated-history
    Params: interval=4h, limit=6, symbol=BTC
    
    V4 Response Format:
        {"code": "0", "data": [
            {"time": 1768550400000, "longLiquidationUsd": 12345678, 
             "shortLiquidationUsd": 9876543},
            ...
        ]}
    
    Args:
        data: Raw API response with 6 datapoints (24h of 4h intervals)
    
    Returns:
        Dict with long, short, total, percentages:
        {
            "long": 123.45,        # million USD
            "short": 98.76,        # million USD
            "total": 222.21,       # million USD
            "long_percent": 55.5,  # percent of total
            "short_percent": 44.5  # percent of total
        }
        None if error or insufficient data
    
    Logic:
        1. Sum all long liquidations across 6 datapoints
        2. Sum all short liquidations across 6 datapoints
        3. Calculate total and percentages
        4. Convert to millions (divide by 1e6)
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None
        
        # Extract data list
        data_list = data.get("data", [])
        if len(data_list) < 6:
            return None
        
        total_long_usd = 0.0
        total_short_usd = 0.0
        
        # Sum liquidations across all 6 datapoints
        for datapoint in data_list[:6]:  # Use only first 6
            # Long liquidations - new schema first, then legacy fallback
            long_value = (
                datapoint.get("aggregated_long_liquidation_usd") or
                datapoint.get("longLiquidationUsd") or
                datapoint.get("longLiquidation") or
                datapoint.get("longVolUsd") or
                0
            )
            total_long_usd += float(long_value)

            # Short liquidations - new schema first, then legacy fallback
            short_value = (
                datapoint.get("aggregated_short_liquidation_usd") or
                datapoint.get("shortLiquidationUsd") or
                datapoint.get("shortLiquidation") or
                datapoint.get("shortVolUsd") or
                0
            )
            total_short_usd += float(short_value)
        
        # Calculate total
        total_usd = total_long_usd + total_short_usd
        
        # Validate total
        if total_usd <= 0:
            return None
        
        # Calculate percentages
        long_percent = (total_long_usd / total_usd) * 100
        short_percent = (total_short_usd / total_usd) * 100
        
        # Convert to millions
        return {
            "long": round(total_long_usd / 1e6, 2),
            "short": round(total_short_usd / 1e6, 2),
            "total": round(total_usd / 1e6, 2),
            "long_percent": round(long_percent, 1),
            "short_percent": round(short_percent, 1)
        }
        
    except Exception:
        return None


# ============================================================================
# NORMALIZER 9: Top Liquidation Events (daily_09)
# ============================================================================

def normalize_liquidation_events(data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Extract top 10 largest liquidations in 24h
    
    Metric: daily_09_top_liquidation_events
    Endpoint: /api/futures/liquidation/aggregated-history
    Params: interval=4h, limit=6, symbol=BTC
    
    Note: v4 aggregated-history may not have individual events.
    This normalizer creates synthetic events from aggregated data.
    
    Args:
        data: Raw API response with liquidation events
    
    Returns:
        List of top 10 events:
        [
            {
                "timestamp": 1704067200,
                "side": "long",
                "amount": 5.23,      # million USD
                "exchange": "Aggregated"
            },
            ...
        ]
        None if error or no events found
    
    Logic:
        1. Extract all liquidation datapoints
        2. Create events from long/short values
        3. Sort by amount (descending)
        4. Take top 10
        5. Return list with timestamp, side, amount, exchange
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None
        
        # Extract data list
        data_list = data.get("data", [])
        if not data_list:
            return None
        
        all_events = []
        
        # Extract events from all datapoints
        for datapoint in data_list:
            timestamp_ms = datapoint.get("time")
            if timestamp_ms is None:
                continue
            
            timestamp = int(timestamp_ms) // 1000  # Convert to seconds

            # Create events - new schema first, then legacy fallback
            long_value = (
                datapoint.get("aggregated_long_liquidation_usd") or
                datapoint.get("longLiquidationUsd") or
                datapoint.get("longLiquidation") or
                0
            )
            short_value = (
                datapoint.get("aggregated_short_liquidation_usd") or
                datapoint.get("shortLiquidationUsd") or
                datapoint.get("shortLiquidation") or
                0
            )
            
            if long_value > 0:
                all_events.append({
                    "timestamp": timestamp,
                    "side": "long",
                    "amount": float(long_value) / 1e6,  # Convert to millions
                    "exchange": "Aggregated"
                })
            
            if short_value > 0:
                all_events.append({
                    "timestamp": timestamp,
                    "side": "short",
                    "amount": float(short_value) / 1e6,
                    "exchange": "Aggregated"
                })
        
        # Validate we have events
        if not all_events:
            return None
        
        # Sort by amount (descending) and take top 10
        all_events.sort(key=lambda x: x["amount"], reverse=True)
        top_10 = all_events[:10]
        
        # Round amounts
        for event in top_10:
            event["amount"] = round(event["amount"], 2)
        
        return top_10
        
    except Exception:
        return None


# ============================================================================
# NORMALIZER 10: Coinbase Premium Index (daily_10)
# ============================================================================

def normalize_coinbase_premium(data: Dict[str, Any]) -> Optional[Dict[str, Optional[float]]]:
    """
    Extract Coinbase premium/discount index
    
    Metric: daily_10_coinbase_premium_index
    Endpoint: /api/coinbase-premium-index
    Params: interval=1h, limit=2, symbol=BTC
    
    V4 Response Format:
        {"code": "0", "data": [
            {"time": 1658880000, "premium": 5.55, "premium_rate": 0.0261},
            {"time": 1658876400, "premium": 5.40, "premium_rate": 0.0254}
        ]}
    
    Args:
        data: Raw API response with premium index values
    
    Returns:
        Dict with premium and 1h change:
        {
            "premium": 0.23,      # percent (positive=premium, negative=discount)
            "change_1h": 0.05     # change in last 1h (or None if insufficient data)
        }
        None if error or missing premium value
    
    Logic:
        1. Extract latest and previous datapoints
        2. Get premium_rate value (latest)
        3. Calculate 1h change if previous available
        4. Return dict with premium and change
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None
        
        # Extract data list
        data_list = data.get("data", [])
        if not data_list:
            return None
        
        # Get latest datapoint
        latest = data_list[0]
        
        # Extract premium rate (as percentage)
        premium_rate = latest.get("premium_rate")
        if premium_rate is None:
            return None
        
        # Convert to percentage
        premium_value = float(premium_rate) * 100
        
        # Try to calculate 1h change if we have previous datapoint
        change_1h = None
        if len(data_list) >= 2:
            previous = data_list[1]
            prev_rate = previous.get("premium_rate")
            
            if prev_rate is not None:
                prev_value = float(prev_rate) * 100
                change_1h = premium_value - prev_value
                change_1h = round(change_1h, 4)
        
        return {
            "premium": round(premium_value, 4),
            "change_1h": change_1h
        }
        
    except Exception:
        return None

# ============================================================================
# NORMALIZER 11: Fear & Greed Index (weekly_16)
# ============================================================================

def normalize_fear_greed_index(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract Fear & Greed Index with 7-day trend

    Metric: weekly_16_fear_greed_index
    Endpoint: /api/index/fear-greed-history
    Params: (none required)

    V4 Response Format (VERIFIED via runtime test):
        {"code": "0", "data": {
            "data_list": [...],  # index values 0-100
            "price_list": [...],
            "time_list": [...]   # timestamps in ms, ASCENDING (old->new)
        }}

    CRITICAL: time_list is ASCENDING (oldest first, newest last).
    Must find max(time_list) to get latest value.

    Args:
        data: Raw API response with fear/greed history

    Returns:
        Dict with current value, label, and 7d change:
        {"value": 72, "label": "Greed", "change_7d": 5.0}
        None if error or missing data
    """
    DAY_MS = 86400000  # milliseconds per day

    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None

        # Extract inner data object
        inner_data = data.get("data", {})
        if not isinstance(inner_data, dict):
            return None

        # Extract parallel lists
        data_list = inner_data.get("data_list", [])
        time_list = inner_data.get("time_list", [])

        if not data_list or not time_list or len(data_list) != len(time_list):
            return None

        # Find latest value by max timestamp
        latest_idx = max(range(len(time_list)), key=lambda i: time_list[i])
        latest_ts = time_list[latest_idx]
        current_value = float(data_list[latest_idx])

        # Validate range (0-100)
        if current_value < 0 or current_value > 100:
            return None

        # Calculate 7d change: find timestamp <= (latest - 7 days)
        change_7d = None
        target_ts = latest_ts - (7 * DAY_MS)

        # Reverse scan to find prev value (timestamp <= target)
        prev_idx = None
        for i in range(len(time_list) - 1, -1, -1):
            if time_list[i] <= target_ts:
                prev_idx = i
                break

        if prev_idx is not None:
            prev_value = float(data_list[prev_idx])
            change_7d = round(current_value - prev_value, 1)

        # Assign label based on standard Fear & Greed ranges
        if current_value <= 24:
            label = "Extreme Fear"
        elif current_value <= 44:
            label = "Fear"
        elif current_value <= 55:
            label = "Neutral"
        elif current_value <= 75:
            label = "Greed"
        else:
            label = "Extreme Greed"

        return {
            "value": int(current_value),
            "label": label,
            "change_7d": change_7d
        }

    except Exception:
        return None


# ============================================================================
# NORMALIZER 12: Bitcoin Dominance Change (weekly_11)
# ============================================================================

def normalize_btc_dominance_change(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract Bitcoin Dominance with 7-day change

    Metric: weekly_11_btc_dominance_change
    Endpoint: /api/index/bitcoin-dominance
    Params: (none required)

    V4 Response Format (VERIFIED via runtime test):
        {"code": "0", "data": [
            {"timestamp": 1367366400000, "bitcoin_dominance": 94.35, ...},  # OLDEST
            ...
            {"timestamp": 1768608000000, "bitcoin_dominance": 59.07, ...}   # NEWEST
        ]}

    CRITICAL: data is ASCENDING (oldest first, newest last).
    Must find max(timestamp) to get latest value.

    Args:
        data: Raw API response with bitcoin dominance history

    Returns:
        Dict with current value and 7d change:
        {"value": 57.23, "change_7d": 0.34}
        None if error or missing data
    """
    DAY_MS = 86400000  # milliseconds per day

    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None

        # Extract data list
        data_list = data.get("data", [])
        if not data_list or len(data_list) < 1:
            return None

        # Find latest value by max timestamp
        # NOTE: This endpoint uses "timestamp" key, not "time"
        latest_idx = max(range(len(data_list)), key=lambda i: data_list[i].get("timestamp", 0))
        latest = data_list[latest_idx]
        latest_ts = latest.get("timestamp", 0)

        current_value = latest.get("bitcoin_dominance")
        if current_value is None:
            return None

        current_value = float(current_value)

        # Validate range (0-100%)
        if current_value < 0 or current_value > 100:
            return None

        # Calculate 7d change: find timestamp <= (latest - 7 days)
        change_7d = None
        target_ts = latest_ts - (7 * DAY_MS)

        # Reverse scan to find prev value (timestamp <= target)
        prev_idx = None
        for i in range(len(data_list) - 1, -1, -1):
            row_ts = data_list[i].get("timestamp", 0)
            if row_ts <= target_ts:
                prev_idx = i
                break

        if prev_idx is not None:
            prev_value = data_list[prev_idx].get("bitcoin_dominance")
            if prev_value is not None:
                change_7d = round(current_value - float(prev_value), 2)

        return {
            "value": round(current_value, 2),
            "change_7d": change_7d
        }

    except Exception:
        return None


# ============================================================================
# NORMALIZER 13: Basis Spread 7d (weekly_04)
# ============================================================================

def normalize_basis_spread(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract Futures Basis Spread with 7-day change

    Metric: weekly_04_basis_spread
    Endpoint: /api/futures/basis/history
    Params: exchange=Binance, symbol=BTCUSDT, interval=1d, limit=14

    V4 Response Format (VERIFIED via runtime test):
        {"code": "0", "data": [
            {"time": 1767830400000, "open_basis": 0.12, "close_basis": 0.15, ...},  # OLDEST
            ...
            {"time": 1768953600000, "open_basis": 0.18, "close_basis": 0.20, ...}   # NEWEST
        ]}

    CRITICAL: data is ASCENDING (oldest first, newest last).
    Must find max(time) to get latest value.

    Args:
        data: Raw API response with basis history

    Returns:
        Dict with current value and 7d change:
        {"value": 0.20, "change_7d": 0.05}
        None if error or missing data
    """
    DAY_MS = 86400000  # milliseconds per day

    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None

        # Extract data list
        data_list = data.get("data", [])
        if not data_list or len(data_list) < 1:
            return None

        # Find latest value by max timestamp
        latest_idx = max(range(len(data_list)), key=lambda i: data_list[i].get("time", 0))
        latest = data_list[latest_idx]
        latest_ts = latest.get("time", 0)

        # Get close_basis as the value
        current_value = latest.get("close_basis")
        if current_value is None:
            return None

        current_value = float(current_value)

        # Calculate 7d change: find timestamp <= (latest - 7 days)
        change_7d = None
        target_ts = latest_ts - (7 * DAY_MS)

        # Reverse scan to find prev value (timestamp <= target)
        prev_idx = None
        for i in range(len(data_list) - 1, -1, -1):
            row_ts = data_list[i].get("time", 0)
            if row_ts <= target_ts:
                prev_idx = i
                break

        if prev_idx is not None:
            prev_value = data_list[prev_idx].get("close_basis")
            if prev_value is not None:
                change_7d = round(current_value - float(prev_value), 4)

        return {
            "value": round(current_value, 4),
            "change_7d": change_7d
        }

    except Exception:
        return None


# ============================================================================
# NORMALIZER 14: ETH/BTC Ratio Change (weekly_12)
# ============================================================================

def normalize_eth_btc_ratio(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Calculate ETH/BTC ratio from spot prices with 7-day change

    Metric: weekly_12_eth_btc_ratio_change
    Fetch Plan (multi-endpoint):
        - eth: /api/spot/price/history (Binance, ETHUSDT, 1d, limit=8)
        - btc: /api/spot/price/history (Binance, BTCUSDT, 1d, limit=8)

    Input Format (from orchestrator fetch_plan):
        {
            "eth": {"code": "0", "data": [{"time": ms, "close": "3217.2", ...}, ...]},
            "btc": {"code": "0", "data": [{"time": ms, "close": "92972.06", ...}, ...]}
        }

    CRITICAL: data lists are ASCENDING (oldest first, newest last).
    Must find max(time) to get latest value.

    Args:
        data: Combined dict with "eth" and "btc" raw API responses

    Returns:
        Dict with ratio and 7d change:
        {"value": 0.03460394, "change_7d": 0.00069509}
        None if error or missing data
    """
    DAY_MS = 86400000  # milliseconds per day

    def extract_latest_and_prev_7d(raw_response: Dict[str, Any]):
        """Extract latest and 7d-ago close values from spot price history"""
        code = str(raw_response.get("code", ""))
        if code not in ("0", "00", "success"):
            return None, None

        data_list = raw_response.get("data", [])
        if not data_list:
            return None, None

        # Build (time, close) pairs
        pairs = []
        for row in data_list:
            ts = row.get("time")
            close = row.get("close")
            if ts is None or close is None:
                continue
            pairs.append((int(ts), float(close)))

        if not pairs:
            return None, None

        # Find latest by max timestamp
        latest_ts, latest_val = max(pairs, key=lambda x: x[0])
        target_ts = latest_ts - (7 * DAY_MS)

        # Reverse scan for 7d-ago value
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        prev_val = None
        for ts, val in reversed(pairs_sorted):
            if ts <= target_ts:
                prev_val = val
                break

        return latest_val, prev_val

    try:
        # Extract ETH and BTC data
        eth_raw = data.get("eth")
        btc_raw = data.get("btc")

        if not eth_raw or not btc_raw:
            return None

        eth_latest, eth_prev = extract_latest_and_prev_7d(eth_raw)
        btc_latest, btc_prev = extract_latest_and_prev_7d(btc_raw)

        if eth_latest is None or btc_latest is None:
            return None
        if btc_latest <= 0:
            return None

        # Calculate current ratio
        ratio_latest = eth_latest / btc_latest

        # Calculate 7d change if we have previous values
        change_7d = None
        if eth_prev is not None and btc_prev is not None and btc_prev > 0:
            ratio_prev = eth_prev / btc_prev
            change_7d = round(ratio_latest - ratio_prev, 8)

        return {
            "value": round(ratio_latest, 8),
            "change_7d": change_7d
        }

    except Exception:
        return None


# ============================================================================
# NORMALIZER 15: Funding Rate Avg 7d (weekly_05)
# ============================================================================

def normalize_funding_rate_avg_7d(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Calculate 7-day average funding rate with week-over-week change

    Metric: weekly_05_funding_rate_avg
    Endpoint: /api/futures/funding-rate/history
    Params: exchange=Binance, symbol=BTCUSDT, interval=1d, limit=14

    V4 Response Format (VERIFIED via runtime test):
        {"code": "0", "data": [
            {"time": 1767657600000, "open": "-0.001376", "close": "0.006618", ...},  # OLDEST
            ...
            {"time": 1768694400000, "open": "0.003502", "close": "...", ...}         # NEWEST
        ]}

    CRITICAL: data is ASCENDING (oldest first, newest last).
    We need 14 days to calculate current 7d avg and previous 7d avg.

    Args:
        data: Raw API response with funding rate history (14 daily bars)

    Returns:
        Dict with 7d average and week-over-week change:
        {"value": 0.00345, "change_7d": 0.00012}
        None if error or insufficient data (< 14 bars)
    """
    try:
        # Check success code
        code = str(data.get("code", ""))
        if code not in ("0", "00", "success"):
            return None

        # Extract data list
        data_list = data.get("data", [])
        if not data_list or len(data_list) < 14:
            return None  # Need 14 days for current + previous week

        # Build (time, close) pairs
        pairs = []
        for row in data_list:
            ts = row.get("time")
            close = row.get("close")
            if ts is None or close is None:
                continue
            pairs.append((int(ts), float(close)))

        if len(pairs) < 14:
            return None

        # Sort by timestamp (ascending)
        pairs_sorted = sorted(pairs, key=lambda x: x[0])

        # Take last 14 days
        last_14 = pairs_sorted[-14:]

        # Current week: last 7 bars (most recent)
        current_week = last_14[-7:]
        # Previous week: first 7 bars of last_14
        prev_week = last_14[:7]

        # Calculate averages
        current_avg = sum(val for _, val in current_week) / len(current_week)
        prev_avg = sum(val for _, val in prev_week) / len(prev_week)

        # Change is current - previous
        change_7d = current_avg - prev_avg

        return {
            "value": round(current_avg, 6),
            "change_7d": round(change_7d, 6)
        }

    except Exception:
        return None


# Helper function for unwrapping CoinGlass API response
def _unwrap_coinglass_data(payload):
    """
    Unwrap CoinGlass API response format.
    CoinGlass v4 returns {"code":"0","data":[...]} wrapper.
    """
    if payload is None:
        return None
    if isinstance(payload, dict):
        if "data" in payload:
            return payload.get("data")
        return payload
    return payload
