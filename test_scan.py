#!/usr/bin/env python3
"""Test script to demonstrate pubSearch scanning capabilities."""

import asyncio
import json
from app.services.orchestrator import ScanOrchestrator


async def main():
    """Run test scans against sample domains."""
    orchestrator = ScanOrchestrator()

    # Test single domain
    print("=" * 80)
    print("Testing single domain scan: example.com")
    print("=" * 80)

    report = await orchestrator.run_single_scan("example.com")

    print(f"\n📊 Publisher: {report.domain}")
    print(f"🔍 ads.txt verified: {report.ads_txt_verified}")
    print(f"⏱️  Scan duration: {report.scan_duration_ms}ms")
    print(f"📈 Signal recovery potential: {report.estimated_signal_recovery_pct}%")

    print(f"\n🚨 Vulnerabilities ({len(report.vulnerabilities)}):")
    for vuln in report.vulnerabilities:
        print(f"  [{vuln.severity.upper()}] {vuln.type}: {vuln.details}")

    print(f"\n💰 Monetization Gaps ({len(report.monetization_gaps)}):")
    for gap in report.monetization_gaps:
        print(f"  {gap.type}: {gap.details}")
        if gap.opportunity:
            print(f"    → Opportunity: {gap.opportunity}")

    # Save to JSON
    output_file = "scan_report_example.json"
    with open(output_file, "w") as f:
        json.dump(report.model_dump(), f, indent=2)

    print(f"\n✅ Full report saved to: {output_file}")

    # Test batch scan
    print("\n" + "=" * 80)
    print("Testing batch scan: example.com, example.org")
    print("=" * 80)

    reports = await orchestrator.run_batch_scan(["example.com", "example.org"])

    print(f"\n📊 Batch Results:")
    print(f"  Total: {len(reports)}")
    print(f"  Successful: {sum(1 for r in reports if not r.error)}")
    print(f"  Failed: {sum(1 for r in reports if r.error)}")

    for report in reports:
        print(f"\n  {report.domain}:")
        print(f"    Vulnerabilities: {len(report.vulnerabilities)}")
        print(f"    Monetization Gaps: {len(report.monetization_gaps)}")
        print(f"    Recovery Potential: {report.estimated_signal_recovery_pct}%")

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
