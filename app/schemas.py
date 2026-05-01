"""Pydantic models for API requests and responses."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ScanRequest(BaseModel):
    """Single domain scan request."""

    domain: str = Field(..., description="Domain to scan (e.g., example.com)")

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, v: str) -> str:
        """Remove protocol and trailing slashes."""
        v = v.lower().strip()
        v = v.replace("https://", "").replace("http://", "")
        v = v.replace("www.", "")
        v = v.rstrip("/")
        return v


class BatchScanRequest(BaseModel):
    """Batch domain scan request."""

    domains: list[str] = Field(..., min_length=1, max_length=50)


class Vulnerability(BaseModel):
    """Security vulnerability finding."""

    type: str = Field(..., description="Vulnerability type")
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    details: str = Field(..., description="Human-readable details")


class MonetizationGap(BaseModel):
    """Revenue monetization opportunity."""

    type: str = Field(..., description="Gap type")
    details: str = Field(..., description="Description of the gap")
    opportunity: str | None = Field(None, description="Recommended action")


class ScanReport(BaseModel):
    """Complete scan report for a publisher."""

    publisher_id: str = Field(..., description="Normalized domain identifier")
    domain: str = Field(..., description="Original scanned domain")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ads_txt_verified: bool = Field(..., description="Whether ads.txt is valid")
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    monetization_gaps: list[MonetizationGap] = Field(default_factory=list)
    estimated_signal_recovery_pct: int = Field(
        ..., ge=0, le=100, description="Estimated signal recovery percentage"
    )
    scan_duration_ms: int | None = Field(None, description="Scan duration in milliseconds")
    error: str | None = Field(None, description="Error message if scan failed")


class BatchScanResponse(BaseModel):
    """Response for batch scan request."""

    total: int
    successful: int
    failed: int
    reports: list[ScanReport]
