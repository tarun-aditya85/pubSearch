"""Monetization opportunity analyzer."""

import logging
from app.schemas import MonetizationGap
from app.services.crawler import InterceptedRequest
from app.core.utils import extract_domain_from_url, is_third_party
from app.config import settings

logger = logging.getLogger(__name__)


class MonetizationAnalyzer:
    """Analyzer for revenue monetization opportunities."""

    # Known SSP domains for header bidding detection
    SSP_DOMAINS = [
        "appnexus.com",
        "rubiconproject.com",
        "pubmatic.com",
        "openx.net",
        "indexexchange.com",
        "sovrn.com",
        "criteo.com",
        "amazon-adsystem.com",
        "spotxchange.com",
        "teads.tv",
        "improvedigital.com",
        "33across.com",
        "rhythmone.com",
        "sharethrough.com",
        "yieldmo.com",
        "triplelift.com",
        "district-m.net",
        "smartadserver.com",
        "adform.com",
    ]

    # Direct tracking domains that should use S2S bridges
    DIRECT_TRACKING_TARGETS = [
        "google-analytics.com",
        "analytics.google.com",
        "facebook.com",
        "connect.facebook.net",
        "doubleclick.net",
    ]

    def analyze(
        self,
        requests: list[InterceptedRequest],
        js_files: list[str],
        publisher_domain: str,
    ) -> list[MonetizationGap]:
        """
        Analyze for monetization opportunities.

        Args:
            requests: Intercepted network requests
            js_files: JavaScript file contents
            publisher_domain: Publisher's domain

        Returns:
            List of detected monetization gaps
        """
        gaps: list[MonetizationGap] = []

        # Check for missing S2S bridge
        s2s_gap = self._check_s2s_bridge(requests, publisher_domain)
        if s2s_gap:
            gaps.append(s2s_gap)

        # Check header bidding setup
        hb_gap = self._check_header_bidding(requests, js_files)
        if hb_gap:
            gaps.append(hb_gap)

        # Check script bloat
        bloat_gap = self._check_script_bloat(requests, publisher_domain)
        if bloat_gap:
            gaps.append(bloat_gap)

        logger.info(f"Found {len(gaps)} monetization opportunities")
        return gaps

    def _check_s2s_bridge(
        self, requests: list[InterceptedRequest], publisher_domain: str
    ) -> MonetizationGap | None:
        """Check if publisher is using direct connections instead of S2S bridges."""
        direct_connections = []

        for request in requests:
            request_domain = extract_domain_from_url(request.url)

            # Check if connecting directly to tracking platforms
            for target in self.DIRECT_TRACKING_TARGETS:
                if target in request_domain:
                    # Check if it's truly third-party (not proxied through publisher domain)
                    if is_third_party(request.url, publisher_domain):
                        direct_connections.append(target)
                        break

        if direct_connections:
            # Deduplicate
            unique_targets = list(set(direct_connections))

            return MonetizationGap(
                type="MISSING_S2S_BRIDGE",
                details=f"Direct client-side connections to {', '.join(unique_targets[:3])}",
                opportunity=f"Implement server-side proxying to capture {settings.s2s_bridge_recovery_pct}% more first-party data signals",
            )

        return None

    def _check_header_bidding(
        self, requests: list[InterceptedRequest], js_files: list[str]
    ) -> MonetizationGap | None:
        """Analyze header bidding setup."""
        # Check for Prebid.js presence
        has_prebid = any(
            "prebid" in js_content.lower() or "pbjs" in js_content for js_content in js_files
        )

        if not has_prebid:
            return MonetizationGap(
                type="NO_HEADER_BIDDING",
                details="No header bidding implementation detected (Prebid.js not found)",
                opportunity="Implement header bidding to increase ad revenue by 15-30%",
            )

        # Count unique SSP bidders
        ssp_count = 0
        detected_ssps = set()

        for request in requests:
            request_domain = extract_domain_from_url(request.url)

            for ssp in self.SSP_DOMAINS:
                if ssp in request_domain:
                    detected_ssps.add(ssp)

        ssp_count = len(detected_ssps)

        # Flag if SSP count is low
        if ssp_count < settings.min_ssp_count_for_healthy_bidding:
            return MonetizationGap(
                type="LOW_HEADER_BIDDING",
                details=f"Only {ssp_count} SSP bidders detected (recommended: {settings.min_ssp_count_for_healthy_bidding}+)",
                opportunity=f"Add {settings.min_ssp_count_for_healthy_bidding - ssp_count} more SSPs to increase bid competition and CPMs by {settings.header_bidding_recovery_pct}%",
            )

        return None

    def _check_script_bloat(
        self, requests: list[InterceptedRequest], publisher_domain: str
    ) -> MonetizationGap | None:
        """Check for excessive third-party script loading."""
        # Count third-party scripts
        third_party_scripts = [
            r
            for r in requests
            if r.resource_type == "script" and is_third_party(r.url, publisher_domain)
        ]

        script_count = len(third_party_scripts)

        if script_count > settings.high_script_count_threshold:
            return MonetizationGap(
                type="SCRIPT_BLOAT",
                details=f"{script_count} third-party scripts detected (threshold: {settings.high_script_count_threshold})",
                opportunity=f"Consolidate tracking to S2S to reduce page load time by 20-40% and improve user experience",
            )

        return None
