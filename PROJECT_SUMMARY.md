# pubSearch: AdTech Security & Monetization Audit Engine

## 🎯 Mission

Automate "Outside-In" audits of digital publishers to identify security vulnerabilities and revenue monetization gaps. Enable a 2-person AdTech team to generate compelling "Signal Health Reports" for cold outreach to Tier-1 D2C brands.

## 📊 What It Does

### Security Audit
- **PII Leakage**: Detects emails/phones leaked to Facebook, Google Analytics, etc.
- **API Key Exposure**: Scans JavaScript for hardcoded keys (Google, AWS, Stripe)
- **Cookie Security**: Flags missing HttpOnly/Secure flags

### Monetization Analysis
- **S2S Bridge Detection**: Identifies missing server-side tracking proxies
- **Header Bidding Audit**: Counts SSP bidders, recommends additions
- **Script Bloat**: Measures 3rd-party script overhead

## 🏗️ Architecture

```
FastAPI Server (port 8000)
    ↓
Scan Orchestrator
    ↓
Playwright Crawler → Network Interception
    ↓
Analysis Engines:
  - ads.txt Validator
  - Security Scanner
  - Monetization Analyzer
    ↓
JSON Report Output
```

## 📁 Project Structure

```
pubSearch/
├── app/
│   ├── main.py              # FastAPI app + routes
│   ├── config.py            # Settings
│   ├── schemas.py           # Pydantic models
│   ├── core/
│   │   ├── browser_pool.py  # Playwright manager
│   │   └── utils.py         # Helpers
│   └── services/
│       ├── crawler.py       # Network interception
│       ├── orchestrator.py  # Scan coordinator
│       └── analyzers/
│           ├── ads_txt.py
│           ├── security.py
│           └── monetization.py
├── requirements.txt
├── LEGAL_SHIELD.md
├── QUICKSTART.md
└── test_scan.py
```

## 🚀 Quick Start

### 1. Activate Environment
```bash
eval "$(/Users/lmv/miniconda3/bin/conda shell.zsh hook)" && conda activate pubsearch
```

### 2. Start Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Test Scan
```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}' | jq .
```

## 💼 Business Use Cases

### 1. Live Demo During Sales Call
- Prospect provides domain
- Run scan in real-time
- Show vulnerabilities and gaps instantly
- Export JSON report for follow-up

### 2. Batch Outreach Campaign
- Load "Top 100 Indian Publishers" list
- Run batch scan overnight
- Filter by `estimated_signal_recovery_pct > 30%`
- Prioritize highest-value targets

### 3. Competitive Intelligence
- Analyze competitor publisher setups
- Identify best practices
- Benchmark SSP adoption rates

## 📈 Sample Output

```json
{
  "domain": "ExampleNews.in",
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
      "opportunity": "Capture 15% more first-party data"
    }
  ],
  "estimated_signal_recovery_pct": 35
}
```

## 🔒 Security & Compliance

- **Passive reconnaissance only** (no exploitation)
- **Public data only** (ads.txt, client-side JS)
- **Respectful crawling** (clear User-Agent, rate limiting)
- **No PII storage** (detection-only)
- **GDPR/CCPA compliant**

See [LEGAL_SHIELD.md](LEGAL_SHIELD.md) for full details.

## 🛠️ Tech Stack

- **Python 3.12** in conda environment `pubsearch`
- **FastAPI** for REST API
- **Playwright** for headless browser automation
- **Pydantic v2** for data validation
- **httpx** for HTTP requests

## ✅ Testing

### Unit Test
```bash
python test_scan.py
```

### API Test
```bash
# Single scan
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"domain": "techcrunch.com"}'

# Batch scan
curl -X POST http://localhost:8000/scan/batch \
  -H "Content-Type: application/json" \
  -d '{"domains": ["example.com", "nytimes.com"]}'
```

## 📝 Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI routes + lifespan |
| `app/services/crawler.py` | Playwright network interception |
| `app/services/orchestrator.py` | Scan coordinator |
| `app/services/analyzers/security.py` | Vulnerability detection |
| `app/services/analyzers/monetization.py` | Revenue gap analysis |
| `LEGAL_SHIELD.md` | Compliance documentation |
| `QUICKSTART.md` | Getting started guide |

## 🎁 What You Get

1. **Production-ready REST API** (FastAPI)
2. **Single + batch domain scanning**
3. **Real-time network interception** (Playwright)
4. **Security vulnerability detection** (PII, API keys, cookies)
5. **Monetization gap analysis** (S2S, header bidding, script bloat)
6. **JSON output format** (ready for automation)
7. **Legal compliance documentation**
8. **Test scripts and examples**

## 🔮 Future Enhancements

- PostgreSQL storage for historical tracking
- Mobile app-ads.txt support
- HTML/PDF report generation
- Grafana dashboard for batch visualizations
- Webhook notifications
- Rate limiting + API authentication

## 👥 Team

Built for a 2-person AdTech team focused on:
- Cold outreach to Tier-1 D2C brands
- Signal health assessments
- Revenue optimization consulting

---

**Status**: ✅ Production-ready MVP  
**Version**: 1.0.0  
**Date**: April 2026
