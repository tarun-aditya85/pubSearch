"""FastAPI application for pubSearch audit engine."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.core.browser_pool import browser_pool
from app.schemas import (
    ScanRequest,
    BatchScanRequest,
    ScanReport,
    BatchScanResponse,
)
from app.services.orchestrator import ScanOrchestrator
from app.services.agency_search.schemas import AgencySearchRequest, AgencySearchReport
from app.services.dsp_search.schemas import DSPSearchRequest, DSPSearchReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle (startup and shutdown)."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await browser_pool.initialize()
    logger.info("Application ready")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await browser_pool.cleanup()
    logger.info("Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AdTech Security & Monetization Audit Engine",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AdTech Security & Monetization Audit Engine",
        "endpoints": {
            "health": "/health",
            "scan_single": "POST /scan",
            "scan_batch": "POST /scan/batch",
            "agency_search": "POST /search/agencies",
            "dsp_search": "POST /search/dsps",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.post("/scan", response_model=ScanReport)
async def scan_domain(request: ScanRequest):
    """
    Scan a single domain for security vulnerabilities and monetization gaps.

    Args:
        request: ScanRequest with domain to scan

    Returns:
        ScanReport with findings
    """
    try:
        logger.info(f"Received scan request for: {request.domain}")

        orchestrator = ScanOrchestrator()
        report = await orchestrator.run_single_scan(request.domain)

        return report

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@app.post("/scan/batch", response_model=BatchScanResponse)
async def scan_batch(request: BatchScanRequest):
    """
    Scan multiple domains concurrently.

    Args:
        request: BatchScanRequest with list of domains

    Returns:
        BatchScanResponse with all reports
    """
    try:
        logger.info(f"Received batch scan request for {len(request.domains)} domains")

        orchestrator = ScanOrchestrator()
        reports = await orchestrator.run_batch_scan(request.domains)

        # Calculate statistics
        successful = sum(1 for r in reports if not r.error)
        failed = len(reports) - successful

        return BatchScanResponse(
            total=len(reports),
            successful=successful,
            failed=failed,
            reports=reports,
        )

    except Exception as e:
        logger.error(f"Batch scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch scan failed: {str(e)}")


@app.post("/search/agencies", response_model=AgencySearchReport)
async def search_agencies(request: AgencySearchRequest):
    """
    Search and rank agencies for a publisher domain.

    Args:
        request: AgencySearchRequest with domain and criteria

    Returns:
        AgencySearchReport with ranked agencies
    """
    try:
        logger.info(f"Received agency search request for: {request.publisher_domain}")

        orchestrator = ScanOrchestrator()
        report = await orchestrator.run_agency_search(request.publisher_domain)

        return report

    except Exception as e:
        logger.error(f"Agency search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agency search failed: {str(e)}")


@app.post("/search/dsps", response_model=DSPSearchReport)
async def search_dsps(request: DSPSearchRequest):
    """
    Search and rank DSPs for a publisher domain.

    Args:
        request: DSPSearchRequest with domain and criteria

    Returns:
        DSPSearchReport with ranked DSPs
    """
    try:
        logger.info(f"Received DSP search request for: {request.publisher_domain}")

        orchestrator = ScanOrchestrator()
        report = await orchestrator.run_dsp_search(request.publisher_domain)

        return report

    except Exception as e:
        logger.error(f"DSP search failed: {e}")
        raise HTTPException(status_code=500, detail=f"DSP search failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
