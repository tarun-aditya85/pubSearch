# Agency & DSP Search - Documentation

## Overview

The Agency and DSP Search modules extend pubSearch to identify, rank, and provide actionable recommendations for advertising agencies and Demand-Side Platforms (DSPs) based on comprehensive quality metrics.

## Architecture

```
Publisher Domain Input
    ↓
Crawler Service (network interception + ads.txt)
    ↓
┌─────────────────────┬───────────────────────┐
│  Agency Search      │    DSP Search         │
│  Service            │    Service            │
└──────┬──────────────┴────────┬──────────────┘
       │                       │
   ┌───▼────┐             ┌───▼────┐
   │ Ranker │             │ Ranker │
   └───┬────┘             └───┬────┘
       │                      │
    Ranked                 Ranked
    Agencies               DSPs
```

## Agency Search

### Ranking Factors

Agencies are scored 0-100 based on three dimensions:

#### 1. Market Presence (30% weight)
- **Excellent (100)**: 1000+ publishers represented
- **Good (80)**: 500-999 publishers
- **Average (60)**: 100-499 publishers
- **Poor (40)**: 10-99 publishers
- **Minimal (20)**: <10 publishers

**Why it matters**: Higher market presence indicates established operations, better fill rates, and proven demand relationships.

#### 2. Transparency (30% weight)
- **sellers.json exists**: +50 points
- **Premium agency (Google, Magnite, PubMatic, etc.)**: +20 points
- **TAG certification**: +30 points

**Why it matters**: Transparency correlates with compliance, fraud prevention, and trustworthiness. TAG-certified agencies follow industry best practices.

#### 3. Tech Sophistication (40% weight)
- **Base score**: 50 points
- **S2S (server-side) support**: +25 points
- **Header bidding capable**: +25 points

**Why it matters**: Modern tech capabilities enable better monetization, faster page loads, and more control over data.

### Opportunity Scoring

Opportunity score (0-100) indicates potential for improvement:

- **High opportunity (70-100)**: Low quality but high potential for upgrades
- **Medium opportunity (40-69)**: Room for improvement
- **Low opportunity (0-39)**: Already optimized or limited upside

**Special rules**:
- RESELLER relationships have 50% lower opportunity (you don't control them directly)
- Low tech sophistication scores boost opportunity (+20 points)

### Known Premium Agencies (Tier 1)

- Google Ad Manager (`google.com`)
- Magnite/Rubicon Project (`rubiconproject.com`)
- OpenX (`openx.com`)
- PubMatic (`pubmatic.com`)
- Index Exchange (`indexexchange.com`)
- Xandr/AppNexus (`appnexus.com`)
- Criteo (`criteo.com`)
- Amazon Publisher Services (`amazon-adsystem.com`)
- Sovrn (`sovrn.com`)
- TripleLift (`triplelift.com`)

### Recommended Actions

Based on quality and opportunity scores, the system recommends:

- **Maintain** (quality ≥80): High-quality, keep as-is
- **Upgrade** (opportunity ≥70, DIRECT): Enable S2S/header bidding
- **Replace** (opportunity ≥70, RESELLER): Switch to better direct relationship
- **Review** (quality <50): Audit performance, consider alternatives
- **Monitor** (default): Track and reassess quarterly

---

## DSP Search

### Ranking Factors

DSPs are scored 0-100 based on three dimensions:

#### 1. Quality (30% weight)
Averaged from three sub-scores:

**a. Market Share Score**
- Tier 1 DSPs (Google DV360, The Trade Desk, Amazon DSP): 85-95
- Tier 2 DSPs (Adform, Criteo, Beeswax): 62-80
- SSP/DSP hybrids (Magnite, PubMatic): 75
- Unknown DSPs: 50 (average)

**b. Performance Score**
- Tier 1: 90 (proven high performance)
- Tier 2: 75 (solid performance)
- Based on request volume for unknown DSPs

**c. Reliability Score**
- Base: 70
- Tier 1 DSPs: 95 (proven uptime)
- Integrated in ads.txt: +10 (indicates trust)

#### 2. Performance (40% weight)
In production, would analyze:
- Bid response rate
- Win rate
- Average eCPM
- Fill rate

#### 3. Opportunity (30% weight)
- **Not integrated + high quality** = high opportunity
- **Already integrated** = low opportunity (max 30%)
- **Tier 1 DSP not integrated** = +20 bonus

### Detection Methods

DSPs are discovered through three sources:

1. **ads.txt**: Declared DSP relationships (most reliable)
2. **Network requests**: Active DSP bid calls detected during crawl
3. **Prebid.js config**: Header bidding DSPs configured in JavaScript

### Known Tier 1 DSPs

| DSP | Domain | Ad Formats | Market Share |
|-----|--------|------------|--------------|
| Google Display & Video 360 | `google.com` | Display, Video, Native | 95 |
| The Trade Desk | `thetradedesk.com` | Display, Video, Native, CTV | 90 |
| Amazon DSP | `amazon-adsystem.com` | Display, Video | 85 |
| Xandr (Microsoft) | `appnexus.com` | Display, Video, Native | 88 |
| MediaMath | `mediamath.com` | Display, Video | 75 |

### Known Tier 2 DSPs

- Adform (`adform.com`) - 70%
- Criteo (`criteo.com`) - 80%
- Beeswax (`beeswax.com`) - 65%
- StackAdapt (`stackadapt.com`) - 68%
- Basis Technologies (`basis.net`) - 62%

### Revenue Uplift Estimation

For non-integrated DSPs, estimated revenue uplift is calculated as:

```
Base Uplift = (Quality Score + Opportunity Score) / 10
Capped at 30% per DSP
```

**Example**:
- Quality Score: 90
- Opportunity Score: 85
- Revenue Uplift: (90 + 85) / 10 = 17.5% ≈ **18% increase**

### Integration Complexity

- **Already integrated**: No additional work needed
- **Easy**: Tier 1 DSPs (good documentation, proven integrations)
- **Medium**: Tier 2 DSPs (some documentation, moderate effort)
- **Hard**: Unknown DSPs (limited docs, higher risk)

### Recommended Actions

- **Integrate** (not integrated, opportunity ≥70): High-value addition
- **Optimize** (integrated, quality ≥80): Increase bid density
- **Review** (integrated, quality <80): Audit performance, consider pausing
- **Consider** (not integrated, quality ≥70): Test in limited capacity
- **Skip** (quality <70): Focus on higher-quality DSPs first

---

## API Usage

### Agency Search

**Endpoint**: `POST /search/agencies`

**Request**:
```json
{
  "publisher_domain": "example.com",
  "min_quality_score": 50
}
```

**Response**:
```json
{
  "publisher_domain": "example.com",
  "timestamp": "2026-04-30T...",
  "total_agencies_found": 8,
  "direct_relationships": 2,
  "reseller_relationships": 6,
  "agencies": [
    {
      "agency_name": "Google Ad Manager",
      "seller_domain": "google.com",
      "relationship": "DIRECT",
      "quality_score": 95,
      "market_presence_score": 100,
      "transparency_score": 100,
      "tech_sophistication_score": 100,
      "total_publishers_represented": 50000,
      "has_sellers_json": true,
      "supports_s2s": true,
      "header_bidding_capable": true,
      "opportunity_score": 5,
      "recommended_action": "Maintain: High-quality agency performing well"
    }
  ],
  "top_opportunities": [...],
  "overall_agency_quality": 82,
  "has_premium_agencies": true,
  "diversification_score": 80,
  "recommendations": [
    "Increase direct relationships: Target 3-5 direct agency partnerships"
  ]
}
```

### DSP Search

**Endpoint**: `POST /search/dsps`

**Request**:
```json
{
  "publisher_domain": "example.com",
  "min_quality_score": 60,
  "category_filter": null
}
```

**Response**:
```json
{
  "publisher_domain": "example.com",
  "timestamp": "2026-04-30T...",
  "total_dsps_found": 12,
  "currently_integrated": 4,
  "potential_additions": 8,
  "dsps": [
    {
      "dsp_name": "The Trade Desk",
      "dsp_domain": "thetradedesk.com",
      "detected_via": "network_request",
      "is_currently_integrated": false,
      "quality_score": 90,
      "market_share_score": 90,
      "performance_score": 90,
      "reliability_score": 95,
      "ad_formats": ["display", "video", "native", "ctv"],
      "header_bidding_integration": true,
      "deals_marketplace": true,
      "opportunity_score": 90,
      "estimated_revenue_uplift_pct": 18,
      "integration_complexity": "easy",
      "recommended_action": "Integrate: High-quality DSP with 18% revenue potential"
    }
  ],
  "top_opportunities": [...],
  "overall_dsp_quality": 75,
  "portfolio_diversification": 60,
  "header_bidding_coverage": 75,
  "estimated_total_revenue_uplift_pct": 35,
  "by_format": {
    "display": 12,
    "video": 8,
    "native": 6
  },
  "recommendations": [
    "Add Tier 1 DSP: Integrate Google DV360, The Trade Desk, or Amazon DSP",
    "Enable header bidding: Only 75% of DSPs support HB"
  ]
}
```

---

## Business Use Cases

### 1. Pre-Sales Competitive Analysis

**Scenario**: You're pitching a D2C brand that currently works with 3 small agencies.

**Action**:
```bash
curl -X POST http://localhost:8000/search/agencies \
  -H "Content-Type: application/json" \
  -d '{"publisher_domain": "target-brand.com"}'
```

**Output**: Show prospect they're missing 5 Tier 1 agencies, costing them 25% revenue uplift.

### 2. DSP Portfolio Optimization

**Scenario**: Existing client wants to maximize header bidding revenue.

**Action**:
```bash
curl -X POST http://localhost:8000/search/dsps \
  -H "Content-Type: application/json" \
  -d '{"publisher_domain": "client.com", "min_quality_score": 70}'
```

**Output**: Identify top 3 non-integrated DSPs with 30% total uplift potential.

### 3. Quarterly Agency Review

**Scenario**: Audit current agency partners for performance.

**Action**: Run agency search, filter by `quality_score < 60`, generate replacement recommendations.

### 4. Vertical-Specific DSP Recommendations

**Scenario**: Video publisher wants to add video-focused DSPs.

**Action**: Run DSP search with `category_filter: "video"`, rank by format support.

---

## Customization

### Custom Ranking Criteria

**Agency Search**:
```python
from app.services.agency_search.schemas import AgencyRankingCriteria

criteria = AgencyRankingCriteria(
    min_publisher_count=100,
    require_sellers_json=True,
    require_certification=True,
    prefer_s2s_capable=True,
    market_presence_weight=0.5,  # Emphasize market presence
    transparency_weight=0.3,
    tech_sophistication_weight=0.2
)
```

**DSP Search**:
```python
from app.services.dsp_search.schemas import DSPRankingCriteria

criteria = DSPRankingCriteria(
    min_quality_score=70,
    require_header_bidding=True,
    require_brand_safety=True,
    preferred_formats=["video", "ctv"],
    quality_weight=0.4,
    performance_weight=0.3,
    opportunity_weight=0.3
)
```

---

## Testing

```bash
# Test agency search
python test_agency_dsp_search.py

# Or via API
curl -X POST http://localhost:8000/search/agencies \
  -H "Content-Type: application/json" \
  -d '{"publisher_domain": "nytimes.com"}'

curl -X POST http://localhost:8000/search/dsps \
  -H "Content-Type: application/json" \
  -d '{"publisher_domain": "techcrunch.com"}'
```

---

## Future Enhancements

### Agency Search
- **Real-time sellers.json harvesting**: Query actual sellers.json endpoints
- **Historical performance tracking**: Store agency performance over time
- **Fraud detection**: Flag agencies with suspicious patterns
- **Contract optimization**: Recommend better deal terms based on benchmarks

### DSP Search
- **Live bid data integration**: Real eCPM, win rate, fill rate from SSPs
- **A/B testing recommendations**: Which DSPs to test first
- **Yield optimization**: Automatic floor price recommendations per DSP
- **Budget allocation**: ML-based budget distribution across DSPs

---

**Version**: 1.0.0  
**Date**: April 30, 2026
