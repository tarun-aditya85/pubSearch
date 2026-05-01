#!/usr/bin/env python3
"""Test script for Agency and DSP search functionality."""

import asyncio
import json
from app.services.orchestrator import ScanOrchestrator


async def test_agency_search():
    """Test agency search functionality."""
    print("=" * 80)
    print("Testing Agency Search")
    print("=" * 80)

    orchestrator = ScanOrchestrator()

    # Test domain (example.com likely won't have many agencies, but will test flow)
    domain = "example.com"
    print(f"\n🔍 Searching agencies for: {domain}")

    try:
        report = await orchestrator.run_agency_search(domain)

        print(f"\n📊 Results:")
        print(f"  Total agencies found: {report.total_agencies_found}")
        print(f"  Direct relationships: {report.direct_relationships}")
        print(f"  Reseller relationships: {report.reseller_relationships}")
        print(f"  Overall agency quality: {report.overall_agency_quality}/100")
        print(f"  Has premium agencies: {report.has_premium_agencies}")
        print(f"  Diversification score: {report.diversification_score}/100")

        print(f"\n🏢 Top Agencies:")
        for i, agency in enumerate(report.agencies[:5], 1):
            print(f"\n  {i}. {agency.agency_name} ({agency.seller_domain})")
            print(f"     Quality Score: {agency.quality_score}/100")
            print(f"     Relationship: {agency.relationship}")
            print(f"     Market Presence: {agency.market_presence_score}/100")
            print(f"     Transparency: {agency.transparency_score}/100")
            print(f"     Tech Sophistication: {agency.tech_sophistication_score}/100")
            print(f"     Publishers Represented: {agency.total_publishers_represented}")
            print(f"     Opportunity Score: {agency.opportunity_score}/100")
            if agency.recommended_action:
                print(f"     → {agency.recommended_action}")

        if report.top_opportunities:
            print(f"\n💡 Top Opportunities:")
            for opp in report.top_opportunities:
                print(f"  • {opp.agency_name}: {opp.recommended_action}")

        if report.recommendations:
            print(f"\n📝 Recommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")

        # Save report
        with open("agency_search_report.json", "w") as f:
            json.dump(report.model_dump(), f, indent=2)

        print(f"\n✅ Report saved to: agency_search_report.json")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_dsp_search():
    """Test DSP search functionality."""
    print("\n" + "=" * 80)
    print("Testing DSP Search")
    print("=" * 80)

    orchestrator = ScanOrchestrator()

    domain = "example.com"
    print(f"\n🔍 Searching DSPs for: {domain}")

    try:
        report = await orchestrator.run_dsp_search(domain)

        print(f"\n📊 Results:")
        print(f"  Total DSPs found: {report.total_dsps_found}")
        print(f"  Currently integrated: {report.currently_integrated}")
        print(f"  Potential additions: {report.potential_additions}")
        print(f"  Overall DSP quality: {report.overall_dsp_quality}/100")
        print(f"  Portfolio diversification: {report.portfolio_diversification}/100")
        print(f"  Header bidding coverage: {report.header_bidding_coverage}%")
        print(f"  Estimated revenue uplift: {report.estimated_total_revenue_uplift_pct}%")

        print(f"\n💰 DSP Breakdown by Format:")
        for fmt, count in report.by_format.items():
            print(f"  {fmt.title()}: {count} DSPs")

        print(f"\n🎯 Top DSPs:")
        for i, dsp in enumerate(report.dsps[:5], 1):
            print(f"\n  {i}. {dsp.dsp_name} ({dsp.dsp_domain})")
            print(f"     Quality Score: {dsp.quality_score}/100")
            print(f"     Integrated: {'✅' if dsp.is_currently_integrated else '❌'}")
            print(f"     Detected via: {dsp.detected_via}")
            if dsp.relationship:
                print(f"     Relationship: {dsp.relationship}")
            print(f"     Market Share: {dsp.market_share_score}/100")
            print(f"     Performance: {dsp.performance_score}/100")
            print(f"     Opportunity: {dsp.opportunity_score}/100")
            print(f"     Ad Formats: {', '.join(dsp.ad_formats)}")
            print(f"     Header Bidding: {'✅' if dsp.header_bidding_integration else '❌'}")
            if dsp.estimated_revenue_uplift_pct:
                print(f"     Revenue Uplift: +{dsp.estimated_revenue_uplift_pct}%")
            print(f"     Integration: {dsp.integration_complexity}")
            if dsp.recommended_action:
                print(f"     → {dsp.recommended_action}")

        if report.top_opportunities:
            print(f"\n🚀 Top Opportunities (Not Yet Integrated):")
            for opp in report.top_opportunities:
                print(f"  • {opp.dsp_name}: {opp.recommended_action}")

        if report.recommendations:
            print(f"\n📝 Recommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")

        # Save report
        with open("dsp_search_report.json", "w") as f:
            json.dump(report.model_dump(), f, indent=2)

        print(f"\n✅ Report saved to: dsp_search_report.json")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    await test_agency_search()
    await test_dsp_search()

    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
