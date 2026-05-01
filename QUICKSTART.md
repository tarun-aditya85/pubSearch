# pubSearch Quick Start Guide

## Overview

**pubSearch** is an automated AdTech security and monetization audit engine that performs "Outside-In" analysis of digital publishers to identify:
- **Security vulnerabilities**: PII leakage, exposed API keys, insecure cookies
- **Revenue gaps**: Missing S2S bridges, low header bidding density, script bloat

## Installation

### 1. Activate Conda Environment
```bash
eval "$(/Users/lmv/miniconda3/bin/conda shell.zsh hook)" && conda activate pubsearch
```

### 2. Dependencies Already Installed
- FastAPI (web framework)
- Playwright (browser automation)
- Pydantic (data validation)
- All dependencies in `requirements.txt`

## Running the Server

### Start FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Server will be available at: `http://localhost:8000`

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Scan Single Domain
```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'
```

#### Batch Scan Multiple Domains
```bash
curl -X POST http://localhost:8000/scan/batch \
  -H "Content-Type: application/json" \
  -d '{"domains": ["example.com", "nytimes.com", "techcrunch.com"]}'
```

## Using the Python Test Script

```bash
python test_scan.py
```

This will:
1. Scan `example.com` and display results
2. Run a batch scan of multiple domains
3. Save JSON report to `scan_report_example.json`

## Output Format

### JSON Report Structure
```json
{
  "publisher_id": "example-com",
  "domain": "example.com",
  "timestamp": "2026-04-29T...",
  "ads_txt_verified": false,
  "vulnerabilities": [
    {
      "type": "PII_LEAK",
      "severity": "high",
      "details": "Email leaked to facebook.com pixel"
    }
  ],
  "monetization_gaps": [
    {
      "type": "MISSING_S2S_BRIDGE",
      "details": "Direct client-side connections to google-analytics.com",
      "opportunity": "Implement S2S proxying to capture 15% more signals"
    }
  ],
  "estimated_signal_recovery_pct": 35,
  "scan_duration_ms": 3200,
  "error": null
}
```

## What Gets Detected

### Security Vulnerabilities

1. **PII_LEAK**: Email/phone numbers passed to 3rd-party tracking pixels
   - Severity: `high`
   - Targets: Facebook, Google Analytics, DoubleClick, etc.

2. **API_KEY_EXPOSED**: Hardcoded API keys in JavaScript
   - Severity: `critical`
   - Patterns: Google Cloud (`AIza...`), AWS (`AKIA...`), Stripe, etc.

3. **INSECURE_COOKIE**: Missing HttpOnly/Secure flags
   - Severity: `medium`
   - Risk: XSS attacks, man-in-the-middle

### Monetization Gaps

1. **MISSING_S2S_BRIDGE**: Direct client-side tracking calls
   - Recovery: ~15% more first-party data signals
   - Fix: Implement server-side proxy for GA/Facebook

2. **LOW_HEADER_BIDDING**: Fewer than 5 SSP bidders
   - Recovery: ~10% higher CPMs
   - Fix: Add more SSPs (Rubicon, OpenX, AppNexus, etc.)

3. **SCRIPT_BLOAT**: Excessive 3rd-party scripts (>15)
   - Recovery: ~5% better user experience
   - Fix: Consolidate tracking to server-side

## Demo Strategy for Sales

### Live Scan During Call
1. **Prospect provides domain**: `prospect-publisher.com`
2. **Run scan in terminal**:
   ```bash
   curl -X POST http://localhost:8000/scan \
     -H "Content-Type: application/json" \
     -d '{"domain": "prospect-publisher.com"}' | jq .
   ```
3. **Show live results**: Point out specific vulnerabilities and gaps
4. **Export JSON**: Save report for follow-up

### Batch Processing for Outreach
1. Create list of Top 100 Indian Publishers in `domains.txt`
2. Run batch scan:
   ```python
   import asyncio
   from app.services.orchestrator import ScanOrchestrator
   
   async def scan_list():
       with open("domains.txt") as f:
           domains = [line.strip() for line in f]
       
       orchestrator = ScanOrchestrator()
       reports = await orchestrator.run_batch_scan(domains)
       
       # Save all reports
       for report in reports:
           with open(f"output/{report.publisher_id}.json", "w") as f:
               f.write(report.model_dump_json(indent=2))
   
   asyncio.run(scan_list())
   ```

3. Filter by `estimated_signal_recovery_pct > 30%` for highest value targets

## Configuration

Edit `app/config.py` to customize:
- Timeouts (page load, scan total)
- User-Agent string
- SSP count thresholds
- Signal recovery percentages

## Legal Compliance

See [LEGAL_SHIELD.md](LEGAL_SHIELD.md) for:
- Passive reconnaissance methodology
- GDPR/CCPA compliance notes
- Responsible disclosure guidelines

## Troubleshooting

### Port Already in Use
```bash
lsof -ti:8000 | xargs kill -9
```

### Playwright Browser Not Found
```bash
playwright install chromium
```

### Module Import Errors
```bash
pip install -r requirements.txt
```

## Next Steps

1. **Test on real publishers**: Try scanning TechCrunch, The Verge, Indian news sites
2. **Export HTML reports**: Build simple HTML template for visual reports
3. **Add more detection patterns**: Expand security and monetization rules
4. **Database storage**: Connect to PostgreSQL for historical tracking

---

**Built for**: 2-person AdTech team cold outreach
**Purpose**: Generate "Signal Health Reports" for Tier-1 D2C brand prospects
**Status**: ✅ Production-ready MVP
