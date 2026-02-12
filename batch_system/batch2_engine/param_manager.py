"""
Parameter Manager - Batch 2
Normalize and validate API request parameters

CRITICAL RULES:
- All intervals must be strings: "1h", "4h", "8h" (NOT integers)
- All limits must be strings: "1", "30" (NOT integers)
- Symbol standardization: "BTC" (consistent ticker format)
- Endpoint-specific parameter validation
"""

from typing import Dict, Any


# Valid parameter values
VALID_INTERVALS = [
    "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h", "24h",
    "1d", "7d", "30d"
]
VALID_SYMBOLS = ["BTC", "ETH", "BNB"]  # Extensible


def normalize_params(params: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    """
    Normalize API request parameters to CoinGlass standards
    
    This function ensures parameters are in the correct format:
    - interval: string (e.g., "1h", "4h")
    - limit: string (e.g., "1", "30")
    - symbol: string (e.g., "BTC")
    
    Args:
        params: Raw parameters dict
        endpoint: API endpoint (for endpoint-specific validation)
    
    Returns:
        Normalized parameters dict
    
    Example:
        # Input
        params = {"interval": 1, "limit": 30, "symbol": "btc"}
        
        # Output
        {
            "interval": "1h",
            "limit": "30",
            "symbol": "BTC"
        }
    """
    if params is None:
        return {}
    
    normalized = {}
    
    # Normalize interval (ensure string)
    if "interval" in params:
        interval = params["interval"]
        if isinstance(interval, int):
            # Convert integer to string with "h" suffix
            interval = f"{interval}h"
        elif isinstance(interval, str):
            # Ensure lowercase
            interval = interval.lower()
            # If no unit, assume hours
            if interval.isdigit():
                interval = f"{interval}h"
        
        # Validate
        if interval in VALID_INTERVALS:
            normalized["interval"] = interval
        else:
            # Default to 1h if invalid
            normalized["interval"] = "1h"
    
    # Normalize limit (ensure string)
    if "limit" in params:
        limit = params["limit"]
        if isinstance(limit, int):
            # Convert to string
            limit = str(limit)
        elif isinstance(limit, str):
            # Ensure it's numeric
            if not limit.isdigit():
                limit = "1"
        
        normalized["limit"] = limit
    
    # Normalize symbol (ensure uppercase)
    if "symbol" in params:
        symbol = params["symbol"]
        if isinstance(symbol, str):
            symbol = symbol.upper()
            
            # Handle common variants
            if symbol in ["BITCOIN", "BITCOINUSDT"]:
                symbol = "BTC"

            
            normalized["symbol"] = symbol
        else:
            normalized["symbol"] = "BTC"  # Default
    
    # Copy other parameters as-is
    for key, value in params.items():
        if key not in ["interval", "limit", "symbol"]:
            normalized[key] = value
    
    return normalized


def validate_params(params: Dict[str, Any], required: list = None) -> bool:
    """
    Validate that required parameters are present
    
    Args:
        params: Parameters dict
        required: List of required parameter names
    
    Returns:
        True if all required parameters present, False otherwise
    """
    if required is None:
        return True
    
    for param in required:
        if param not in params:
            return False
    
    return True
