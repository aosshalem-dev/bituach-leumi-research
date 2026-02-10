#!/usr/bin/env python3
"""
Scraper for the old Israeli National Insurance Law (חוק הביטוח הלאומי, נוסח משולב תשכ"ח-1968)
from nevo.co.il and other Israeli legal databases.

Usage:
    python3 scrape_old_law_nevo.py

Output:
    Saves scraped data to ../data/stream_1_old_law_scraped.json
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

# Try to import requests and BeautifulSoup
try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip3 install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: 'beautifulsoup4' not installed. Run: pip3 install beautifulsoup4")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "stream_1_old_law_scraped.json"

# Key URLs to try for the old National Insurance Law (1968 version)
URLS_TO_TRY = [
    # Nevo - The old law (תשכ"ח-1968) - several possible URL patterns
    {
        "url": "https://www.nevo.co.il/law_html/law01/044_001.htm",
        "description": "Nevo - חוק הביטוח הלאומי נוסח משולב תשכ"ח - page 1",
        "source": "nevo.co.il"
    },
    {
        "url": "https://www.nevo.co.il/law_html/law01/044_002.htm",
        "description": "Nevo - חוק הביטוח הלאומי נוסח משולב תשכ"ח - page 2",
        "source": "nevo.co.il"
    },
    {
        "url": "https://www.nevo.co.il/law_html/law01/044_003.htm",
        "description": "Nevo - חוק הביטוח הלאומי נוסח משולב תשכ"ח - page 3",
        "source": "nevo.co.il"
    },
    # Nevo search for the old law
    {
        "url": "https://www.nevo.co.il/law_word/law01/law-0044.htm",
        "description": "Nevo - חוק הביטוח הלאומי alternative URL",
        "source": "nevo.co.il"
    },
    # WikiSource Hebrew
    {
        "url": "https://he.wikisource.org/wiki/%D7%97%D7%95%D7%A7_%D7%94%D7%91%D7%99%D7%98%D7%95%D7%97_%D7%94%D7%9C%D7%90%D7%95%D7%9E%D7%99_(%D7%A0%D7%95%D7%A1%D7%97_%D7%9E%D7%A9%D7%95%D7%9C%D7%91)",
        "description": "WikiSource - חוק הביטוח הלאומי (נוסח משולב)",
        "source": "he.wikisource.org"
    },
    # Knesset website
    {
        "url": "https://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid=2006893",
        "description": "Knesset - National Insurance Law",
        "source": "knesset.gov.il"
    },
    # Israeli Law Book (ספר החוקים)
    {
        "url": "https://fs.knesset.gov.il/globaldocs/docs/he/law/00/he_law_00008877.pdf",
        "description": "Original law publication in Sefer HaHukim",
        "source": "knesset.gov.il"
    },
    # National Insurance Institute website
    {
        "url": "https://www.btl.gov.il/חוקים%20ותקנות/חוק%20ביטוח%20לאומי/Pages/default.aspx",
        "description": "BTL - חוק ביטוח לאומי",
        "source": "btl.gov.il"
    },
]

# Keywords to search for in scraped content
KEYWORDS = [
    "מבוטח",      # insured
    "תושב",       # resident
    "תושב ישראל", # resident of Israel
    "עובד",        # worker/employee
    "עובד זר",    # foreign worker
    "שטחים",       # territories
    "יהודה ושומרון",  # Judea and Samaria (West Bank)
    "עזה",         # Gaza
    "אזור",        # area/zone (legal term for territories)
    "ענפי ביטוח",  # branches of insurance
    "ביטוח זקנה",  # old age insurance
    "ביטוח נכות",  # disability insurance
    "ביטוח אמהות", # maternity insurance
    "ביטוח ילדים", # children's insurance
    "ביטוח נפגעי עבודה",  # work injury insurance
    "ביטוח אבטלה", # unemployment insurance
    "דמי ביטוח",   # insurance premiums
    "פרק",         # chapter
    "סימן",        # section
    "סעיף 1",      # article 1 (definitions)
    "הגדרות",      # definitions
]


def fetch_url(url, timeout=30):
    """Fetch a URL with proper headers for Hebrew content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, verify=True)
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp
    except Exception as e:
        return {"error": str(e)}


def extract_law_sections(html_content, source_url):
    """Parse HTML and extract relevant law sections."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    results = {
        "full_text_length": len(text),
        "relevant_sections": [],
        "keyword_matches": {},
    }

    # Search for keyword matches with context
    lines = text.split("\n")
    for keyword in KEYWORDS:
        matches = []
        for i, line in enumerate(lines):
            if keyword in line:
                # Get surrounding context (3 lines before and after)
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context = "\n".join(lines[start:end])
                matches.append({
                    "line_number": i,
                    "context": context[:1000],  # Limit context size
                })
        if matches:
            results["keyword_matches"][keyword] = matches[:10]  # Limit to 10 matches per keyword

    # Try to identify chapter/section structure
    chapter_pattern = re.compile(r'(פרק\s+[\u05d0-\u05ea]+[\'"]?\s*[-–:]\s*.+)')
    section_pattern = re.compile(r'(סימן\s+[\u05d0-\u05ea]+[\'"]?\s*[-–:]\s*.+)')
    article_pattern = re.compile(r'(סעיף\s+\d+[\u05d0-\u05ea]?\.?\s*.+)')

    for pattern, label in [(chapter_pattern, "פרק"), (section_pattern, "סימן"), (article_pattern, "סעיף")]:
        for match in pattern.finditer(text):
            start = match.start()
            # Get some context after the match
            context_end = min(start + 500, len(text))
            results["relevant_sections"].append({
                "type": label,
                "header": match.group(1)[:200],
                "context": text[start:context_end],
            })

    return results


def main():
    print("=" * 60)
    print("Scraping Old National Insurance Law (תשכ\"ח-1968)")
    print("=" * 60)

    all_results = {
        "timestamp": datetime.now().isoformat(),
        "urls_attempted": [],
        "successful_scrapes": [],
        "failed_scrapes": [],
        "extracted_data": [],
    }

    for url_info in URLS_TO_TRY:
        url = url_info["url"]
        desc = url_info["description"]
        print(f"\n--- Trying: {desc}")
        print(f"    URL: {url}")

        resp = fetch_url(url)

        if isinstance(resp, dict) and "error" in resp:
            print(f"    FAILED: {resp['error']}")
            all_results["failed_scrapes"].append({
                "url": url,
                "description": desc,
                "error": resp["error"],
            })
            all_results["urls_attempted"].append({"url": url, "status": "error"})
            continue

        if resp.status_code != 200:
            print(f"    FAILED: HTTP {resp.status_code}")
            all_results["failed_scrapes"].append({
                "url": url,
                "description": desc,
                "error": f"HTTP {resp.status_code}",
            })
            all_results["urls_attempted"].append({"url": url, "status": resp.status_code})
            continue

        print(f"    SUCCESS: {len(resp.text)} chars")
        all_results["urls_attempted"].append({"url": url, "status": 200, "size": len(resp.text)})

        # Check if it's a PDF
        if url.endswith(".pdf"):
            all_results["successful_scrapes"].append({
                "url": url,
                "description": desc,
                "note": "PDF file - saved raw. Use a PDF reader to extract text.",
                "content_type": resp.headers.get("Content-Type", "unknown"),
            })
            # Save PDF separately
            pdf_path = OUTPUT_DIR / "old_law_original.pdf"
            with open(pdf_path, "wb") as f:
                f.write(resp.content)
            print(f"    Saved PDF to: {pdf_path}")
            continue

        # Parse HTML
        try:
            extracted = extract_law_sections(resp.text, url)
            all_results["successful_scrapes"].append({
                "url": url,
                "description": desc,
                "extracted": extracted,
            })
            all_results["extracted_data"].append({
                "source": url,
                "data": extracted,
            })
            kw_count = sum(len(v) for v in extracted["keyword_matches"].values())
            print(f"    Extracted: {len(extracted['relevant_sections'])} sections, {kw_count} keyword matches")
        except Exception as e:
            print(f"    PARSE ERROR: {e}")
            all_results["failed_scrapes"].append({
                "url": url,
                "description": desc,
                "error": f"Parse error: {e}",
            })

        # Be polite - wait between requests
        time.sleep(1)

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Successful scrapes: {len(all_results['successful_scrapes'])}")
    print(f"Failed scrapes: {len(all_results['failed_scrapes'])}")
    print(f"{'=' * 60}")

    return all_results


if __name__ == "__main__":
    main()
