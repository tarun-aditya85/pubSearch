"""Scan orchestrator coordinating all analysis engines."""

import asyncio
import logging
import time
from app.schemas import ScanReport, Vulnerability, MonetizationGap
from app.services.crawler import CrawlerService
from app.services.analyzers.ads_txt import AdsTxtAnalyzer
from app.services.analyzers.security import SecurityAnalyzer
from app.services.analyzers.monetization import MonetizationAnalyzer
from app.services.agency_search.service import AgencySearchService
from app.services.dsp_search.service import DSPSearchService
from app.core.utils import generate_publisher_id
from app.config import settings

logger = logging.getLogger(__name__)


class ScanOrchestrator:
    """Orchestrates complete scan workflow."""

    def __init__(self):
        self.crawler = CrawlerService()
        self.ads_txt_analyzer = AdsTxtAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.monetization_analyzer = MonetizationAnalyzer()
        self.agency_search = AgencySearchService()
        self.dsp_search = DSPSearchService()

    async def run_single_scan(self, domain: str) -> ScanReport:
        """
        Execute complete scan for a single domain.

        Args:
            domain: Domain to scan

        Returns:
            Complete ScanReport
        """
        start_time = time.time()

        logger.info(f"Starting scan for {domain}")

        # Initialize report
        publisher_id = generate_publisher_id(domain)
        report = ScanReport(
            publisher_id=publisher_id,
            domain=domain,
            ads_txt_verified=False,
            vulnerabilities=[],
            monetization_gaps=[],
            estimated_signal_recovery_pct=0,
        )

        try:
            # Step 1: Crawl domain and collect raw data
            crawler_result = await self.crawler.scan_domain(domain)

            if not crawler_result.success:
                report.error = crawler_result.error
                return report

            # Step 2: Fetch and validate ads.txt (in parallel with crawl data processing)
            ads_txt_content = await self.crawler.fetch_ads_txt(domain)
            report.ads_txt_verified = self.ads_txt_analyzer.validate(ads_txt_content)

            # Step 3: Run security analysis
            vulnerabilities = self.security_analyzer.analyze(
                requests=crawler_result.requests,
                js_files=crawler_result.js_files,
                cookies=crawler_result.cookies,
                publisher_domain=domain,
            )
            report.vulnerabilities = vulnerabilities

            # Step 4: Run monetization analysis
            monetization_gaps = self.monetization_analyzer.analyze(
                requests=crawler_result.requests,
                js_files=crawler_result.js_files,
                publisher_domain=domain,
            )
            report.monetization_gaps = monetization_gaps

            # Step 5: Calculate estimated signal recovery percentage
            report.estimated_signal_recovery_pct = self._calculate_signal_recovery(
                vulnerabilities, monetization_gaps
            )

            # Calculate scan duration
            duration_ms = int((time.time() - start_time) * 1000)
            report.scan_duration_ms = duration_ms

            logger.info(
                f"Scan complete for {domain}: "
                f"{len(vulnerabilities)} vulnerabilities, "
                f"{len(monetization_gaps)} gaps, "
                f"{report.estimated_signal_recovery_pct}% recovery potential"
            )

        except Exception as e:
            logger.error(f"Scan failed for {domain}: {e}")
            report.error = str(e)

        return report

    async def run_batch_scan(self, domains: list[str]) -> list[ScanReport]:
        """
        Execute scans for multiple domains concurrently.

        Args:
            domains: List of domains to scan

        Returns:
            List of ScanReports
        """
        logger.info(f"Starting batch scan for {len(domains)} domains")

        # Create scan tasks
        tasks = [self.run_single_scan(domain) for domain in domains]

        # Run concurrently with exception handling
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error reports
        reports: list[ScanReport] = []
        for domain, result in zip(domains, results):
            if isinstance(result, Exception):
                # Create error report
                reports.append(
                    ScanReport(
                        publisher_id=generate_publisher_id(domain),
                        domain=domain,
                        ads_txt_verified=False,
                        vulnerabilities=[],
                        monetization_gaps=[],
                        estimated_signal_recovery_pct=0,
                        error=str(result),
                    )
                )
            else:
                reports.append(result)

        logger.info(f"Batch scan complete: {len(reports)} reports generated")
        return reports

    def _calculate_signal_recovery(
        self, vulnerabilities: list[Vulnerability], monetization_gaps: list[MonetizationGap]
    ) -> int:
        """
        Calculate estimated signal recovery percentage based on findings.

        Uses weighted scoring based on gap types.
        """
        recovery_pct = 0

        # Monetization gaps contribute to recovery potential
        for gap in monetization_gaps:
            if gap.type == "MISSING_S2S_BRIDGE":
                recovery_pct += settings.s2s_bridge_recovery_pct
            elif gap.type in ["LOW_HEADER_BIDDING", "NO_HEADER_BIDDING"]:
                recovery_pct += settings.header_bidding_recovery_pct
            elif gap.type == "SCRIPT_BLOAT":
                recovery_pct += settings.script_bloat_recovery_pct

        # PII leaks indicate recoverable signal loss
        pii_leak_count = sum(1 for v in vulnerabilities if v.type == "PII_LEAK")
        if pii_leak_count > 0:
            recovery_pct += settings.pii_leak_recovery_pct

        # Cap at 100%
        return min(recovery_pct, 100)

    async def run_agency_search(self, domain: str):
        """
        Execute agency search for a domain.

        Args:
            domain: Domain to analyze

        Returns:
            AgencySearchReport with ranked agencies
        """
        logger.info(f"Starting agency search for {domain}")

        try:
            # Crawl domain
            crawler_result = await self.crawler.scan_domain(domain)

            if not crawler_result.success:
                raise Exception(f"Crawler failed: {crawler_result.error}")

            # Fetch ads.txt
            ads_txt_content = await self.crawler.fetch_ads_txt(domain)

            # Run agency search
            report = await self.agency_search.search_agencies(
                crawler_result, ads_txt_content
            )

            logger.info(
                f"Agency search complete: {report.total_agencies_found} agencies, "
                f"quality: {report.overall_agency_quality}"
            )

            return report

        except Exception as e:
            logger.error(f"Agency search failed for {domain}: {e}")
            raise

    async def run_dsp_search(self, domain: str):
        """
        Execute DSP search for a domain.

        Args:
            domain: Domain to analyze

        Returns:
            DSPSearchReport with ranked DSPs
        """
        logger.info(f"Starting DSP search for {domain}")

        try:
            # Crawl domain
            crawler_result = await self.crawler.scan_domain(domain)

            if not crawler_result.success:
                raise Exception(f"Crawler failed: {crawler_result.error}")

            # Fetch ads.txt
            ads_txt_content = await self.crawler.fetch_ads_txt(domain)

            # Run DSP search
            report = await self.dsp_search.search_dsps(
                crawler_result, ads_txt_content
            )

            logger.info(
                f"DSP search complete: {report.total_dsps_found} DSPs, "
                f"{report.potential_additions} potential additions"
            )

            return report

        except Exception as e:
            logger.error(f"DSP search failed for {domain}: {e}")
            raise
