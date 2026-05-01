"""DSP ranking and scoring engine."""

import logging
from typing import Dict, List
from .schemas import DSPMatch, DSPSearchReport, DSPRankingCriteria

logger = logging.getLogger(__name__)


class DSPRanker:
    """
    Ranks DSPs based on quality, performance, and opportunity.

    Ranking Factors:
    1. Quality (30%): Market share, reputation, reliability
    2. Performance (40%): Bid rate, win rate, eCPM
    3. Opportunity (30%): Revenue uplift potential
    """

    # Known top-tier DSPs with metadata
    TIER1_DSPS = {
        "google.com": {
            "name": "Google Display & Video 360",
            "formats": ["display", "video", "native"],
            "market_share": 95,
            "pricing": "CPM",
        },
        "thetradedesk.com": {
            "name": "The Trade Desk",
            "formats": ["display", "video", "native", "ctv"],
            "market_share": 90,
            "pricing": "CPM",
        },
        "amazon-adsystem.com": {
            "name": "Amazon DSP",
            "formats": ["display", "video"],
            "market_share": 85,
            "pricing": "CPM",
        },
        "appnexus.com": {
            "name": "Xandr (Microsoft)",
            "formats": ["display", "video", "native"],
            "market_share": 88,
            "pricing": "CPM",
        },
        "mediamath.com": {
            "name": "MediaMath",
            "formats": ["display", "video"],
            "market_share": 75,
            "pricing": "CPM",
        },
    }

    TIER2_DSPS = {
        "adform.com": {"name": "Adform", "market_share": 70},
        "criteo.com": {"name": "Criteo", "market_share": 80},
        "beeswax.com": {"name": "Beeswax", "market_share": 65},
        "stackadapt.com": {"name": "StackAdapt", "market_share": 68},
        "basis.net": {"name": "Basis Technologies", "market_share": 62},
    }

    # SSP domains that also function as DSPs (programmatic platforms)
    SSP_DSP_HYBRID = {
        "rubiconproject.com": "Magnite",
        "pubmatic.com": "PubMatic",
        "openx.com": "OpenX",
        "indexexchange.com": "Index Exchange",
    }

    def __init__(self, criteria: DSPRankingCriteria | None = None):
        self.criteria = criteria or DSPRankingCriteria()

    def rank_dsps(
        self,
        detected_dsps: List[Dict],
        network_requests: List[Dict],
        ads_txt_entries: List[Dict],
    ) -> List[DSPMatch]:
        """
        Rank DSPs based on multiple quality dimensions.

        Args:
            detected_dsps: DSPs detected from various sources
            network_requests: Network request data for detection
            ads_txt_entries: ads.txt entries for relationship verification

        Returns:
            Ranked list of DSPMatch objects
        """
        ranked_dsps = []

        for dsp in detected_dsps:
            match = self._score_dsp(dsp, network_requests, ads_txt_entries)
            if match.quality_score >= self.criteria.min_quality_score:
                ranked_dsps.append(match)

        # Sort by combined quality + opportunity score
        ranked_dsps.sort(
            key=lambda x: (x.quality_score * 0.5 + x.opportunity_score * 0.5),
            reverse=True,
        )

        return ranked_dsps

    def _score_dsp(
        self,
        dsp: Dict,
        network_requests: List[Dict],
        ads_txt_entries: List[Dict],
    ) -> DSPMatch:
        """Calculate comprehensive quality score for a DSP."""

        domain = dsp.get("domain", "")
        name = self._get_dsp_name(domain)
        detected_via = dsp.get("detected_via", "network_request")

        # Check if in ads.txt
        seller_id = None
        relationship = None
        is_integrated = False

        for entry in ads_txt_entries:
            if entry.get("domain") == domain:
                seller_id = entry.get("seller_id")
                relationship = entry.get("relationship")
                is_integrated = True
                break

        # 1. Market Share Score (0-100)
        market_score = self._calculate_market_share_score(domain)

        # 2. Performance Score (0-100)
        performance_score = self._calculate_performance_score(domain, network_requests)

        # 3. Reliability Score (0-100)
        reliability_score = self._calculate_reliability_score(domain, is_integrated)

        # Weighted quality score
        quality_score = int(
            (market_score + performance_score + reliability_score) / 3
        )

        # Opportunity score
        opportunity_score = self._calculate_opportunity_score(
            quality_score, is_integrated, domain
        )

        # Capabilities
        capabilities = self._get_dsp_capabilities(domain)

        # Integration complexity
        complexity = self._assess_integration_complexity(domain, is_integrated)

        # Revenue uplift estimate
        revenue_uplift = self._estimate_revenue_uplift(
            quality_score, is_integrated, opportunity_score
        )

        # Recommended action
        recommended_action = self._get_recommended_action(
            is_integrated, quality_score, opportunity_score
        )

        return DSPMatch(
            dsp_name=name,
            dsp_domain=domain,
            seller_id=seller_id,
            relationship=relationship,
            detected_via=detected_via,
            quality_score=quality_score,
            market_share_score=market_score,
            performance_score=performance_score,
            reliability_score=reliability_score,
            ad_formats=capabilities.get("formats", []),
            pricing_model=capabilities.get("pricing", "CPM"),
            header_bidding_integration=capabilities.get("header_bidding", False),
            deals_marketplace=capabilities.get("deals", False),
            brand_safety=capabilities.get("brand_safety", True),
            opportunity_score=opportunity_score,
            estimated_revenue_uplift_pct=revenue_uplift,
            recommended_action=recommended_action,
            is_currently_integrated=is_integrated,
            integration_complexity=complexity,
        )

    def _get_dsp_name(self, domain: str) -> str:
        """Get human-readable DSP name."""
        if domain in self.TIER1_DSPS:
            return self.TIER1_DSPS[domain]["name"]
        if domain in self.TIER2_DSPS:
            return self.TIER2_DSPS[domain]["name"]
        if domain in self.SSP_DSP_HYBRID:
            return self.SSP_DSP_HYBRID[domain]

        # Extract name from domain
        return domain.replace(".com", "").replace("-", " ").title()

    def _calculate_market_share_score(self, domain: str) -> int:
        """Score based on market share and adoption."""
        if domain in self.TIER1_DSPS:
            return self.TIER1_DSPS[domain]["market_share"]
        if domain in self.TIER2_DSPS:
            return self.TIER2_DSPS[domain]["market_share"]
        if domain in self.SSP_DSP_HYBRID:
            return 75  # Hybrid platforms typically have good reach

        # Unknown DSPs get average score
        return 50

    def _calculate_performance_score(
        self, domain: str, network_requests: List[Dict]
    ) -> int:
        """
        Score based on performance indicators.

        In production, this would analyze:
        - Bid response rate
        - Win rate
        - Average eCPM
        - Fill rate
        """
        # For MVP, use tier-based scoring
        if domain in self.TIER1_DSPS:
            return 90
        if domain in self.TIER2_DSPS:
            return 75

        # Check request volume as proxy for performance
        request_count = sum(
            1 for req in network_requests if domain in req.get("url", "")
        )

        if request_count > 10:
            return 70
        elif request_count > 5:
            return 60
        else:
            return 50

    def _calculate_reliability_score(self, domain: str, is_integrated: bool) -> int:
        """Score based on reliability and uptime."""
        base_score = 70

        # Tier 1 DSPs have proven reliability
        if domain in self.TIER1_DSPS:
            base_score = 95

        # Integration in ads.txt indicates trust
        if is_integrated:
            base_score += 10

        return min(base_score, 100)

    def _calculate_opportunity_score(
        self, quality_score: int, is_integrated: bool, domain: str
    ) -> int:
        """
        Calculate revenue opportunity score.

        High opportunity = high quality BUT not yet integrated.
        """
        if is_integrated:
            # Already integrated, limited opportunity
            return min(30, 100 - quality_score)

        # Not integrated - opportunity based on quality
        opportunity = quality_score  # High quality = high opportunity

        # Tier 1 DSPs have highest opportunity if not integrated
        if domain in self.TIER1_DSPS:
            opportunity = min(opportunity + 20, 100)

        return opportunity

    def _get_dsp_capabilities(self, domain: str) -> Dict:
        """Get DSP capabilities and features."""
        if domain in self.TIER1_DSPS:
            data = self.TIER1_DSPS[domain]
            return {
                "formats": data.get("formats", ["display"]),
                "pricing": data.get("pricing", "CPM"),
                "header_bidding": True,
                "deals": True,
                "brand_safety": True,
            }

        # Default capabilities
        return {
            "formats": ["display"],
            "pricing": "CPM",
            "header_bidding": False,
            "deals": False,
            "brand_safety": False,
        }

    def _assess_integration_complexity(self, domain: str, is_integrated: bool) -> str:
        """Assess how difficult integration would be."""
        if is_integrated:
            return "already_integrated"

        # Tier 1 DSPs typically have good documentation
        if domain in self.TIER1_DSPS:
            return "easy"

        # Smaller DSPs may require more effort
        if domain in self.TIER2_DSPS:
            return "medium"

        return "hard"

    def _estimate_revenue_uplift(
        self, quality_score: int, is_integrated: bool, opportunity_score: int
    ) -> int:
        """Estimate revenue increase from adding this DSP."""
        if is_integrated:
            return 0  # Already integrated

        # Base uplift on quality and opportunity
        base_uplift = int((quality_score + opportunity_score) / 10)

        return min(base_uplift, 30)  # Cap at 30% per DSP

    def _get_recommended_action(
        self, is_integrated: bool, quality_score: int, opportunity_score: int
    ) -> str:
        """Generate actionable recommendation."""
        if is_integrated:
            if quality_score >= 80:
                return "Optimize: Analyze performance and increase bid density"
            else:
                return "Review: Audit DSP performance and consider pausing"

        # Not integrated
        if opportunity_score >= 70:
            return f"Integrate: High-quality DSP with {self._estimate_revenue_uplift(quality_score, False, opportunity_score)}% revenue potential"

        if quality_score >= 70:
            return "Consider: Test integration in limited capacity"

        return "Skip: Low priority, focus on higher-quality DSPs first"

    def generate_report(
        self, publisher_domain: str, ranked_dsps: List[DSPMatch]
    ) -> DSPSearchReport:
        """Generate comprehensive DSP search report."""

        integrated_count = sum(1 for d in ranked_dsps if d.is_currently_integrated)
        potential_additions = len(ranked_dsps) - integrated_count

        # Overall metrics
        avg_quality = (
            int(sum(d.quality_score for d in ranked_dsps) / len(ranked_dsps))
            if ranked_dsps
            else 0
        )

        # Portfolio diversification
        diversification = min(len(ranked_dsps) * 5, 100)

        # Header bidding coverage
        hb_capable = sum(1 for d in ranked_dsps if d.header_bidding_integration)
        hb_coverage = int((hb_capable / len(ranked_dsps)) * 100) if ranked_dsps else 0

        # Top opportunities (not integrated, high opportunity score)
        top_opportunities = sorted(
            [d for d in ranked_dsps if not d.is_currently_integrated],
            key=lambda x: x.opportunity_score,
            reverse=True,
        )[:5]

        # Total revenue uplift estimate
        total_uplift = sum(
            d.estimated_revenue_uplift_pct or 0
            for d in top_opportunities
        )

        # Format breakdown
        format_counts = {"display": 0, "video": 0, "native": 0}
        for dsp in ranked_dsps:
            for fmt in dsp.ad_formats:
                if fmt in format_counts:
                    format_counts[fmt] += 1

        # Recommendations
        recommendations = self._generate_recommendations(
            ranked_dsps, integrated_count, hb_coverage
        )

        return DSPSearchReport(
            publisher_domain=publisher_domain,
            total_dsps_found=len(ranked_dsps),
            currently_integrated=integrated_count,
            potential_additions=potential_additions,
            dsps=ranked_dsps,
            top_opportunities=top_opportunities,
            overall_dsp_quality=avg_quality,
            portfolio_diversification=diversification,
            header_bidding_coverage=hb_coverage,
            estimated_total_revenue_uplift_pct=min(total_uplift, 50),
            recommendations=recommendations,
            by_format=format_counts,
        )

    def _generate_recommendations(
        self, dsps: List[DSPMatch], integrated_count: int, hb_coverage: int
    ) -> List[str]:
        """Generate actionable recommendations."""
        recs = []

        if integrated_count < 3:
            recs.append(
                "Increase DSP diversity: Integrate 3-5 quality DSPs for optimal competition"
            )

        # Check for Tier 1 DSPs
        has_tier1 = any(d.dsp_domain in self.TIER1_DSPS for d in dsps if d.is_currently_integrated)
        if not has_tier1:
            recs.append(
                "Add Tier 1 DSP: Integrate Google DV360, The Trade Desk, or Amazon DSP"
            )

        if hb_coverage < 80:
            recs.append(
                f"Enable header bidding: Only {hb_coverage}% of DSPs support HB"
            )

        # Video opportunity
        video_dsps = [d for d in dsps if "video" in d.ad_formats and d.is_currently_integrated]
        if len(video_dsps) < 2:
            recs.append(
                "Add video DSPs: Expand video monetization with specialized DSPs"
            )

        return recs
