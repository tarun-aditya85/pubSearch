"""Agency ranking and scoring engine."""

import logging
from typing import Dict, List
from .schemas import AgencyMatch, AgencySearchReport, AgencyRankingCriteria

logger = logging.getLogger(__name__)


class AgencyRanker:
    """
    Ranks agencies based on multiple quality dimensions.

    Ranking Factors:
    1. Market Presence (30%): Number of publishers, market reach
    2. Transparency (30%): sellers.json, TAG certification
    3. Tech Sophistication (40%): S2S, header bidding, innovation
    """

    # Known premium agencies (Tier 1)
    PREMIUM_AGENCIES = {
        "google.com": "Google Ad Manager",
        "rubiconproject.com": "Magnite (Rubicon Project)",
        "openx.com": "OpenX",
        "pubmatic.com": "PubMatic",
        "indexexchange.com": "Index Exchange",
        "appnexus.com": "Xandr (AppNexus)",
        "criteo.com": "Criteo",
        "amazon-adsystem.com": "Amazon Publisher Services",
        "sovrn.com": "Sovrn",
        "triplelift.com": "TripleLift",
    }

    # Typical publisher count ranges for market presence scoring
    MARKET_PRESENCE_THRESHOLDS = {
        "excellent": 1000,  # >1000 publishers
        "good": 500,
        "average": 100,
        "poor": 10,
    }

    def __init__(self, criteria: AgencyRankingCriteria | None = None):
        self.criteria = criteria or AgencyRankingCriteria()

    def rank_agencies(
        self,
        agencies: List[Dict],
        ads_txt_entries: List[Dict],
        detected_capabilities: Dict[str, Dict],
    ) -> List[AgencyMatch]:
        """
        Rank agencies based on quality metrics.

        Args:
            agencies: List of agency data from sellers.json harvest
            ads_txt_entries: Parsed ads.txt entries
            detected_capabilities: Tech capabilities detected during scan

        Returns:
            Ranked list of AgencyMatch objects
        """
        ranked_agencies = []

        for agency in agencies:
            match = self._score_agency(agency, ads_txt_entries, detected_capabilities)
            if match.quality_score >= self.criteria.min_quality_score:
                ranked_agencies.append(match)

        # Sort by quality score descending
        ranked_agencies.sort(key=lambda x: x.quality_score, reverse=True)

        return ranked_agencies

    def _score_agency(
        self,
        agency: Dict,
        ads_txt_entries: List[Dict],
        detected_capabilities: Dict[str, Dict],
    ) -> AgencyMatch:
        """Calculate comprehensive quality score for an agency."""

        domain = agency.get("domain", "")
        seller_id = agency.get("seller_id", "")
        name = agency.get("name", self.PREMIUM_AGENCIES.get(domain, domain))

        # Find relationship from ads.txt
        relationship = "RESELLER"  # Default
        cert_id = None
        for entry in ads_txt_entries:
            if entry.get("domain") == domain:
                relationship = entry.get("relationship", "RESELLER")
                cert_id = entry.get("certification_id")
                break

        # 1. Market Presence Score (0-100)
        market_score = self._calculate_market_presence_score(agency)

        # 2. Transparency Score (0-100)
        transparency_score = self._calculate_transparency_score(agency, cert_id)

        # 3. Tech Sophistication Score (0-100)
        tech_score = self._calculate_tech_sophistication_score(
            agency, detected_capabilities.get(domain, {})
        )

        # Weighted overall quality score
        quality_score = int(
            market_score * self.criteria.market_presence_weight
            + transparency_score * self.criteria.transparency_weight
            + tech_score * self.criteria.tech_sophistication_weight
        )

        # Calculate opportunity score (inverse of quality - lower quality = higher opportunity)
        opportunity_score = self._calculate_opportunity_score(
            quality_score, relationship, tech_score
        )

        # Determine recommended action
        recommended_action = self._get_recommended_action(
            quality_score, opportunity_score, relationship
        )

        return AgencyMatch(
            agency_name=name,
            seller_id=seller_id,
            seller_domain=domain,
            relationship=relationship,
            quality_score=quality_score,
            market_presence_score=market_score,
            transparency_score=transparency_score,
            tech_sophistication_score=tech_score,
            total_publishers_represented=agency.get("publisher_count", 0),
            has_sellers_json=agency.get("has_sellers_json", False),
            certification_authority_id=cert_id,
            supports_s2s=detected_capabilities.get(domain, {}).get("s2s_capable", False),
            header_bidding_capable=detected_capabilities.get(domain, {}).get("hb_capable", False),
            opportunity_score=opportunity_score,
            recommended_action=recommended_action,
        )

    def _calculate_market_presence_score(self, agency: Dict) -> int:
        """Score based on market reach and adoption."""
        publisher_count = agency.get("publisher_count", 0)

        if publisher_count >= self.MARKET_PRESENCE_THRESHOLDS["excellent"]:
            return 100
        elif publisher_count >= self.MARKET_PRESENCE_THRESHOLDS["good"]:
            return 80
        elif publisher_count >= self.MARKET_PRESENCE_THRESHOLDS["average"]:
            return 60
        elif publisher_count >= self.MARKET_PRESENCE_THRESHOLDS["poor"]:
            return 40
        else:
            return 20

    def _calculate_transparency_score(self, agency: Dict, cert_id: str | None) -> int:
        """Score based on transparency and compliance."""
        score = 0

        # Has sellers.json (+50 points)
        if agency.get("has_sellers_json", False):
            score += 50

        # Is in our known premium list (+20 points)
        if agency.get("domain") in self.PREMIUM_AGENCIES:
            score += 20

        # Has TAG certification (+30 points)
        if cert_id:
            score += 30

        return min(score, 100)

    def _calculate_tech_sophistication_score(
        self, agency: Dict, capabilities: Dict
    ) -> int:
        """Score based on technology capabilities."""
        score = 50  # Base score

        # S2S support (+25 points)
        if capabilities.get("s2s_capable", False):
            score += 25

        # Header bidding support (+25 points)
        if capabilities.get("hb_capable", False):
            score += 25

        # Innovation indicators (newer agencies often more tech-forward)
        # This would require additional data sources

        return min(score, 100)

    def _calculate_opportunity_score(
        self, quality_score: int, relationship: str, tech_score: int
    ) -> int:
        """
        Calculate opportunity for improvement.

        Higher opportunity = lower current quality but high potential.
        """
        base_opportunity = 100 - quality_score

        # RESELLER relationships have less opportunity (you don't control them)
        if relationship == "RESELLER":
            base_opportunity = int(base_opportunity * 0.5)

        # Low tech sophistication = high opportunity
        if tech_score < 50:
            base_opportunity += 20

        return min(base_opportunity, 100)

    def _get_recommended_action(
        self, quality_score: int, opportunity_score: int, relationship: str
    ) -> str:
        """Generate actionable recommendation."""

        if quality_score >= 80:
            return "Maintain: High-quality agency performing well"

        if opportunity_score >= 70:
            if relationship == "DIRECT":
                return "Upgrade: Work with agency to enable S2S and header bidding"
            else:
                return "Replace: Consider switching to direct relationship with higher-quality agency"

        if quality_score < 50:
            return "Review: Audit agency performance and consider alternatives"

        return "Monitor: Track performance and reassess quarterly"

    def generate_report(
        self, publisher_domain: str, ranked_agencies: List[AgencyMatch]
    ) -> AgencySearchReport:
        """Generate comprehensive agency search report."""

        direct_count = sum(1 for a in ranked_agencies if a.relationship == "DIRECT")
        reseller_count = len(ranked_agencies) - direct_count

        # Calculate overall metrics
        avg_quality = (
            int(sum(a.quality_score for a in ranked_agencies) / len(ranked_agencies))
            if ranked_agencies
            else 0
        )

        has_premium = any(
            a.seller_domain in self.PREMIUM_AGENCIES for a in ranked_agencies
        )

        # Diversification: more unique agencies = better
        diversification = min(len(ranked_agencies) * 10, 100)

        # Top opportunities (highest opportunity scores)
        top_opportunities = sorted(
            ranked_agencies, key=lambda x: x.opportunity_score, reverse=True
        )[:3]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            ranked_agencies, direct_count, has_premium
        )

        return AgencySearchReport(
            publisher_domain=publisher_domain,
            total_agencies_found=len(ranked_agencies),
            direct_relationships=direct_count,
            reseller_relationships=reseller_count,
            agencies=ranked_agencies,
            top_opportunities=top_opportunities,
            overall_agency_quality=avg_quality,
            has_premium_agencies=has_premium,
            diversification_score=diversification,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, agencies: List[AgencyMatch], direct_count: int, has_premium: bool
    ) -> List[str]:
        """Generate actionable recommendations."""
        recs = []

        if not has_premium:
            recs.append(
                "Add premium agency: Consider integrating Google Ad Manager, Magnite, or PubMatic"
            )

        if direct_count < 2:
            recs.append(
                "Increase direct relationships: Target 3-5 direct agency partnerships for better control"
            )

        low_quality = [a for a in agencies if a.quality_score < 50]
        if low_quality:
            recs.append(
                f"Review {len(low_quality)} low-quality agencies and consider replacement"
            )

        no_hb = [a for a in agencies if not a.header_bidding_capable]
        if len(no_hb) > len(agencies) * 0.5:
            recs.append(
                "Enable header bidding: Over 50% of agencies lack HB integration"
            )

        return recs
