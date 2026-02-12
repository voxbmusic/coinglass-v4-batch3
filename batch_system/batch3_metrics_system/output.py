def _format_funding_regime_line(v: dict) -> str:
    regime = v.get("regime", "N/A")
    last_pct = v.get("last_pct", "N/A")
    mean_pct = v.get("mean_pct", "N/A")
    stdev_pct = v.get("stdev_pct", "N/A")
    pos_ratio = v.get("pos_ratio", "N/A")
    ann = v.get("ann_carry_pct", "N/A")
    flips = v.get("flips", "N/A")
    z = v.get("z_last", "N/A")
    slope = v.get("slope_pct_per_bar", "N/A")
    cum = v.get("cum_30_pct", "N/A")
    hint = v.get("squeeze_risk_hint", None)
    tail = "" if (hint in (None, "N/A", "")) else f" | hint={hint}"
    return f"{regime} | last={last_pct}% | mean={mean_pct}% | stdev={stdev_pct} | pos={pos_ratio} | ann={ann}% | flips={flips} | z={z} | slope={slope} | cum30={cum}%{tail}"


"""
Output Formatter - Batch 3
JSON Contract v1 builder and text formatter for metric results

JSON SCHEMA V1 (CONTRACT-LOCKED):
{
    "id": str,              # required - metric identifier
    "name": str,            # required - display name
    "timeframe": str,       # required - canonical timeframe
    "category": str,        # required - canonical category
    "status": str,          # required - ok/missing/locked/external_required
    "unit": str,            # required - display unit
    "value": Any | None,    # required - normalized value (can be None)
    "source": str,          # optional - data source
    "notes": str            # optional - additional notes
}

CRITICAL RULES:
- Weekly/monthly metrics: value=None but status MUST be visible
- Status is always present regardless of value
- Keys are contract-stable (do not change)
- JSON-serializable only (no NaN, no inf)
"""

from typing import Dict, Any, List, Optional
from batch3_metrics_system.metric_registry import PANEL_REGISTRY, MetricDefinition
from batch3_metrics_system.orchestrator import MetricResult
from batch3_metrics_system.metric_definitions import MetricStatus
import json
import math


# ============================================================================
# JSON CONTRACT V1 BUILDER
# ============================================================================

class JSONContractBuilder:
    """
    Build JSON Contract v1 output from metric results
    
    Contract schema is LOCKED - do not modify without version bump
    """
    
    @staticmethod
    def sanitize_value(value: Any) -> Any:
        """
        Sanitize value for JSON safety (NaN/inf → None)
        
        CRITICAL: API may return corrupt data (NaN/inf) which breaks JSON serialization
        or causes downstream misinterpretation. This function ensures JSON-safe values.
        
        Args:
            value: Value to sanitize (float | dict | list | None | other)
        
        Returns:
            Sanitized value (NaN/inf replaced with None)
        """
        if value is None:
            return None
        
        # Float: check for NaN/inf
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
            return value
        
        # Dict: recursively sanitize values
        elif isinstance(value, dict):
            if unit == "funding_regime":
                return "Funding Regime: " + _format_funding_regime_line(value)
            return {k: JSONContractBuilder.sanitize_value(v) for k, v in value.items()}
        
        # List: recursively sanitize items
        elif isinstance(value, list):
            return [JSONContractBuilder.sanitize_value(item) for item in value]
        
        # Other types: return as-is
        else:
            return value
    
    @staticmethod
    def build_metric_item(
        metric: MetricDefinition,
        result: MetricResult
    ) -> Dict[str, Any]:
        """
        Build a single metric item conforming to JSON Contract v1
        
        Args:
            metric: MetricDefinition from registry
            result: MetricResult from orchestrator
        
        Returns:
            Dict conforming to JSON Contract v1 schema
        """
        # Required fields (always present)
        item = {
            "id": metric.id,
            "name": metric.name,
            "timeframe": metric.timeframe,
            "category": metric.category,
            "status": result.status.value,
            "unit": metric.unit,
            "value": JSONContractBuilder.sanitize_value(result.value)  # JSON-safe (NaN/inf → None)
        }
        
        # Optional fields (add if available)
        if metric.data_source:
            item["source"] = metric.data_source.value
        
        # Add notes for non-OK statuses or if error present
        notes = []
        if result.error:
            notes.append(result.error)
        if result.status == MetricStatus.LOCKED:
            notes.append(f"Requires {metric.min_plan.value} plan or higher")
        if result.status == MetricStatus.EXTERNAL_REQUIRED:
            notes.append(metric.implementation_notes or "Requires external data source")
        
        if notes:
            item["notes"] = " | ".join(notes)
        
        return item
    
    @staticmethod
    def build_timeframe_output(
        timeframe: str,
        results: List[MetricResult]
    ) -> List[Dict[str, Any]]:
        """
        Build output for all metrics in a timeframe
        
        Args:
            timeframe: 'daily', 'weekly', or 'monthly'
            results: List of MetricResult objects
        
        Returns:
            List of metric items conforming to JSON Contract v1
        """
        metrics = PANEL_REGISTRY.get(timeframe, [])
        output = []
        
        # Create a map of metric_id -> result for fast lookup
        result_map = {r.metric_id: r for r in results}
        
        # Build items in registry order (preserves display order)
        for metric in metrics:
            result = result_map.get(metric.id)
            if result:
                item = JSONContractBuilder.build_metric_item(metric, result)
                output.append(item)
        
        return output
    
    @staticmethod
    def build_full_output(
        all_results: Dict[str, List[MetricResult]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build complete JSON Contract v1 output for all timeframes
        
        Args:
            all_results: Dict with timeframes as keys, lists of MetricResult as values
                        (from BatchOrchestrator.fetch_all())
        
        Returns:
            Dict conforming to JSON Contract v1:
            {
                "daily": [metric_item, ...],
                "weekly": [metric_item, ...],
                "monthly": [metric_item, ...]
            }
        """
        output = {}
        
        for timeframe in ['daily', 'weekly', 'monthly']:
            results = all_results.get(timeframe, [])
            output[timeframe] = JSONContractBuilder.build_timeframe_output(timeframe, results)
        
        return output
    
    @staticmethod
    def to_json_string(
        output: Dict[str, Any],
        pretty: bool = True
    ) -> str:
        """
        Convert output dict to JSON string
        
        Args:
            output: Dict conforming to JSON Contract v1
            pretty: If True, pretty-print with indentation
        
        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(output, indent=2, ensure_ascii=False)
        else:
            return json.dumps(output, ensure_ascii=False)


# ============================================================================
# TEXT FORMATTER (TERMINAL/DEBUG)
# ============================================================================
def _format_funding_regime_line(v: dict) -> str:
    regime = v.get("regime", "N/A")
    last_pct = v.get("last_pct", "N/A")
    mean_pct = v.get("mean_pct", "N/A")
    stdev_pct = v.get("stdev_pct", "N/A")
    pos_ratio = v.get("pos_ratio", "N/A")
    ann = v.get("ann_carry_pct", "N/A")
    flips = v.get("flips", "N/A")
    z = v.get("z_last", "N/A")
    slope = v.get("slope_pct_per_bar", "N/A")
    cum = v.get("cum_30_pct", "N/A")
    cs = v.get("crowding_score", "N/A")
    ss = v.get("squeeze_score", "N/A")
    ch = v.get("chop_score", "N/A")
    hint = v.get("squeeze_risk_hint", None)
    tail = "" if (hint in (None, "N/A", "")) else f" | hint={hint}"
    return (
        f"{regime}"
        f" | last8h={last_pct}%"
        f" | mean8h={mean_pct}%"
        f" | stdev8h={stdev_pct}"
        f" | pos={pos_ratio}"
        f" | annCarry={ann}%"
        f" | flips30={flips}"
        f" | z={z}"
        f" | slope={slope}"
        f" | cum30={cum}%"
        f" | crowd={cs}"
        f" | squeeze={ss}"
        f" | chop={ch}"
        f"{tail}"
    )


class TextFormatter:
    """
    Format metric results as human-readable text
    
    Useful for terminal output, logs, and debugging
    """
    
    # Status symbols for visual feedback
    STATUS_SYMBOLS = {
        MetricStatus.OK: "✅",
        MetricStatus.MISSING: "❌",
        MetricStatus.LOCKED: "🔒",
        MetricStatus.EXTERNAL_REQUIRED: "🔗"
    }
    @staticmethod
    def format_value(value: Any, unit: str) -> str:
        """
        Format a metric value with its unit

        Args:
            value: Normalized value (float | dict | list | None)
            unit: Display unit

        Returns:
            Formatted string
        """
        if value is None:
            return "N/A"

        if isinstance(value, (int, float)):
            if unit == "percent":
                return f"{value:+.2f}%"
            elif unit == "billion_usd":
                return f"${value:.2f}B"
            elif unit == "million_usd":
                return f"${value:.2f}M"
            elif unit == "ratio":
                return f"{value:.3f}"
            else:
                return f"{value:.4f}"

        elif isinstance(value, dict):
            if unit == "funding_regime":
                return "Funding Regime: " + _format_funding_regime_line(value)
            parts = []
            for k, v in value.items():
                if v is None:
                    parts.append(f"{k}=N/A")
                elif isinstance(v, float):
                    parts.append(f"{k}={v:.2f}")
                else:
                    parts.append(f"{k}={v}")
            return "{" + ", ".join(parts) + "}"

        elif isinstance(value, list):
            return f"[{len(value)} items]"

        else:
            return str(value)

    
    @staticmethod
    def format_metric(
        metric: MetricDefinition,
        result: MetricResult,
        verbose: bool = False
    ) -> str:
        """
        Format a single metric result as text
        
        Args:
            metric: MetricDefinition from registry
            result: MetricResult from orchestrator
            verbose: If True, include additional details
        
        Returns:
            Formatted string
        """
        symbol = TextFormatter.STATUS_SYMBOLS.get(result.status, "❓")
        value_str = TextFormatter.format_value(result.value, metric.unit)
        
        # Basic format: [symbol] name: value (status)
        output = f"{symbol} {metric.name}: {value_str}"
        
        if verbose:
            output += f" [{result.status.value.upper()}]"
            if result.error:
                output += f" - {result.error}"
        
        return output
    
    @staticmethod
    def format_timeframe(
        timeframe: str,
        results: List[MetricResult],
        verbose: bool = False
    ) -> str:
        """
        Format all metrics in a timeframe as text
        
        Args:
            timeframe: 'daily', 'weekly', or 'monthly'
            results: List of MetricResult objects
            verbose: If True, include additional details
        
        Returns:
            Formatted multi-line string
        """
        metrics = PANEL_REGISTRY.get(timeframe, [])
        result_map = {r.metric_id: r for r in results}
        
        lines = []
        lines.append(f"\n{'=' * 70}")
        lines.append(f"{timeframe.upper()} METRICS")
        lines.append(f"{'=' * 70}")
        
        for metric in metrics:
            result = result_map.get(metric.id)
            if result:
                line = TextFormatter.format_metric(metric, result, verbose)
                lines.append(line)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_full_output(
        all_results: Dict[str, List[MetricResult]],
        verbose: bool = False
    ) -> str:
        """
        Format complete output for all timeframes as text
        
        Args:
            all_results: Dict with timeframes as keys, lists of MetricResult as values
            verbose: If True, include additional details
        
        Returns:
            Formatted multi-line string
        """
        lines = []
        
        for timeframe in ['daily', 'weekly', 'monthly']:
            results = all_results.get(timeframe, [])
            lines.append(TextFormatter.format_timeframe(timeframe, results, verbose))
        
        # Add summary
        total_results = sum(len(results) for results in all_results.values())
        ok_count = sum(1 for results in all_results.values() for r in results if r.status == MetricStatus.OK)
        
        lines.append(f"\n{'=' * 70}")
        lines.append(f"SUMMARY: {ok_count}/{total_results} metrics OK")
        lines.append(f"{'=' * 70}")
        
        return "\n".join(lines)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def output_to_json(
    all_results: Dict[str, List[MetricResult]],
    filepath: Optional[str] = None,
    pretty: bool = True
) -> str:
    """
    Convert results to JSON Contract v1 format
    
    Args:
        all_results: Dict with timeframes as keys, lists of MetricResult as values
        filepath: If provided, write JSON to file
        pretty: If True, pretty-print JSON
    
    Returns:
        JSON string
    """
    output = JSONContractBuilder.build_full_output(all_results)
    json_str = JSONContractBuilder.to_json_string(output, pretty=pretty)
    
    if filepath:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    return json_str


def output_to_text(
    all_results: Dict[str, List[MetricResult]],
    filepath: Optional[str] = None,
    verbose: bool = False
) -> str:
    """
    Convert results to human-readable text format
    
    Args:
        all_results: Dict with timeframes as keys, lists of MetricResult as values
        filepath: If provided, write text to file
        verbose: If True, include additional details
    
    Returns:
        Formatted text string
    """
    text_str = TextFormatter.format_full_output(all_results, verbose=verbose)
    
    if filepath:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_str)
    
    return text_str


def output_daily_only_json(
    daily_results: List[MetricResult],
    filepath: Optional[str] = None,
    pretty: bool = True
) -> str:
    """
    Convert daily results to JSON Contract v1 format
    
    Convenience function for daily-only output
    
    Args:
        daily_results: List of MetricResult objects for daily metrics
        filepath: If provided, write JSON to file
        pretty: If True, pretty-print JSON
    
    Returns:
        JSON string
    """
    output = JSONContractBuilder.build_timeframe_output('daily', daily_results)
    json_str = json.dumps({"daily": output}, indent=2 if pretty else None, ensure_ascii=False)
    
    if filepath:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    return json_str


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def validate_json_contract(output: Dict[str, Any]) -> bool:
    """
    Validate that output conforms to JSON Contract v1 schema
    
    Args:
        output: Dict to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_timeframes = ['daily', 'weekly', 'monthly']
    required_fields = ['id', 'name', 'timeframe', 'category', 'status', 'unit', 'value']
    
    # Check top-level structure
    if not isinstance(output, dict):
        return False
    
    for timeframe in required_timeframes:
        if timeframe not in output:
            return False
        
        if not isinstance(output[timeframe], list):
            return False
        
        # Check each metric item
        for item in output[timeframe]:
            if not isinstance(item, dict):
                return False
            
            # Check required fields
            for field in required_fields:
                if field not in item:
                    return False
    
    return True
