"""Security vulnerability analyzer."""

import re
import logging
from app.schemas import Vulnerability
from app.services.crawler import InterceptedRequest, Cookie
from app.core.utils import is_third_party, extract_url_params, is_pii_value

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """Analyzer for security vulnerabilities."""

    # Known tracking domains that should not receive PII
    TRACKING_DOMAINS = [
        "facebook.com",
        "google-analytics.com",
        "doubleclick.net",
        "googlesyndication.com",
        "google.com",
        "analytics.google.com",
        "twitter.com",
        "linkedin.com",
        "pinterest.com",
        "snapchat.com",
        "tiktok.com",
    ]

    # API key patterns
    API_KEY_PATTERNS = {
        "Google Cloud API Key": r"AIza[0-9A-Za-z-_]{35}",
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "Stripe Live Key": r"sk_live_[0-9a-zA-Z]{24,}",
        "Stripe Test Key": r"sk_test_[0-9a-zA-Z]{24,}",
        "GitHub Token": r"gh[pousr]_[0-9a-zA-Z]{36}",
        "SendGrid API Key": r"SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}",
        "Mailgun API Key": r"key-[0-9a-zA-Z]{32}",
        "Twilio Account SID": r"AC[0-9a-f]{32}",
        "PayPal Client ID": r"A[A-Za-z0-9\-_]{80}",
    }

    def analyze(
        self,
        requests: list[InterceptedRequest],
        js_files: list[str],
        cookies: list[Cookie],
        publisher_domain: str,
    ) -> list[Vulnerability]:
        """
        Analyze for security vulnerabilities.

        Args:
            requests: Intercepted network requests
            js_files: JavaScript file contents
            cookies: Browser cookies
            publisher_domain: Publisher's domain

        Returns:
            List of detected vulnerabilities
        """
        vulnerabilities: list[Vulnerability] = []

        # Check for PII leakage
        pii_vulns = self._check_pii_leakage(requests, publisher_domain)
        vulnerabilities.extend(pii_vulns)

        # Check for exposed API keys
        api_key_vulns = self._check_api_keys(js_files)
        vulnerabilities.extend(api_key_vulns)

        # Check for insecure cookies
        cookie_vulns = self._check_cookie_security(cookies, publisher_domain)
        vulnerabilities.extend(cookie_vulns)

        logger.info(f"Found {len(vulnerabilities)} security vulnerabilities")
        return vulnerabilities

    def _check_pii_leakage(
        self, requests: list[InterceptedRequest], publisher_domain: str
    ) -> list[Vulnerability]:
        """Check for PII in URL parameters to third-party domains."""
        vulnerabilities: list[Vulnerability] = []
        detected_leaks: set[str] = set()  # Avoid duplicates

        for request in requests:
            # Only check third-party requests
            if not is_third_party(request.url, publisher_domain):
                continue

            # Check if it's a known tracking domain
            is_tracking_domain = any(
                tracking in request.url.lower() for tracking in self.TRACKING_DOMAINS
            )

            if not is_tracking_domain:
                continue

            # Extract and check URL parameters
            params = extract_url_params(request.url)

            for param_name, param_value in params.items():
                is_pii, pii_type = is_pii_value(param_value)

                if is_pii:
                    # Create unique key to avoid duplicates
                    leak_key = f"{pii_type}:{param_name}"

                    if leak_key not in detected_leaks:
                        detected_leaks.add(leak_key)

                        # Determine target domain
                        from app.core.utils import extract_domain_from_url

                        target_domain = extract_domain_from_url(request.url)

                        vulnerabilities.append(
                            Vulnerability(
                                type="PII_LEAK",
                                severity="high",
                                details=f"Potential {pii_type} leaked in parameter '{param_name}' to {target_domain}",
                            )
                        )

        return vulnerabilities

    def _check_api_keys(self, js_files: list[str]) -> list[Vulnerability]:
        """Scan JavaScript files for hardcoded API keys."""
        vulnerabilities: list[Vulnerability] = []
        detected_keys: set[str] = set()

        for js_content in js_files:
            for key_name, pattern in self.API_KEY_PATTERNS.items():
                matches = re.finditer(pattern, js_content)

                for match in matches:
                    key_value = match.group(0)

                    # Create unique identifier
                    key_id = f"{key_name}:{key_value[:20]}"

                    if key_id not in detected_keys:
                        detected_keys.add(key_id)

                        # Mask the key for display
                        masked_key = key_value[:8] + "..." + key_value[-4:]

                        vulnerabilities.append(
                            Vulnerability(
                                type="API_KEY_EXPOSED",
                                severity="critical",
                                details=f"{key_name} exposed in JavaScript ({masked_key})",
                            )
                        )

        return vulnerabilities

    def _check_cookie_security(
        self, cookies: list[Cookie], publisher_domain: str
    ) -> list[Vulnerability]:
        """Check for insecure cookie configurations."""
        vulnerabilities: list[Vulnerability] = []

        # Only check first-party cookies
        first_party_cookies = [
            c for c in cookies if publisher_domain in c.domain or c.domain.startswith(".")
        ]

        insecure_count = 0
        missing_httponly_count = 0
        missing_secure_count = 0

        for cookie in first_party_cookies:
            # Skip obviously non-sensitive cookies
            if cookie.name.lower() in ["_ga", "_gid", "_fbp", "_gcl_au"]:
                continue

            issues = []

            if not cookie.http_only:
                missing_httponly_count += 1
                issues.append("missing HttpOnly flag")

            if not cookie.secure:
                missing_secure_count += 1
                issues.append("missing Secure flag")

            if issues:
                insecure_count += 1

        # Only report if there are significant issues
        if missing_httponly_count > 0:
            vulnerabilities.append(
                Vulnerability(
                    type="INSECURE_COOKIE",
                    severity="medium",
                    details=f"{missing_httponly_count} first-party cookies missing HttpOnly flag (vulnerable to XSS)",
                )
            )

        if missing_secure_count > 0:
            vulnerabilities.append(
                Vulnerability(
                    type="INSECURE_COOKIE",
                    severity="medium",
                    details=f"{missing_secure_count} first-party cookies missing Secure flag (can be sent over HTTP)",
                )
            )

        return vulnerabilities
