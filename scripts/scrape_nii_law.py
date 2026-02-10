#!/usr/bin/env python3
"""
Scraper for Israeli National Insurance Law (חוק הביטוח הלאומי, נוסח משולב, תשנ"ה-1995)
Fetches law text from Israeli legal databases and extracts key provisions.

Sources:
1. Nevo (nevo.co.il) - Primary Israeli legal database
2. Israeli Knesset website (knesset.gov.il)
3. National Insurance Institute (btl.gov.il)
4. Wikisource Hebrew (he.wikisource.org)

Usage:
    python3 scrape_nii_law.py

Output:
    ../data/stream_2_new_law_scraped.json
"""

import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("WARNING: 'requests' not installed. Run: pip3 install requests")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("WARNING: 'beautifulsoup4' not installed. Run: pip3 install beautifulsoup4")


OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "stream_2_new_law_scraped.json"

# ===================== SOURCES CONFIGURATION =====================

SOURCES = {
    "nevo_main": {
        "url": "https://www.nevo.co.il/law_html/law01/044_001.htm",
        "description": "Nevo: חוק הביטוח הלאומי נוסח משולב תשנ\"ה-1995 - Main law text",
        "type": "law"
    },
    "nevo_chapter1": {
        "url": "https://www.nevo.co.il/law_html/law01/044_002.htm",
        "description": "Nevo: פרק א - פרשנות (Chapter 1 - Interpretation/Definitions)",
        "type": "law"
    },
    "nevo_chapter_gimmel": {
        "url": "https://www.nevo.co.il/law_html/law01/044_004.htm",
        "description": "Nevo: פרק ג - ביטוח (Chapter 3 - Insurance)",
        "type": "law"
    },
    "wikisource": {
        "url": "https://he.wikisource.org/wiki/%D7%97%D7%95%D7%A7_%D7%94%D7%91%D7%99%D7%98%D7%95%D7%97_%D7%94%D7%9C%D7%90%D7%95%D7%9E%D7%99_(%D7%A0%D7%95%D7%A1%D7%97_%D7%9E%D7%A9%D7%95%D7%9C%D7%91)",
        "description": "Wikisource: חוק הביטוח הלאומי (נוסח משולב)",
        "type": "law"
    },
    "btl_insurance_branches": {
        "url": "https://www.btl.gov.il/Insurance/National_Insurance/Pages/default.aspx",
        "description": "BTL: Insurance branches overview",
        "type": "official_site"
    },
    "btl_who_insured": {
        "url": "https://www.btl.gov.il/Insurance/National_Insurance/Who_is_insured/Pages/default.aspx",
        "description": "BTL: Who is insured (מי מבוטח)",
        "type": "official_site"
    },
    "btl_contributions": {
        "url": "https://www.btl.gov.il/Insurance/National_Insurance/Amounts/Pages/default.aspx",
        "description": "BTL: Contribution rates (שיעורי דמי ביטוח)",
        "type": "official_site"
    },
    "knesset_law": {
        "url": "https://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawPrimary.aspx?t=lawlaws&st=lawlaws&lawitemid=2000559",
        "description": "Knesset: National Insurance Law entry",
        "type": "law"
    },
    # Regulations
    "takanot_workers_territories": {
        "url": "https://www.nevo.co.il/law_html/law01/044_045.htm",
        "description": "תקנות ביטוח לאומי (ביטוח בפני פגיעה בעבודה של עובדים בשטחים המוחזקים)",
        "type": "regulation"
    },
    "takanot_foreign_workers": {
        "url": "https://www.nevo.co.il/law_html/law01/044_069.htm",
        "description": "תקנות ביטוח לאומי (עובדים זרים)",
        "type": "regulation"
    },
    "takanot_residence": {
        "url": "https://www.nevo.co.il/law_html/law01/044_015.htm",
        "description": "תקנות ביטוח לאומי (קביעת תושבות)",
        "type": "regulation"
    },
}

# ===================== KEY SECTIONS TO EXTRACT =====================

KEY_SECTIONS = [
    # Section numbers from the 1995 consolidated law
    "סעיף 1",     # Definitions (הגדרות)
    "סעיף 2",     # Definition of resident (תושב)
    "סעיף 3",     # Definition of insured (מבוטח)
    "סעיף 4",     # Who is a worker (עובד)
    "סעיף 5",     # Self-employed (עובד עצמאי)
    "סעיף 6",     # Insurance of residents (ביטוח תושבים)
    "סעיף 7",     # Insurance of non-residents
    "סעיף 8",     # Voluntary insurance
    "סעיף 9",     # Insurance branches
    "סעיף 10",    # Exemptions
    "סעיף 11",    # Territorial application
    "סעיף 13",    # Classification of insured persons
    "סעיף 14",    # Contribution rates
    "סעיף 15",    # Employer contributions
    "סעיף 16",    # Worker contributions
    "סעיף 40",    # Work injury insurance applicability
    "סעיף 75",    # Old-age and survivors
    "סעיף 196",   # General insurance
    "סעיף 197",   # Income thresholds
    "סעיף 340",   # Application to territories
    "סעיף 378",   # Extension provisions
    "סעיף 379",   # Regulations power
    "סעיף 380",   # Transitional provisions
]

SEARCH_PATTERNS = [
    r'(?:מבוטח|מבוטחים)',
    r'(?:תושב|תושבת|תושבי|תושבות)',
    r'(?:עובד|עובדת|עובדים)',
    r'(?:עובד\s*עצמאי)',
    r'(?:עובד\s*זר|עובדים\s*זרים)',
    r'(?:שטח|שטחים|יהודה\s*ושומרון|איזור)',
    r'(?:ענפי\s*ביטוח|ענף\s*ביטוח)',
    r'(?:דמי\s*ביטוח)',
    r'(?:תחולה)',
    r'(?:ריבונות)',
]


def fetch_url(url, timeout=30):
    """Fetch a URL and return the response text."""
    if not HAS_REQUESTS:
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'he,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout, verify=True)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def extract_text_from_html(html):
    """Extract clean text from HTML, preserving structure."""
    if not HAS_BS4 or not html:
        return html or ""

    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link"]):
        script.decompose()

    # Get text with newlines preserved
    text = soup.get_text(separator='\n', strip=True)

    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def extract_sections(text, section_ids):
    """Extract specific sections from law text."""
    sections = {}
    for sec_id in section_ids:
        # Try various patterns for section references
        patterns = [
            rf'({sec_id}[\.\s].*?)(?=סעיף\s+\d+|$)',
            rf'({re.escape(sec_id)}.*?)(?=\n\s*סעיף|\Z)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                sections[sec_id] = match.group(1).strip()[:2000]  # Limit length
                break
    return sections


def search_patterns_in_text(text, patterns):
    """Search for key patterns and extract surrounding context."""
    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 200)
            context = text[start:end].strip()
            results.append({
                "pattern": pattern,
                "match": match.group(),
                "context": context
            })
    return results


def scrape_all():
    """Main scraping function."""
    results = {
        "stream": "stream_2_new_law",
        "status": "partial",
        "scrape_timestamp": datetime.now().isoformat(),
        "sources_attempted": [],
        "sources_succeeded": [],
        "sources_failed": [],
        "raw_texts": {},
        "extracted_sections": {},
        "pattern_matches": {},
        "findings": [],
    }

    if not HAS_REQUESTS or not HAS_BS4:
        print("\n" + "="*60)
        print("MISSING DEPENDENCIES")
        print("="*60)
        print("To run the scraper, install required packages:")
        print("  pip3 install requests beautifulsoup4")
        print("="*60)
        results["status"] = "failed"
        results["error"] = "Missing dependencies: requests and/or beautifulsoup4"
        save_results(results)
        return results

    for source_key, source_info in SOURCES.items():
        url = source_info["url"]
        desc = source_info["description"]
        print(f"\n--- Fetching: {desc}")
        print(f"    URL: {url}")

        results["sources_attempted"].append(source_info)

        html = fetch_url(url)
        if html:
            text = extract_text_from_html(html)
            results["raw_texts"][source_key] = text[:50000]  # Limit storage
            results["sources_succeeded"].append(source_info)
            print(f"    SUCCESS: {len(text)} characters extracted")

            # Extract sections
            sections = extract_sections(text, KEY_SECTIONS)
            if sections:
                results["extracted_sections"][source_key] = sections
                print(f"    Found {len(sections)} key sections")

            # Search patterns
            matches = search_patterns_in_text(text, SEARCH_PATTERNS)
            if matches:
                results["pattern_matches"][source_key] = matches[:100]  # Limit
                print(f"    Found {len(matches)} pattern matches")
        else:
            results["sources_failed"].append(source_info)
            print(f"    FAILED")

    # Determine status
    if len(results["sources_succeeded"]) > 0:
        results["status"] = "partial" if results["sources_failed"] else "completed"
    else:
        results["status"] = "failed"

    # Generate findings summary
    results["findings"] = generate_findings_summary(results)

    save_results(results)
    return results


def generate_findings_summary(results):
    """Generate a human-readable findings summary from scraped data."""
    findings = []

    for source_key, sections in results.get("extracted_sections", {}).items():
        for sec_id, sec_text in sections.items():
            findings.append({
                "topic": f"Section {sec_id} from {source_key}",
                "content": sec_text[:1000],
                "source": SOURCES.get(source_key, {}).get("url", "unknown")
            })

    return findings


def save_results(results):
    """Save results to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Remove raw_texts from the saved file to keep it manageable
    save_data = {k: v for k, v in results.items() if k != "raw_texts"}

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {OUTPUT_FILE}")

    # Also save raw texts separately if they exist
    if results.get("raw_texts"):
        raw_file = OUTPUT_DIR / "stream_2_raw_texts.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(results["raw_texts"], f, ensure_ascii=False, indent=2)
        print(f"Raw texts saved to: {raw_file}")


if __name__ == "__main__":
    print("="*60)
    print("Israeli National Insurance Law Scraper")
    print("חוק הביטוח הלאומי (נוסח משולב), תשנ\"ה-1995")
    print("="*60)

    results = scrape_all()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Status: {results['status']}")
    print(f"Sources attempted: {len(results['sources_attempted'])}")
    print(f"Sources succeeded: {len(results['sources_succeeded'])}")
    print(f"Sources failed: {len(results['sources_failed'])}")
    print(f"Sections extracted: {sum(len(s) for s in results.get('extracted_sections', {}).values())}")
    print(f"Findings: {len(results.get('findings', []))}")
