"""ads.txt validation analyzer."""

import logging

logger = logging.getLogger(__name__)


class AdsTxtAnalyzer:
    """Analyzer for ads.txt compliance."""

    def validate(self, ads_txt_content: str | None) -> bool:
        """
        Validate ads.txt content according to IAB spec.

        Format: domain, publisher_id, relationship_type, certification_id (optional)
        Example: google.com, pub-123456789, DIRECT, f08c47fec0942fa0

        Args:
            ads_txt_content: Raw ads.txt file content

        Returns:
            True if valid ads.txt with at least one valid entry exists
        """
        if not ads_txt_content:
            return False

        valid_entries = 0
        lines = ads_txt_content.split("\n")

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Split by comma or tab
            parts = [p.strip() for p in line.replace("\t", ",").split(",")]

            # Valid entry must have at least 3 fields
            if len(parts) >= 3:
                domain, publisher_id, relationship = parts[0], parts[1], parts[2]

                # Basic validation
                if (
                    domain
                    and publisher_id
                    and relationship.upper() in ["DIRECT", "RESELLER"]
                    and "." in domain
                ):
                    valid_entries += 1

        logger.info(f"Found {valid_entries} valid ads.txt entries")
        return valid_entries > 0
