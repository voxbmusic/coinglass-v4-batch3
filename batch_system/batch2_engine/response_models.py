"""
Response Models - Batch 2
Data models for CoinGlass API responses

CRITICAL RULES:
- APIResponse wraps raw API responses
- .data contains the actual payload (Dict[str, Any])
- .success indicates if request was successful
- Clean separation between HTTP layer and data layer
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class APIResponse:
    """
    Wrapper for CoinGlass API responses
    
    Attributes:
        data: Raw API response data (Dict[str, Any])
              This is what normalizers consume
        status_code: HTTP status code (200, 404, 500, etc.)
        success: Whether request was successful (2xx status)
        error: Error message if request failed (optional)
        raw_response: Full response object (optional, for debugging)
    
    Usage:
        response = APIResponse(
            data={"dataList": [...]},
            status_code=200,
            success=True
        )
        
        # Normalizer consumes:
        normalized = normalize_func(response.data)
    """
    
    data: Dict[str, Any]
    status_code: int
    success: bool
    error: Optional[str] = None
    raw_response: Optional[Any] = None
    
    @classmethod
    def from_requests_response(cls, response) -> 'APIResponse':
        """
        Create APIResponse from requests.Response object
        
        CRITICAL SUCCESS LOGIC (v4-compliant):
        1. HTTP status must be 2xx
        2. Response body must parse as JSON
        3. Body "code" field must be "0" (or "00" or "success")
        
        CoinGlass v4 returns HTTP 200 even for errors:
        {"code": "400", "msg": "API key missing."}
        
        This dual-check prevents false positives.
        
        Args:
            response: requests.Response object
        
        Returns:
            APIResponse instance
        """
        status_code = response.status_code
        
        # Step 1: Check HTTP status
        if not (200 <= status_code < 300):
            return cls(
                data={},
                status_code=status_code,
                success=False,
                error=f"HTTP {status_code}",
                raw_response=response
            )
        
        # Step 2: Parse JSON
        try:
            data = response.json()
        except Exception as e:
            return cls(
                data={},
                status_code=status_code,
                success=False,
                error=f"JSON parse error: {str(e)}",
                raw_response=response
            )
        
        # Step 3: Check body "code" field (CRITICAL for v4)
        body_code = str(data.get("code", ""))
        
        # Success codes: "0", "00", "success"
        if body_code in ("0", "00", "success"):
            return cls(
                data=data,
                status_code=status_code,
                success=True,
                error=None,
                raw_response=response
            )
        else:
            # API returned error in body
            error_msg = data.get("msg", f"API error (code: {body_code})")
            return cls(
                data=data,
                status_code=status_code,
                success=False,
                error=error_msg,
                raw_response=response
            )
    
    @classmethod
    def error_response(cls, error_message: str, status_code: int = 500) -> 'APIResponse':
        """
        Create error response
        
        Args:
            error_message: Error description
            status_code: HTTP status code (default 500)
        
        Returns:
            APIResponse with error
        """
        return cls(
            data={},
            status_code=status_code,
            success=False,
            error=error_message
        )
