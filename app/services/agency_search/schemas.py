"""Schemas for Agency Search and Ranking."""

from pydantic import BaseModel, Field
from datetime import datetime


class AgencySearchRequest(BaseModel):
    """Request for agency search."""

    publisher_domain: str = Field(..., description="Publisher domain to analyze")
    min_quality_score: int = Field(default=50, ge=0, le=100, description="Minimum quality threshold")


class AgencyMatch(BaseModel):
    """Individual agency match result."""

    agency_name: str = Field(..., description="Agency name from sellers.json")
    seller_id: str = Field(..., description="Seller ID in ads.txt")
    seller_domain: str = Field(..., description="Agency domain")
    relationship: str = Field(..., description="DIRECT or RESELLER")

    # Quality metrics
    quality_score: int = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    market_presence_score: int = Field(..., ge=0, le=100, description="Market reach and adoption")
    transparency_score: int = Field(..., ge=0, le=100, description="Transparency and compliance")
    tech_sophistication_score: int = Field(..., ge=0, le=100, description="Technology capabilities")

    # Ranking factors
    total_publishers_represented: int = Field(..., description="Number of publishers using this agency")
    has_sellers_json: bool = Field(..., description="Whether sellers.json exists")
    certification_authority_id: str | None = Field(None, description="TAG certification ID")
    supports_s2s: bool = Field(default=False, description="Server-side integration support")
    header_bidding_capable: bool = Field(default=False, description="Header bidding support")

    # Opportunity indicators
    opportunity_score: int = Field(..., ge=0, le=100, description="Opportunity for improvement")
    recommended_action: str | None = Field(None, description="Recommended next step")

    # Metadata
    detected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgencySearchReport(BaseModel):
    """Complete agency search report."""

    publisher_domain: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    total_agencies_found: int
    direct_relationships: int
    reseller_relationships: int

    # Agency matches ranked by quality
    agencies: list[AgencyMatch]

    # Opportunities
    top_opportunities: list[AgencyMatch] = Field(
        default_factory=list,
        description="Top 3 agencies by opportunity score"
    )

    # Analysis
    overall_agency_quality: int = Field(..., ge=0, le=100, description="Average quality across all agencies")
    has_premium_agencies: bool = Field(..., description="Whether any top-tier agencies detected")
    diversification_score: int = Field(..., ge=0, le=100, description="Agency portfolio diversity")

    recommendations: list[str] = Field(default_factory=list)


class AgencyRankingCriteria(BaseModel):
    """Criteria for ranking agencies."""

    # Market presence indicators
    min_publisher_count: int = Field(default=10, description="Minimum publisher representation")

    # Transparency requirements
    require_sellers_json: bool = Field(default=True)
    require_certification: bool = Field(default=False)

    # Technology capabilities
    prefer_s2s_capable: bool = Field(default=True)
    prefer_header_bidding: bool = Field(default=True)

    # Scoring weights
    market_presence_weight: float = Field(default=0.3, ge=0, le=1)
    transparency_weight: float = Field(default=0.3, ge=0, le=1)
    tech_sophistication_weight: float = Field(default=0.4, ge=0, le=1)
