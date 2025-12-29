"""Tests for SEC EDGAR service."""

import pytest
from app.services.edgar import EdgarClient, SECTION_PATTERNS


def test_section_patterns_valid():
    """Verify all section patterns are valid regex."""
    import re
    for name, pattern in SECTION_PATTERNS.items():
        try:
            re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            pytest.fail(f"Invalid regex for {name}: {e}")


def test_section_patterns_match_expected():
    """Test section patterns match expected text."""
    import re

    test_cases = [
        ("Business", "ITEM 1. BUSINESS"),
        ("Business", "ITEM 1 - BUSINESS"),
        ("Risk Factors", "ITEM 1A. RISK FACTORS"),
        ("Risk Factors", "ITEM 1A - RISK FACTORS"),
        ("MD&A", "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS"),
        ("MD&A", "ITEM 7 - MANAGEMENT'S DISCUSSION"),
    ]

    for section_name, test_text in test_cases:
        pattern = SECTION_PATTERNS[section_name]
        match = re.search(pattern, test_text, re.IGNORECASE)
        assert match is not None, f"Pattern for {section_name} should match '{test_text}'"


@pytest.mark.asyncio
async def test_edgar_client_initialization():
    """Test EDGAR client can be initialized."""
    client = EdgarClient()
    assert client.BASE_URL == "https://data.sec.gov"
    await client.close()
