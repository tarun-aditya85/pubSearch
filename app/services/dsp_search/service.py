"""DSP search service integrating with crawler data."""

import logging
from typing import List, Dict
from app.services.crawler import CrawlerResult
from app.core.utils import extract_domain_from_url
from .ranker import DSPRanker
from .schemas import DSPSearchReport, DSPRankingCriteria

logger = logging.getLogger(__name__)


class DSPSearchService:
    """Service for discovering and ranking DSPs."""

    # Known DSP domains for detection
    DSP_DOMAINS = {
        "google.com",
        "thetradedesk.com",
        "amazon-adsystem.com",
        "appnexus.com",
        "mediamath.com",
        "adform.com",
        "criteo.com",
        "beeswax.com",
        "stackadapt.com",
        "basis.net",
        "adobe.com",
        "verizonmedia.com",
        "xandr.com",
    }

    # SSP domains that also act as DSPs
    SSP_AS_DSP = {
        "rubiconproject.com",
        "pubmatic.com",
        "openx.com",
        "indexexchange.com",
        "sovrn.com",
    }

    def __init__(self):
        self.ranker = DSPRanker()

    async def search_dsps(
        self,
        crawler_result: CrawlerResult,
        ads_txt_content: str | None,
        criteria: DSPRankingCriteria | None = None,
    ) -> DSPSearchReport:
        """
        Search for DSPs based on crawler data and ads.txt.

        Args:
            crawler_result: Data from crawler service
            ads_txt_content: Raw ads.txt content
            criteria: Custom ranking criteria

        Returns:
            DSPSearchReport with ranked DSPs
        """
        logger.info(f"Starting DSP search for {crawler_result.domain}")

        # Parse ads.txt
        ads_txt_entries = self._parse_ads_txt(ads_txt_content) if ads_txt_content else []

        # Detect DSPs from multiple sources
        detected_dsps = self._detect_dsps_multi_source(
            crawler_result.requests,
            crawler_result.js_files,
            ads_txt_entries,
        )

        # Rank DSPs
        if criteria:
            self.ranker = DSPRanker(criteria)

        ranked_dsps = self.ranker.rank_dsps(
            detected_dsps,
            [{"url": r.url, "resource_type": r.resource_type} for r in crawler_result.requests],
            ads_txt_entries,
        )

        # Generate report
        report = self.ranker.generate_report(crawler_result.domain, ranked_dsps)

        logger.info(
            f"DSP search complete: {report.total_dsps_found} DSPs found, "
            f"{report.potential_additions} potential additions"
        )

        return report

    def _parse_ads_txt(self, ads_txt_content: str) -> List[Dict]:
        """Parse ads.txt file into structured entries."""
        entries = []

        for line in ads_txt_content.split("\n"):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = [p.strip() for p in line.replace("\t", ",").split(",")]

            if len(parts) >= 3:
                entry = {
                    "domain": parts[0].lower(),
                    "seller_id": parts[1],
                    "relationship": parts[2].upper(),
                }
                entries.append(entry)

        return entries

    def _detect_dsps_multi_source(
        self,
        requests: List,
        js_files: List[str],
        ads_txt_entries: List[Dict],
    ) -> List[Dict]:
        """
        Detect DSPs from multiple sources:
        1. ads.txt entries (declared integrations)
        2. Network requests (active DSP calls)
        3. Prebid.js config (header bidding DSPs)
        """
        dsps_map = {}

        # Source 1: ads.txt entries
        for entry in ads_txt_entries:
            domain = entry["domain"]

            if self._is_dsp_domain(domain):
                dsps_map[domain] = {
                    "domain": domain,
                    "detected_via": "ads.txt",
                    "seller_id": entry["seller_id"],
                    "relationship": entry["relationship"],
                }

        # Source 2: Network requests
        for request in requests:
            domain = extract_domain_from_url(request.url)

            if self._is_dsp_domain(domain) and domain not in dsps_map:
                dsps_map[domain] = {
                    "domain": domain,
                    "detected_via": "network_request",
                }

        # Source 3: Prebid.js config
        prebid_dsps = self._extract_prebid_bidders(js_files)
        for dsp_domain in prebid_dsps:
            if dsp_domain not in dsps_map:
                dsps_map[dsp_domain] = {
                    "domain": dsp_domain,
                    "detected_via": "prebid",
                }

        return list(dsps_map.values())

    def _is_dsp_domain(self, domain: str) -> bool:
        """Check if domain belongs to a known DSP."""
        # Check exact match
        if domain in self.DSP_DOMAINS or domain in self.SSP_AS_DSP:
            return True

        # Check partial match for subdomains
        for dsp_domain in self.DSP_DOMAINS | self.SSP_AS_DSP:
            if dsp_domain in domain:
                return True

        # Heuristic: domains with "dsp", "demand", "buy" in name
        if any(keyword in domain for keyword in ["dsp", "demand", "buy", "advertis"]):
            return True

        return False

    def _extract_prebid_bidders(self, js_files: List[str]) -> List[str]:
        """
        Extract DSP bidders from Prebid.js configuration.

        Prebid config typically looks like:
        pbjs.addAdUnits({
            bids: [{
                bidder: 'appnexus',
                params: {...}
            }]
        })
        """
        bidders = set()

        # Known Prebid bidder codes to domain mapping
        bidder_to_domain = {
            "appnexus": "appnexus.com",
            "rubicon": "rubiconproject.com",
            "pubmatic": "pubmatic.com",
            "openx": "openx.com",
            "ix": "indexexchange.com",
            "criteo": "criteo.com",
            "sovrn": "sovrn.com",
            "triplelift": "triplelift.com",
            "ttd": "thetradedesk.com",
            "amazon": "amazon-adsystem.com",
            "mediamath": "mediamath.com",
            "adform": "adform.com",
        }

        for js_content in js_files:
            # Search for bidder declarations
            for bidder_code, domain in bidder_to_domain.items():
                if f'bidder:"{bidder_code}"' in js_content or f"bidder:'{bidder_code}'" in js_content:
                    bidders.add(domain)

        return list(bidders)
