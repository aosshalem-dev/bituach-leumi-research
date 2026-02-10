#!/usr/bin/env python3
"""
Fetch sources that were blocked for Claude's WebFetch tool.
Saves raw text + metadata (including original URL) to JSON files.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests")
    import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing beautifulsoup4...")
    os.system(f"{sys.executable} -m pip install beautifulsoup4")
    from bs4 import BeautifulSoup

DATA_DIR = Path("/Users/zvishalem/Downloads/bituach_leumi_research/data/raw_fetches")
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "he,en;q=0.9",
}

SOURCES = [
    {
        "id": "wikisource_interim_agreement",
        "url": "https://he.wikisource.org/wiki/%D7%97%D7%95%D7%A7_%D7%99%D7%99%D7%A9%D7%95%D7%9D_%D7%94%D7%A1%D7%9B%D7%9D_%D7%94%D7%91%D7%99%D7%A0%D7%99%D7%99%D7%9D_%D7%91%D7%93%D7%91%D7%A8_%D7%94%D7%92%D7%93%D7%94_%D7%94%D7%9E%D7%A2%D7%A8%D7%91%D7%99%D7%AA_%D7%95%D7%A8%D7%A6%D7%95%D7%A2%D7%AA_%D7%A2%D7%96%D7%94_(%D7%A1%D7%9E%D7%9B%D7%95%D7%99%D7%95%D7%AA_%D7%A9%D7%99%D7%A4%D7%95%D7%98_%D7%95%D7%94%D7%95%D7%A8%D7%90%D7%95%D7%AA_%D7%90%D7%97%D7%A8%D7%95%D7%AA)_(%D7%AA%D7%99%D7%A7%D7%95%D7%A0%D7%99_%D7%97%D7%A7%D7%99%D7%A7%D7%94)",
        "description": "חוק יישום הסכם הביניים - ויקיטקסט (full law text including section 37 NII amendment)",
    },
    {
        "id": "wikisource_nii_law",
        "url": "https://he.wikisource.org/wiki/%D7%97%D7%95%D7%A7_%D7%94%D7%91%D7%99%D7%98%D7%95%D7%97_%D7%94%D7%9C%D7%90%D7%95%D7%9E%D7%99",
        "description": "חוק הביטוח הלאומי - ויקיטקסט (table of contents / full law)",
    },
    {
        "id": "knesset_old_law_page",
        "url": "https://main.knesset.gov.il/Activity/Legislation/Laws/pages/lawprimary.aspx?lawitemid=2000197",
        "description": "חוק הביטוח הלאומי [נוסח משולב], התשכ\"ח-1968 - Knesset legislation page",
    },
    {
        "id": "knesset_new_law_page",
        "url": "https://main.knesset.gov.il/Activity/Legislation/Laws/pages/lawprimary.aspx?lawitemid=2000198",
        "description": "חוק הביטוח הלאומי [נוסח משולב], התשנ\"ה-1995 - Knesset legislation page",
    },
    {
        "id": "knesset_research_nii_foreigners",
        "url": "https://fs.knesset.gov.il/globaldocs/MMM/a0be8d55-f7f7-e411-80c8-00155d010977/2_a0be8d55-f7f7-e411-80c8-00155d010977_11_8948.pdf",
        "description": "מחקר כנסת: זכויות ביטוח לאומי לזרים העובדים בישראל",
    },
    {
        "id": "nevo_interim_agreement_law",
        "url": "https://www.nevo.co.il/law_html/law01/177_006.htm",
        "description": "חוק יישום הסכם הביניים - נבו",
    },
    {
        "id": "kolzchut_nii_palestinian",
        "url": "https://www.kolzchut.org.il/he/%D7%91%D7%99%D7%98%D7%95%D7%97_%D7%9C%D7%90%D7%95%D7%9E%D7%99_%D7%9C%D7%A2%D7%95%D7%91%D7%93%D7%99%D7%9D_%D7%A4%D7%9C%D7%A1%D7%98%D7%99%D7%A0%D7%99%D7%9D",
        "description": "כל-זכות: ביטוח לאומי לעובדים פלסטינים",
    },
    {
        "id": "kolzchut_resident_definition",
        "url": "https://www.kolzchut.org.il/he/%D7%AA%D7%95%D7%A9%D7%91_%D7%99%D7%A9%D7%A8%D7%90%D7%9C",
        "description": "כל-זכות: תושב ישראל - הגדרה",
    },
    {
        "id": "wikipedia_salach_hassan",
        "url": "https://he.wikipedia.org/wiki/%D7%91%D7%92%22%D7%A5_%D7%A1%D7%9C%D7%90%D7%97_%D7%97%D7%A1%D7%9F_%D7%A0%D7%92%D7%93_%D7%94%D7%9E%D7%95%D7%A1%D7%93_%D7%9C%D7%91%D7%99%D7%98%D7%95%D7%97_%D7%9C%D7%90%D7%95%D7%9E%D7%99",
        "description": "בג\"ץ סלאח חסן נגד המוסד לביטוח לאומי - ויקיפדיה",
    },
]


def fetch_and_save(source):
    """Fetch a URL and save raw text + metadata to JSON."""
    source_id = source["id"]
    url = source["url"]
    description = source["description"]

    print(f"\n{'='*60}")
    print(f"Fetching: {source_id}")
    print(f"URL: {url}")

    result = {
        "id": source_id,
        "url": url,
        "description": description,
        "fetch_timestamp": datetime.now().isoformat(),
        "success": False,
        "status_code": None,
        "content_type": None,
        "raw_text": None,
        "extracted_text": None,
        "error": None,
    }

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        result["status_code"] = resp.status_code
        result["content_type"] = resp.headers.get("Content-Type", "")
        result["final_url"] = resp.url

        if resp.status_code == 200:
            if "pdf" in result["content_type"].lower():
                # Save PDF binary separately
                pdf_path = DATA_DIR / f"{source_id}.pdf"
                pdf_path.write_bytes(resp.content)
                result["raw_text"] = f"[PDF saved to {pdf_path}]"
                result["success"] = True
                print(f"  -> PDF saved ({len(resp.content)} bytes)")
            else:
                # Parse HTML
                resp.encoding = resp.apparent_encoding or "utf-8"
                html = resp.text
                result["raw_html_length"] = len(html)

                soup = BeautifulSoup(html, "html.parser")

                # Remove script/style tags
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                # Try to find main content
                main = (
                    soup.find("div", {"id": "mw-content-text"})  # Wikipedia/Wikisource
                    or soup.find("div", {"class": "mw-parser-output"})
                    or soup.find("article")
                    or soup.find("main")
                    or soup.find("div", {"id": "content"})
                    or soup.find("div", {"class": "content"})
                    or soup.body
                )

                if main:
                    text = main.get_text(separator="\n", strip=True)
                    result["extracted_text"] = text
                    result["raw_text"] = text[:50000]  # cap at 50k chars
                    result["success"] = True
                    print(f"  -> OK! Extracted {len(text)} chars")
                else:
                    result["raw_text"] = soup.get_text(separator="\n", strip=True)[:50000]
                    result["success"] = True
                    print(f"  -> OK (no main content found, used full page)")
        else:
            result["error"] = f"HTTP {resp.status_code}"
            print(f"  -> FAILED: HTTP {resp.status_code}")

    except Exception as e:
        result["error"] = str(e)
        print(f"  -> ERROR: {e}")

    # Save to JSON
    out_path = DATA_DIR / f"{source_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def main():
    print("=" * 60)
    print("Fetching blocked sources with Python requests")
    print(f"Output dir: {DATA_DIR}")
    print(f"Sources to fetch: {len(SOURCES)}")
    print("=" * 60)

    results_summary = []
    for source in SOURCES:
        result = fetch_and_save(source)
        results_summary.append({
            "id": source["id"],
            "url": source["url"],
            "success": result["success"],
            "status_code": result["status_code"],
            "text_length": len(result.get("extracted_text") or result.get("raw_text") or ""),
            "error": result.get("error"),
        })

    # Save summary
    summary_path = DATA_DIR / "_fetch_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": len(SOURCES),
            "successful": sum(1 for r in results_summary if r["success"]),
            "failed": sum(1 for r in results_summary if not r["success"]),
            "results": results_summary,
        }, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("SUMMARY:")
    for r in results_summary:
        status = "OK" if r["success"] else "FAIL"
        print(f"  [{status}] {r['id']}: HTTP {r['status_code']}, {r['text_length']} chars")
    print(f"\nTotal: {sum(1 for r in results_summary if r['success'])}/{len(SOURCES)} successful")
    print(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
