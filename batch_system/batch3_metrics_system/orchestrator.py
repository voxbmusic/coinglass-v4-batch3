"""
Orchestrator - Batch 3
Pipeline orchestration for metric fetching, normalization, and status handling

CRITICAL RULES:
- implemented=False metrics: NEVER fetch/normalize - pass-through default_status + value=None
- implemented=True metrics: Deterministic status logic (fetch fail or normalize None => MISSING, else OK)
- Each metric is independent (one failure doesn't kill others)
- Clean separation: fetch | normalize | status

STATUS PRIORITY (DETERMINISTIC):
For implemented=False:
  - status = metric.default_status (LOCKED or EXTERNAL_REQUIRED from registry)
  - value = None
  - NO fetch, NO normalize

For implemented=True:
  - if fetch_failed or normalize_returned_none:
      status = MISSING
      value = None
  - else:
      status = OK
      value = normalized_value (float | dict | list)
"""

from typing import Dict, Any, Optional, List
from batch3_metrics_system.metric_definitions import MetricDefinition, MetricStatus
from batch3_metrics_system.metric_registry import PANEL_REGISTRY, get_all_implemented_metrics
from batch3_metrics_system import normalizer

# Batch 2 imports - DETERMINISTIC (no fallback)
from batch2_engine.coinglass import CoinGlassAPI
from batch2_engine.param_manager import normalize_params


# ============================================================================
# METRIC RESULT MODEL
# ============================================================================

class MetricResult:
    """
    Result container for a single metric fetch + normalize operation
    
    Attributes:
        metric_id: Metric identifier (e.g., "daily_01_total_open_interest")
        status: MetricStatus enum value (OK, MISSING, LOCKED, EXTERNAL_REQUIRED)
        value: Normalized value (float | dict | list | None)
        error: Error message if status is MISSING (optional, debug-only)
    
    CONTRACT NOTE:
    - error field is DEBUG-ONLY (not part of JSON Contract v1)
    - output.py may optionally include error in 'notes' field
    - error does NOT become a required field in JSON output
    - This prevents contract drift
    """
    
    def __init__(
        self,
        metric_id: str,
        status: MetricStatus,
        value: Optional[Any] = None,
        error: Optional[str] = None
    ):
        self.metric_id = metric_id
        self.status = status
        self.value = value
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            'metric_id': self.metric_id,
            'status': self.status.value,
            'value': self.value
        }
        if self.error:
            result['error'] = self.error
        return result


# ============================================================================
# CORE ORCHESTRATOR
# ============================================================================

class MetricOrchestrator:
    """
    Orchestrates metric fetching, normalization, and status handling
    
    Key responsibilities:
    1. Distinguish between implemented and registry-only metrics
    2. For implemented metrics: fetch → normalize → determine status
    3. For registry-only metrics: pass-through default_status
    4. Handle errors gracefully (one metric failure doesn't affect others)
    """
    
    def __init__(self, api_client: CoinGlassAPI):
        """
        Initialize orchestrator with CoinGlass API client
        
        INJECTION PATTERN: Accepts CoinGlassAPI instance for better testability
        - Real API test: MetricOrchestrator(CoinGlassAPI(api_key))
        - Unit test: MetricOrchestrator(MockCoinGlassAPI())
        - Same code path for both scenarios
        
        Args:
            api_client: CoinGlassAPI instance (real or mock)
        """
        self.api = api_client
        
        # Map normalizer function names to actual functions
        self.normalizer_map = {
            'normalize_total_oi': normalizer.normalize_total_oi,
            'normalize_oi_change_1h': normalizer.normalize_oi_change_1h,
            'normalize_oi_change_4h': normalizer.normalize_oi_change_4h,
            'normalize_weighted_funding': normalizer.normalize_weighted_funding,
            'normalize_funding_history': normalizer.normalize_funding_history,
            'normalize_long_short_global': normalizer.normalize_long_short_global,
            'normalize_long_short_hyperliquid': normalizer.normalize_long_short_hyperliquid,
            'normalize_liquidations_total': normalizer.normalize_liquidations_total,
            'normalize_liquidation_events': normalizer.normalize_liquidation_events,
            'normalize_coinbase_premium': normalizer.normalize_coinbase_premium,
            # Weekly normalizers
            'normalize_fear_greed_index': normalizer.normalize_fear_greed_index,
            'normalize_btc_dominance_change': normalizer.normalize_btc_dominance_change,
            'normalize_basis_spread': normalizer.normalize_basis_spread,
            'normalize_eth_btc_ratio': normalizer.normalize_eth_btc_ratio,
            'normalize_funding_rate_avg_7d': normalizer.normalize_funding_rate_avg_7d,
            'normalize_long_liquidations_7d': normalizer.normalize_long_liquidations_7d,
            'normalize_short_liquidations_7d': normalizer.normalize_short_liquidations_7d,
            'normalize_oi_trend_7d': normalizer.normalize_oi_trend_7d,
            'normalize_major_exchange_volume_7d': normalizer.normalize_major_exchange_volume_7d,
            'normalize_perp_volume_change_7d': normalizer.normalize_perp_volume_change_7d
        }
    
    def fetch_and_normalize(self, metric: MetricDefinition) -> MetricResult:
        """
        Fetch and normalize a single metric
        
        This is the core pipeline:
        1. Check if metric is implemented
        2. If not implemented: return default_status + value=None (pass-through)
        3. If implemented: fetch → normalize → determine status
        
        Args:
            metric: MetricDefinition from registry
        
        Returns:
            MetricResult with status and value
        
        Status Logic (DETERMINISTIC):
        - implemented=False: status = metric.default_status, value = None
        - implemented=True:
            - fetch failed OR normalize returned None => MISSING, value = None
            - normalize returned value => OK, value = normalized_value
        """
        # RULE 1: implemented=False => pass-through (NO fetch, NO normalize)
        if not metric.implemented:
            return MetricResult(
                metric_id=metric.id,
                status=metric.default_status,
                value=None,
                error=None
            )
        
        # RULE 2: implemented=True => fetch + normalize + deterministic status
        
        # Step 1: Fetch raw data
        raw_data = self._fetch_raw_data(metric)
        if raw_data is None:
            # Fetch failed
            return MetricResult(
                metric_id=metric.id,
                status=MetricStatus.MISSING,
                value=None,
                error="API fetch failed"
            )
        
        # Step 2: Normalize data
        normalized_value = self._normalize_data(metric, raw_data)
        if normalized_value is None:
            # Normalize failed (returned None)
            return MetricResult(
                metric_id=metric.id,
                status=MetricStatus.MISSING,
                value=None,
                error="Normalization returned None"
            )
        
        # Step 3: Success - return OK with value
        return MetricResult(
            metric_id=metric.id,
            status=MetricStatus.OK,
            value=normalized_value,
            error=None
        )
    
    def _fetch_raw_data(self, metric: MetricDefinition) -> Optional[Dict[str, Any]]:
        """
        Fetch raw data from CoinGlass API

        Supports two modes:
        1. Single endpoint: Uses metric.endpoint + metric.params
        2. Multi-endpoint (fetch_plan): Fetches multiple endpoints, combines results

        Args:
            metric: MetricDefinition with endpoint/params OR fetch_plan

        Returns:
            Single endpoint: Raw API response data (APIResponse.data)
            Multi-endpoint: Combined dict {"name1": data1, "name2": data2, ...}
            None if any fetch failed
        """
        try:
            # Check for multi-endpoint fetch_plan
            if metric.fetch_plan:
                return self._fetch_multi_endpoint(metric.fetch_plan)

            # Single endpoint mode (original behavior)
            # Normalize params using Batch 2 normalize_params
            normalized_params = normalize_params(metric.params or {}, metric.endpoint)

            # Fetch from API
            response = self.api.fetch(metric.endpoint, normalized_params)

            # Extract data from APIResponse
            # In Batch 2, response is APIResponse object with .data attribute
            if response is None:
                return None

            # Handle both APIResponse object and dict (for compatibility)
            if hasattr(response, 'data'):
                return response.data
            elif isinstance(response, dict):
                return response.get('data')
            else:
                return None
                
        except Exception:
            # Any fetch error => return None
            return None

    def _fetch_multi_endpoint(self, fetch_plan: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Fetch multiple endpoints and combine results

        Generic multi-endpoint support for metrics that need data from multiple API calls.
        Each item in fetch_plan must have: name, endpoint, params

        Args:
            fetch_plan: List of {"name": str, "endpoint": str, "params": dict}

        Returns:
            Combined dict: {"name1": raw_response1, "name2": raw_response2, ...}
            None if ANY fetch fails (all-or-nothing)
        """
        combined = {}

        for item in fetch_plan:
            name = item.get("name")
            endpoint = item.get("endpoint")
            params = item.get("params", {})

            if not name or not endpoint:
                return None

            # Normalize params
            normalized_params = normalize_params(params, endpoint)

            # Fetch from API
            response = self.api.fetch(endpoint, normalized_params)

            if response is None:
                return None  # All-or-nothing: any failure => None

            # Extract raw data (full response for normalizer to handle)
            if hasattr(response, 'data'):
                combined[name] = response.data
            elif isinstance(response, dict):
                combined[name] = response
            else:
                return None

        return combined

    def _normalize_data(self, metric: MetricDefinition, raw_data: Dict[str, Any]) -> Optional[Any]:
        """
        Normalize raw data using appropriate normalizer function
        
        Args:
            metric: MetricDefinition with normalizer function name
            raw_data: Raw API response data
        
        Returns:
            Normalized value (float | dict | list)
            None if normalization failed
        """
        try:
            # Get normalizer function
            normalizer_func = self.normalizer_map.get(metric.normalizer)
            if normalizer_func is None:
                return None
            
            # Call normalizer (normalizer handles its own errors and returns None on failure)
            normalized_value = normalizer_func(raw_data)
            
            return normalized_value
            
        except Exception:
            # Any normalization error => return None
            return None
    
    def fetch_all_metrics(self, timeframe: str) -> List[MetricResult]:
        """
        Fetch and normalize all metrics for a given timeframe
        
        Args:
            timeframe: 'daily', 'weekly', or 'monthly'
        
        Returns:
            List of MetricResult objects
        """
        metrics = PANEL_REGISTRY.get(timeframe, [])
        results = []
        
        for metric in metrics:
            result = self.fetch_and_normalize(metric)
            results.append(result)
        
        return results
    
    def fetch_all_daily_metrics(self) -> List[MetricResult]:
        """
        Fetch and normalize all daily metrics
        
        Convenience method for daily metrics only
        
        Returns:
            List of MetricResult objects for daily metrics
        """
        return self.fetch_all_metrics('daily')
    
    def fetch_metric_by_id(self, metric_id: str) -> Optional[MetricResult]:
        """
        Fetch and normalize a single metric by ID
        
        Args:
            metric_id: Metric identifier (e.g., "daily_01_total_open_interest")
        
        Returns:
            MetricResult if metric found, None otherwise
        """
        # Search for metric in registry
        for metrics in PANEL_REGISTRY.values():
            for metric in metrics:
                if metric.id == metric_id:
                    return self.fetch_and_normalize(metric)
        
        return None


# ============================================================================
# BATCH ORCHESTRATOR (ALL TIMEFRAMES)
# ============================================================================

class BatchOrchestrator:
    """
    Orchestrates fetching all metrics across all timeframes
    
    This is the high-level interface for getting a complete panel snapshot
    """
    
    def __init__(self, api_client: CoinGlassAPI):
        """
        Initialize batch orchestrator
        
        INJECTION PATTERN: Accepts CoinGlassAPI instance for better testability
        
        Args:
            api_client: CoinGlassAPI instance (real or mock)
        """
        self.orchestrator = MetricOrchestrator(api_client)
    
    def fetch_all(self) -> Dict[str, List[MetricResult]]:
        """
        Fetch all metrics across all timeframes
        
        Returns:
            Dict with timeframes as keys, lists of MetricResult as values:
            {
                'daily': [MetricResult, ...],
                'weekly': [MetricResult, ...],
                'monthly': [MetricResult, ...]
            }
        """
        return {
            'daily': self.orchestrator.fetch_all_metrics('daily'),
            'weekly': self.orchestrator.fetch_all_metrics('weekly'),
            'monthly': self.orchestrator.fetch_all_metrics('monthly')
        }
    
    def fetch_implemented_only(self) -> List[MetricResult]:
        """
        Fetch only implemented metrics (currently daily metrics only)
        
        Returns:
            List of MetricResult objects for implemented metrics
        """
        implemented_metrics = get_all_implemented_metrics()
        results = []
        
        for metric in implemented_metrics:
            result = self.orchestrator.fetch_and_normalize(metric)
            results.append(result)
        
        return results


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_status_summary(results: List[MetricResult]) -> Dict[str, int]:
    """
    Get summary statistics for metric results
    
    Args:
        results: List of MetricResult objects
    
    Returns:
        Dict with status counts:
        {
            'total': int,
            'ok': int,
            'missing': int,
            'locked': int,
            'external_required': int
        }
    """
    summary = {
        'total': len(results),
        'ok': 0,
        'missing': 0,
        'locked': 0,
        'external_required': 0
    }
    
    for result in results:
        if result.status == MetricStatus.OK:
            summary['ok'] += 1
        elif result.status == MetricStatus.MISSING:
            summary['missing'] += 1
        elif result.status == MetricStatus.LOCKED:
            summary['locked'] += 1
        elif result.status == MetricStatus.EXTERNAL_REQUIRED:
            summary['external_required'] += 1
    
    return summary


def filter_by_status(results: List[MetricResult], status: MetricStatus) -> List[MetricResult]:
    """
    Filter results by status
    
    Args:
        results: List of MetricResult objects
        status: MetricStatus to filter by
    
    Returns:
        List of MetricResult objects with matching status
    """
    return [r for r in results if r.status == status]
