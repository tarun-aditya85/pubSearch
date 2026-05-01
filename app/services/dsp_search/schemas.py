"""Schemas for DSP Search and Ranking."""

from pydantic import BaseModel, Field
from datetime import datetime


class DSPSearchRequest(BaseModel):
    """Request for DSP search."""

    publisher_domain: str = Field(..., description="Publisher domain to analyze")
    min_quality_score: int = Field(default=50, ge=0, le=100, description="Minimum quality threshold")
    category_filter: str | None = Field(None, description="Filter by category (video, display, native)")


class DSPMatch(BaseModel):
    """Individual DSP match result."""

    dsp_name: str = Field(..., description="DSP name")
    dsp_domain: str = Field(..., description="DSP domain")
    seller_id: str | None = Field(None, description="Seller ID if present in ads.txt")
    relationship: str | None = Field(None, description="DIRECT or RESELLER")

    # Detection method
    detected_via: str = Field(..., description="How DSP was detected: ads.txt, network_request, prebid")

    # Quality metrics
    quality_score: int = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    market_share_score: int = Field(..., ge=0, le=100, description="Market share and adoption")
    performance_score: int = Field(..., ge=0, le=100, description="Historical performance metrics")
    reliability_score: int = Field(..., ge=0, le=100, description="Uptime and reliability")

    # DSP capabilities
    ad_formats: list[str] = Field(default_factory=list, description="Supported formats: display, video, native")
    pricing_model: str | None = Field(None, description="CPM, CPC, CPA, etc.")
    header_bidding_integration: bool = Field(default=False)
    deals_marketplace: bool = Field(default=False, description="Private marketplace support")
    brand_safety: bool = Field(default=False, description="Brand safety controls")

    # Market presence
    estimated_daily_requests: int | None = Field(None, description="Estimated bid requests per day")
    avg_bid_rate: float | None = Field(None, ge=0, le=100, description="Average bid response rate %")
    avg_win_rate: float | None = Field(None, ge=0, le=100, description="Average win rate %")

    # Opportunity indicators
    opportunity_score: int = Field(..., ge=0, le=100, description="Revenue opportunity score")
    estimated_revenue_uplift_pct: int | None = Field(None, description="Estimated revenue increase %")
    recommended_action: str | None = Field(None)

    # Integration status
    is_currently_integrated: bool = Field(..., description="Whether DSP is already integrated")
    integration_complexity: str = Field(..., description="easy, medium, hard")

    detected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class DSPSearchReport(BaseModel):
    """Complete DSP search report."""

    publisher_domain: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    total_dsps_found: int
    currently_integrated: int
    potential_additions: int

    # DSP matches ranked by quality
    dsps: list[DSPMatch]

    # Opportunities
    top_opportunities: list[DSPMatch] = Field(
        default_factory=list,
        description="Top 5 DSPs by opportunity score"
    )

    # Analysis
    overall_dsp_quality: int = Field(..., ge=0, le=100, description="Average quality of current DSPs")
    portfolio_diversification: int = Field(..., ge=0, le=100, description="DSP portfolio diversity")
    header_bidding_coverage: int = Field(..., ge=0, le=100, description="% of HB-capable DSPs")

    # Revenue estimation
    estimated_total_revenue_uplift_pct: int = Field(..., description="Total estimated revenue increase")

    recommendations: list[str] = Field(default_factory=list)

    # Category breakdown
    by_format: dict[str, int] = Field(
        default_factory=dict,
        description="DSP count by format: display, video, native"
    )


class DSPRankingCriteria(BaseModel):
    """Criteria for ranking DSPs."""

    # Quality thresholds
    min_quality_score: int = Field(default=60, ge=0, le=100)
    min_market_share_score: int = Field(default=50, ge=0, le=100)

    # Capabilities
    require_header_bidding: bool = Field(default=True)
    require_deals_marketplace: bool = Field(default=False)
    require_brand_safety: bool = Field(default=True)

    # Format preferences
    preferred_formats: list[str] = Field(
        default_factory=lambda: ["display", "video", "native"]
    )

    # Scoring weights
    quality_weight: float = Field(default=0.3, ge=0, le=1)
    performance_weight: float = Field(default=0.4, ge=0, le=1)
    opportunity_weight: float = Field(default=0.3, ge=0, le=1)
