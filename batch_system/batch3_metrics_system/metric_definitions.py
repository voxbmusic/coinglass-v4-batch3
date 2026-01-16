"""
Metric Definitions - Batch 3
Defines the structure for all panel metrics (daily/weekly/monthly)

CRITICAL RULES:
- Metric IDs are CONTRACT-STABLE: Never change once defined
- Metric names can change (display only)
- JSON output, tests, and all downstream systems lock onto IDs
- Timeframes must use canonical values: snapshot, 1h, 4h, 8h, 24h, 7d, 30d
- ID format: {timeframe}_{number:02d}_{stable_slug} (e.g., daily_01_total_open_interest)
- ALWAYS use helper functions (create_daily_metric, create_registry_metric) to create metrics

PARAMS STANDARD (CONTRACT):
- interval: always STRING ("1h", "4h", "8h")
- limit: always STRING ("1", "2", "30")
- symbol: always "BTC" (standard ticker)

CATEGORY STANDARD (CONTRACT):
- Canonical categories: open_interest, funding, long_short, liquidations, premium
- These are used for UI grouping and output contract
- Not Enum in Batch 3, but must use these exact values
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
import re
import warnings


# Canonical timeframe values (will become Enum in future)
# Note: For time series (e.g., "8h candles"), use base timeframe (e.g., "8h") 
# and specify bars/series details in params or metadata
CANONICAL_TIMEFRAMES = ['snapshot', '1h', '4h', '8h', '24h', '7d', '30d']

# Canonical categories (not Enum in Batch 3, but contract-stable)
CANONICAL_CATEGORIES = ['open_interest', 'funding', 'long_short', 'liquidations', 'premium']


class MetricStatus(Enum):
    """
    Standardized metric status values
    
    Note: Future consideration - ERROR status for permanent failures vs MISSING for temporary issues
    """
    OK = "ok"                              # Successfully fetched and normalized
    LOCKED = "locked"                      # Plan restriction (upgrade required)
    EXTERNAL_REQUIRED = "external_required" # Not in CoinGlass (external source needed)
    MISSING = "missing"                    # Temporary technical failure or not implemented


class DataSource(Enum):
    """Data source types"""
    COINGLASS = "coinglass"    # Available in CoinGlass API
    EXTERNAL = "external"      # Requires external API
    COMPUTED = "computed"      # Derived/calculated metric


class PlanTier(Enum):
    """
    Plan tier requirements
    
    Note: STANDARD includes Standard/Standard+ mapping (to be finalized with actual CoinGlass plan names)
    """
    STARTUP = "startup"        # Startup tier (paid plan)
    STANDARD = "standard"      # Standard/Standard+ tier
    PREMIUM = "premium"        # Premium tier


class APIConfidence(Enum):
    """API endpoint confidence level"""
    CONFIRMED = "confirmed"    # Smoke tested or previously verified
    UNVERIFIED = "unverified"  # Not yet tested


# ID format validation regex patterns
# Stricter rules: no double underscores, no trailing underscore
DAILY_ID_PATTERN = re.compile(r'^daily_\d{2}_[a-z0-9]+(_[a-z0-9]+)*$')
WEEKLY_ID_PATTERN = re.compile(r'^weekly_\d{2}_[a-z0-9]+(_[a-z0-9]+)*$')
MONTHLY_ID_PATTERN = re.compile(r'^monthly_\d{2}_[a-z0-9]+(_[a-z0-9]+)*$')


@dataclass
class MetricDefinition:
    """
    Complete metric definition for panel registry
    
    WARNING: Do NOT instantiate directly - always use helper functions:
    - create_daily_metric() for daily metrics
    - create_registry_metric() for weekly/monthly metrics
    
    Attributes:
        id: Unique identifier - IMMUTABLE, CONTRACT-STABLE
            Format: "{timeframe}_{number:02d}_{stable_slug}"
            Example: "daily_01_total_open_interest"
            RULE: ID never changes once defined, even if name changes
            RULE: Slug does NOT contain timeframe suffix (e.g., "_7d")
        
        name: Display name - MUTABLE
            Can be changed for UI improvements
            Example: "Total Open Interest"
        
        timeframe: Time period - USE CANONICAL VALUES ONLY
            Allowed: snapshot, 1h, 4h, 8h, 24h, 7d, 30d
            Note: For time series (e.g., "8h candles"), use timeframe="8h" 
                  and specify bars/series info in metadata
            (Future: Will become Enum)
        
        category: Metric category - USE CANONICAL VALUES ONLY
            Allowed: open_interest, funding, long_short, liquidations, premium
            (Future: Will become Enum)
        
        # API Configuration
        endpoint: CoinGlass API endpoint (None if not implemented)
        params: Default parameters for API call (None is safe - normalize_params in Batch 2 handles this)
                STANDARD: interval="STRING", limit="STRING", symbol="BTC"
                Note: Some endpoints may not require params - this is guideline, not hard requirement
        api_confidence: Whether endpoint is confirmed working
        
        # Status Configuration
        default_status: Expected status if not implemented
        data_source: Where data comes from
        
        # Plan Configuration
        min_plan: Minimum plan tier required
        
        # Implementation Status
        implemented: Whether metric is implemented in current batch
        normalizer: Normalization function name (None if not implemented)
        
        # Metadata
        unit: Display unit (e.g., "billion_usd", "percent")
        description: Human-readable description
        implementation_notes: Technical notes for implementation
    """
    
    # Core identification
    id: str                    # IMMUTABLE - contract stable
    name: str                  # MUTABLE - display only
    timeframe: str             # CANONICAL VALUES ONLY
    category: str              # CANONICAL VALUES ONLY
    
    # API configuration
    endpoint: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    api_confidence: APIConfidence = APIConfidence.UNVERIFIED
    
    # Status configuration
    default_status: MetricStatus = MetricStatus.MISSING  # Safe default for undefined metrics
    data_source: DataSource = DataSource.COINGLASS
    
    # Plan configuration
    min_plan: PlanTier = PlanTier.STARTUP
    
    # Implementation status
    implemented: bool = False
    normalizer: Optional[str] = None
    
    # Metadata
    unit: str = ""
    description: str = ""
    implementation_notes: str = ""
    
    def __post_init__(self):
        """
        Validate fields after initialization
        
        This provides a safety net even if someone bypasses helper functions
        
        Note: params validation is intentionally NOT strict here - normalize_params
        in Batch 2 handles parameter standardization. Some endpoints may not require params.
        """
        # Validate timeframe against canonical list
        if self.timeframe not in CANONICAL_TIMEFRAMES:
            raise ValueError(
                f"Invalid timeframe '{self.timeframe}'. "
                f"Must be one of: {CANONICAL_TIMEFRAMES}"
            )
        
        # Validate category (soft check for now - will be stricter in future)
        # Note: Future enhancement - make this strict once all metrics are reviewed
        if self.category not in CANONICAL_CATEGORIES:
            warnings.warn(
                f"Non-canonical category '{self.category}'. "
                f"Recommended categories: {CANONICAL_CATEGORIES}",
                category=UserWarning,
                stacklevel=2
            )
        
        # Validate ID format
        if self.id.startswith('daily_'):
            if not DAILY_ID_PATTERN.match(self.id):
                raise ValueError(
                    f"Invalid daily metric ID format: '{self.id}'. "
                    f"Must match pattern: daily_XX_slug (e.g., 'daily_01_total_open_interest')"
                )
        elif self.id.startswith('weekly_'):
            if not WEEKLY_ID_PATTERN.match(self.id):
                raise ValueError(
                    f"Invalid weekly metric ID format: '{self.id}'. "
                    f"Must match pattern: weekly_XX_slug (e.g., 'weekly_01_cme_long_short')"
                )
        elif self.id.startswith('monthly_'):
            if not MONTHLY_ID_PATTERN.match(self.id):
                raise ValueError(
                    f"Invalid monthly metric ID format: '{self.id}'. "
                    f"Must match pattern: monthly_XX_slug (e.g., 'monthly_01_mvrv_ratio')"
                )
        else:
            raise ValueError(
                f"Invalid metric ID prefix: '{self.id}'. "
                f"Must start with 'daily_', 'weekly_', or 'monthly_'"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'name': self.name,
            'timeframe': self.timeframe,
            'category': self.category,
            'endpoint': self.endpoint,
            'params': self.params,
            'api_confidence': self.api_confidence.value,
            'default_status': self.default_status.value,
            'data_source': self.data_source.value,
            'min_plan': self.min_plan.value,
            'implemented': self.implemented,
            'normalizer': self.normalizer,
            'unit': self.unit,
            'description': self.description,
            'implementation_notes': self.implementation_notes
        }


# Helper functions for creating metric definitions

def create_daily_metric(
    daily_id: str,             # REQUIRED: Manually specified, stable ID
    name: str,
    timeframe: str,
    category: str,
    endpoint: str,
    params: Dict[str, Any],
    api_confidence: APIConfidence,
    normalizer: str,
    unit: str,
    description: str,
    implementation_notes: str = ""
) -> MetricDefinition:
    """
    Helper to create a daily metric definition (fully implemented)
    
    CRITICAL RULES:
    - daily_id is MANUALLY specified and IMMUTABLE
    - NEVER derive ID from name (name can change, ID cannot)
    - Format: "daily_{number:02d}_{stable_slug}" (e.g., "daily_01_total_open_interest")
    - Slug does NOT contain timeframe suffix (e.g., NO "_7d" or "_30d")
    - This ID is used in JSON contract, tests, and all downstream systems
    
    All daily metrics are:
    - implemented=True (Batch 3)
    - default_status=OK
    - data_source=COINGLASS
    - min_plan=STARTUP
    
    Args:
        daily_id: Contract-stable identifier (e.g., "daily_01_total_open_interest")
                  DO NOT derive from name - specify manually
                  Format: daily_{XX}_{stable_slug} where XX is 01-99
                  Slug rules: lowercase, alphanumeric + underscore, no double/trailing underscores
                  NO timeframe suffix in slug (e.g., no "_7d")
        name: Display name (can change)
        timeframe: Canonical timeframe (snapshot, 1h, 4h, 8h, 24h, 7d, 30d)
                   For time series, use base timeframe (e.g., "8h" not "8h_candles")
        category: Metric category (use canonical: open_interest, funding, long_short, liquidations, premium)
        endpoint: CoinGlass API endpoint
        params: API parameters - STANDARD: interval="STRING", limit="STRING", symbol="BTC"
                Note: Some endpoints may not require all params - this is guideline
        api_confidence: CONFIRMED or UNVERIFIED
        normalizer: Normalization function name
        unit: Display unit
        description: Human-readable description
        implementation_notes: Technical notes
    
    Returns:
        MetricDefinition with implemented=True
    
    Raises:
        ValueError: If ID format is invalid or timeframe is not canonical
    """
    # Validation happens in __post_init__, but we can do early check here too
    if not DAILY_ID_PATTERN.match(daily_id):
        raise ValueError(
            f"Invalid daily metric ID format: '{daily_id}'. "
            f"Must match pattern: daily_XX_slug (e.g., 'daily_01_total_open_interest'). "
            f"Rules: lowercase, alphanumeric + underscore, no double/trailing underscores, NO timeframe suffix"
        )
    
    return MetricDefinition(
        id=daily_id,
        name=name,
        timeframe=timeframe,
        category=category,
        endpoint=endpoint,
        params=params,
        api_confidence=api_confidence,
        default_status=MetricStatus.OK,
        data_source=DataSource.COINGLASS,
        min_plan=PlanTier.STARTUP,
        implemented=True,
        normalizer=normalizer,
        unit=unit,
        description=description,
        implementation_notes=implementation_notes
    )


def create_registry_metric(
    registry_id: str,          # REQUIRED: Manually specified, stable ID
    name: str,
    timeframe: str,
    category: str,
    data_source: DataSource,
    min_plan: PlanTier,
    unit: str,
    description: str,
    implementation_notes: str
) -> MetricDefinition:
    """
    Helper to create a registry-only metric (weekly/monthly)
    
    CRITICAL RULES:
    - registry_id is MANUALLY specified and IMMUTABLE
    - Format: "{timeframe}_{number:02d}_{stable_slug}" 
              (e.g., "weekly_01_cme_long_short" or "monthly_01_mvrv_ratio")
    - Slug does NOT contain timeframe suffix (e.g., NO "_7d" or "_30d")
    - NEVER derive ID from name
    
    Registry metrics are:
    - implemented=False (Batch 3: display only)
    - endpoint=None
    - normalizer=None
    - default_status determined by plan tier FIRST, then data source
    
    STATUS PRIORITY:
    1. If min_plan != STARTUP → LOCKED (plan restriction takes precedence)
    2. Else if data_source is EXTERNAL or COMPUTED → EXTERNAL_REQUIRED
    3. Else → EXTERNAL_REQUIRED (safe default)
    
    TIMEFRAME CONVENTION:
    - Weekly metrics: typically use timeframe="7d"
    - Monthly metrics: typically use timeframe="30d"
    - Other timeframes are allowed but may indicate misconfiguration (soft warning)
    
    SOFT VALIDATION WARNINGS:
    - Warnings are emitted for timeframe convention violations
    - Note: Future enhancement - these could be controlled by environment flag
          (e.g., METRICS_DEV_MODE=true) to reduce noise in production
    
    Args:
        registry_id: Contract-stable identifier (e.g., "weekly_01_cme_long_short")
                     Slug rules: lowercase, alphanumeric + underscore, no double/trailing underscores
                     NO timeframe suffix in slug (e.g., no "_7d")
        name: Display name (can change)
        timeframe: Canonical timeframe (typically 7d for weekly, 30d for monthly,
                   but all canonical values are enforced by validator)
        category: Metric category (use canonical: open_interest, funding, long_short, liquidations, premium)
        data_source: COINGLASS, EXTERNAL, or COMPUTED
        min_plan: STARTUP, STANDARD, or PREMIUM
        unit: Display unit
        description: Human-readable description
        implementation_notes: Technical notes
    
    Returns:
        MetricDefinition with implemented=False
    
    Raises:
        ValueError: If ID format is invalid or timeframe is not canonical
    """
    # Validate ID format
    if not (WEEKLY_ID_PATTERN.match(registry_id) or MONTHLY_ID_PATTERN.match(registry_id)):
        raise ValueError(
            f"Invalid registry metric ID format: '{registry_id}'. "
            f"Must match pattern: weekly_XX_slug or monthly_XX_slug. "
            f"Rules: lowercase, alphanumeric + underscore, no double/trailing underscores, NO timeframe suffix"
        )
    
    # Soft validation: check timeframe convention
    # Note: Future enhancement - could be controlled by environment flag
    if registry_id.startswith('weekly_') and timeframe != '7d':
        warnings.warn(
            f"Weekly metric '{registry_id}' uses timeframe '{timeframe}' (typically '7d')",
            category=UserWarning,
            stacklevel=2
        )
    elif registry_id.startswith('monthly_') and timeframe != '30d':
        warnings.warn(
            f"Monthly metric '{registry_id}' uses timeframe '{timeframe}' (typically '30d')",
            category=UserWarning,
            stacklevel=2
        )
    
    # Determine default status - PLAN TIER TAKES PRECEDENCE
    if min_plan != PlanTier.STARTUP:
        # Plan restriction - user needs to upgrade
        default_status = MetricStatus.LOCKED
    elif data_source == DataSource.EXTERNAL or data_source == DataSource.COMPUTED:
        # Available in plan but requires external source or computation
        default_status = MetricStatus.EXTERNAL_REQUIRED
    else:
        # Safe default
        default_status = MetricStatus.EXTERNAL_REQUIRED
    
    return MetricDefinition(
        id=registry_id,
        name=name,
        timeframe=timeframe,
        category=category,
        endpoint=None,
        params=None,
        api_confidence=APIConfidence.UNVERIFIED,
        default_status=default_status,
        data_source=data_source,
        min_plan=min_plan,
        implemented=False,
        normalizer=None,
        unit=unit,
        description=description,
        implementation_notes=implementation_notes
    )
