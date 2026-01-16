"""
CoinGlass API Client - Batch 2
Production-ready API client for CoinGlass data

CRITICAL RULES:
- API key in headers (X-API-KEY or similar)
- Rate limiting (basic implementation)
- Error handling (network errors, API errors)
- Returns APIResponse objects
- Thread-safe (for future async usage)
"""

import requests
import time
from typing import Dict, Any, Optional
from batch2_engine.response_models import APIResponse
from batch2_engine.param_manager import normalize_params


class CoinGlassAPI:
    """
    CoinGlass API Client
    
    Usage:
        api = CoinGlassAPI(api_key="your_key")
        response = api.fetch("/api/futures/openInterest/ohlc-aggregated-history", {"interval": "8h", "limit": "1", "symbol": "BTC"})
        
        if response.success:
            data = response.data
            # Process data...
    """
    
    BASE_URL = "https://open-api-v4.coinglass.com"
    
    def __init__(self, api_key: str, timeout: int = 30, rate_limit_delay: float = 0.1):
        """
        Initialize CoinGlass API client
        
        Args:
            api_key: CoinGlass API key
            timeout: Request timeout in seconds (default 30)
            rate_limit_delay: Minimum delay between requests in seconds (default 0.1)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "CG-API-KEY": api_key,  # CoinGlass v4 uses this header
            "Content-Type": "application/json"
        })
    
    def _rate_limit(self):
        """
        Simple rate limiting
        
        Ensures minimum delay between requests
        """
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> APIResponse:
        """
        Fetch data from CoinGlass API
        
        Args:
            endpoint: API endpoint (e.g., "/api/futures/openInterest/ohlc-aggregated-history")
            params: Query parameters (will be normalized)
        
        Returns:
            APIResponse object
        
        Error Handling:
            - Network errors → APIResponse with error
            - API errors (4xx, 5xx) → APIResponse with error
            - JSON parsing errors → APIResponse with error
        """
        # Rate limit
        self._rate_limit()
        
        # Normalize params
        if params:
            params = normalize_params(params, endpoint)
        else:
            params = {}
        
        # Build full URL
        url = self.BASE_URL + endpoint
        
        try:
            # Make request
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            # Convert to APIResponse
            return APIResponse.from_requests_response(response)
            
        except requests.exceptions.Timeout:
            return APIResponse.error_response(
                f"Request timeout after {self.timeout}s",
                status_code=408
            )
        
        except requests.exceptions.ConnectionError as e:
            return APIResponse.error_response(
                f"Connection error: {str(e)}",
                status_code=503
            )
        
        except requests.exceptions.RequestException as e:
            return APIResponse.error_response(
                f"Request failed: {str(e)}",
                status_code=500
            )
        
        except Exception as e:
            return APIResponse.error_response(
                f"Unexpected error: {str(e)}",
                status_code=500
            )
    
    def close(self):
        """Close session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()
