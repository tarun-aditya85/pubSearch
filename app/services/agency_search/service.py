"""Agency search service integrating with crawler data."""

import logging
from typing import List, Dict
from app.services.crawler import CrawlerResult
from .ranker import AgencyRanker
from .schemas import AgencySearchReport, AgencyRankingCriteria

logger = logging.getLogger(__name__)


class AgencySearchService:
    """Service for discovering and ranking agencies."""

    def __init__(self):
        self.ranker = AgencyRanker()

    async def search_agencies(
        self,
        crawler_result: CrawlerResult,
        ads_txt_content: str | None,
        criteria: AgencyRankingCriteria | None = None,
    ) -> AgencySearchReport:
        """
        Search for agencies based on crawler data and ads.txt.

        Args:
            crawler_result: Data from crawler service
            ads_txt_content: Raw ads.txt content
            criteria: Custom ranking criteria

        Returns:
            AgencySearchReport with ranked agencies
        """
        logger.info(f"Starting agency search for {crawler_result.domain}")

        # Parse ads.txt
        ads_txt_entries = self._parse_ads_txt(ads_txt_content) if ads_txt_content else []

        # Extract agencies from ads.txt
        agencies = self._extract_agencies_from_ads_txt(ads_txt_entries)

        # Detect capabilities from network requests
        detected_capabilities = self._detect_capabilities_from_requests(
            crawler_result.requests, crawler_result.js_files
        )

        # Rank agencies
        if criteria:
            self.ranker = AgencyRanker(criteria)

        ranked_agencies = self.ranker.rank_agencies(
            agencies, ads_txt_entries, detected_capabilities
        )

        # Generate report
        report = self.ranker.generate_report(crawler_result.domain, ranked_agencies)

        logger.info(
            f"Agency search complete: {report.total_agencies_found} agencies found, "
            f"avg quality: {report.overall_agency_quality}"
        )

        return report

    def _parse_ads_txt(self, ads_txt_content: str) -> List[Dict]:
        """Parse ads.txt file into structured entries."""
        entries = []

        for line in ads_txt_content.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse entry: domain, seller_id, relationship, [cert_id]
            parts = [p.strip() for p in line.replace("\t", ",").split(",")]

            if len(parts) >= 3:
                entry = {
                    "domain": parts[0].lower(),
                    "seller_id": parts[1],
                    "relationship": parts[2].upper(),
                    "certification_id": parts[3] if len(parts) > 3 else None,
                }
                entries.append(entry)

        return entries

    def _extract_agencies_from_ads_txt(self, ads_txt_entries: List[Dict]) -> List[Dict]:
        """Extract unique agencies from ads.txt entries."""
        agencies_map = {}

        for entry in ads_txt_entries:
            domain = entry["domain"]

            if domain not in agencies_map:
                agencies_map[domain] = {
                    "domain": domain,
                    "seller_id": entry["seller_id"],
                    "name": self._infer_agency_name(domain),
                    "publisher_count": self._estimate_publisher_count(domain),
                    "has_sellers_json": self._check_sellers_json_existence(domain),
                }

        return list(agencies_map.values())

    def _infer_agency_name(self, domain: str) -> str:
        """Infer agency name from domain."""
        # Remove common TLDs and format
        name = domain.replace(".com", "").replace(".net", "").replace(".io", "")
        name = name.replace("-", " ").replace("project", "").strip().title()
        return name

    def _estimate_publisher_count(self, domain: str) -> int:
        """
        Estimate number of publishers using this agency.

        In production, this would query a sellers.json aggregator database.
        For MVP, use heuristics based on known agencies.
        """
        # Known large agencies (Tier 1)
        tier1_agencies = {
            "google.com": 50000,
            "rubiconproject.com": 10000,
            "openx.com": 5000,
            "pubmatic.com": 8000,
            "indexexchange.com": 6000,
            "appnexus.com": 12000,
        }

        if domain in tier1_agencies:
            return tier1_agencies[domain]

        # Medium agencies
        if "exchange" in domain or "ssp" in domain or "adtech" in domain:
            return 1000

        # Small/unknown
        return 50

    def _check_sellers_json_existence(self, domain: str) -> bool:
        """
        Check if agency has sellers.json file.

        In production, this would make HTTP request to:
        https://{domain}/sellers.json

        For MVP, assume Tier 1 agencies have it.
        """
        tier1_domains = [
            "google.com",
            "rubiconproject.com",
            "openx.com",
            "pubmatic.com",
            "indexexchange.com",
        ]

        return domain in tier1_domains

    def _detect_capabilities_from_requests(
        self, requests: List, js_files: List[str]
    ) -> Dict[str, Dict]:
        """
        Detect agency capabilities from network requests and JS.

        Capabilities detected:
        - S2S (server-side) integration
        - Header bidding support
        """
        capabilities = {}

        # Detect header bidding from Prebid.js
        has_prebid = any("prebid" in js.lower() or "pbjs" in js for js in js_files)

        # Extract domains from requests
        from app.core.utils import extract_domain_from_url

        for request in requests:
            domain = extract_domain_from_url(request.url)

            if domain not in capabilities:
                capabilities[domain] = {
                    "s2s_capable": False,
                    "hb_capable": False,
                }

            # S2S detection: requests to /openrtb or /auction endpoints
            if "/openrtb" in request.url or "/auction" in request.url:
                capabilities[domain]["s2s_capable"] = True

            # Header bidding detection
            if has_prebid and request.resource_type in ["xhr", "fetch"]:
                capabilities[domain]["hb_capable"] = True

        return capabilities
