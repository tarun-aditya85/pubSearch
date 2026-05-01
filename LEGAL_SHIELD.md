# Legal & Ethical Guidelines for pubSearch

## Purpose

pubSearch is an **automated audit tool** designed for passive reconnaissance of publicly accessible web publisher properties. It identifies security vulnerabilities and revenue monetization opportunities through **non-intrusive scanning**.

## Scanning Methodology

### What We Do

1. **Passive Observation**: We access only publicly available resources:
   - Published web pages
   - Public ads.txt files (IAB standard)
   - Client-side JavaScript files served to all visitors
   - Publicly observable HTTP/HTTPS network requests

2. **Detection, Not Exploitation**: We identify potential issues but **never**:
   - Exploit vulnerabilities
   - Access unauthorized systems or data
   - Attempt credential stuffing or authentication bypass
   - Perform denial-of-service attacks
   - Exfiltrate private user data

3. **Respectful Crawling**:
   - Clear User-Agent identification: `pubSearch-Audit-Bot/1.0; +https://audit.pubsearch.io/info`
   - Rate limiting to avoid server overload
   - Single page visit per domain (not exhaustive crawling)
   - Respect robots.txt directives where applicable

## Data Collection & Privacy

### What We Collect

- **Network request metadata**: URLs, domains, request types
- **Public JavaScript files**: For API key exposure detection
- **Cookie attributes**: Flags (HttpOnly, Secure), not values
- **ads.txt content**: Public IAB-compliant file

### What We DO NOT Collect

- User passwords or authentication tokens
- Private user data or profiles
- Session identifiers or authentication cookies
- Payment card information (PCI data)
- Personal health information (PHI)

### PII Detection

When our tool detects **potential PII leakage** (emails, phone numbers in URL parameters), we:
- Flag the detection pattern without storing the actual PII value
- Report only the parameter name and target domain
- **Do not log, store, or transmit** the detected PII itself

## Compliance Considerations

### GDPR (EU General Data Protection Regulation)

- No personal data of EU citizens is collected or processed
- Detection of PII in transit is logged as a security finding, not stored as data
- Publishers retain full control over their public web properties

### CCPA (California Consumer Privacy Act)

- No consumer personal information is sold or shared
- Detection is performed on publicly accessible business data only

### Computer Fraud and Abuse Act (CFAA) - US

- All access is to publicly available resources
- No unauthorized access to protected systems
- No circumvention of authentication or access controls

## Authorized Use Cases

### ✅ Permitted Uses

1. **Self-Assessment**: Publishers scanning their own properties
2. **Pre-Sales Security Audits**: With explicit permission from target publisher
3. **Third-Party AdTech Review**: As part of legitimate business due diligence
4. **Educational/Research**: Security research with proper disclosure

### ❌ Prohibited Uses

1. Scanning domains without authorization for malicious purposes
2. Using detected vulnerabilities for exploitation
3. Selling or publicly disclosing detailed vulnerability findings without consent
4. Competitive intelligence gathering with intent to harm

## Responsible Disclosure

If you use pubSearch and discover a **critical security vulnerability** (e.g., exposed production API keys), we encourage:

1. **Notify the publisher immediately** through their security contact
2. **Allow 90 days** for remediation before public disclosure
3. **Do not exploit** the vulnerability for unauthorized access

## Contact & Attribution

- **Project**: pubSearch AdTech Audit Engine
- **Purpose**: Security and monetization assessment for digital publishers
- **Contact**: audit@pubsearch.io (fictional - replace with actual contact)
- **Website**: https://audit.pubsearch.io/info (fictional - replace with actual URL)

## Disclaimer

This tool is provided "as is" for security assessment purposes. Users are responsible for ensuring their use complies with all applicable laws and regulations in their jurisdiction. The developers assume no liability for misuse or unauthorized scanning activities.

---

**Last Updated**: April 2026
**Version**: 1.0.0
