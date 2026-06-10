#!/usr/bin/env python3
"""
DAI Health Diagnostic Runner
Executes digital health analysis for a prospect and sends callback with results.
"""

import argparse
import json
import re
import os
import sys
import httpx
from pathlib import Path


def extract_score_from_html(html_path: Path) -> dict:
    """Extract score, grade and opportunities from existing health report."""
    content = html_path.read_text(encoding="utf-8")

    # Extract total score
    score_match = re.search(r'class="score-number">(\d+)<', content)
    score = int(score_match.group(1)) if score_match else 0

    # Extract grade
    grade_match = re.search(r'class="score-grade-badge">Grade\s+([A-D])', content)
    grade = grade_match.group(1) if grade_match else "D"

    # Extract opportunity titles
    opp_matches = re.findall(r'class="opportunity-title">[^<]*?([A-ZÀ-Ú][^<]+)<\/div>', content)
    # Clean emoji prefixes
    opportunities = []
    for o in opp_matches:
        # Remove leading emoji characters
        cleaned = re.sub(r'^[\U00010000-\U0010ffff\u2000-\u3300\U0001F300-\U0001F9FF]+\s*', '', o.strip())
        if cleaned:
            opportunities.append(cleaned)

    return {"score": score, "grade": grade, "opportunities": opportunities}


def send_callback(callback_url: str, payload: dict) -> bool:
    """Send callback with diagnostic results."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(callback_url, json=payload)
            return response.status_code < 400
    except Exception as e:
        print(f"[WARN] Callback failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="DAI Digital Health Diagnostic")
    parser.add_argument("--slug", required=True, help="Prospect slug")
    parser.add_argument("--ig-handle", default="", help="Instagram handle")
    parser.add_argument("--website-url", required=True, help="Website URL")
    parser.add_argument("--brand-name", required=True, help="Brand name")
    parser.add_argument("--city", default="", help="City")
    parser.add_argument("--sector", default="", help="Sector")
    parser.add_argument("--callback-url", required=True, help="Callback webhook URL")
    args = parser.parse_args()

    # Determine report path
    base_dir = Path(__file__).parent / "prospects" / f"{args.slug}-health"
    report_path = base_dir / "index.html"

    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)

    # Extract data from existing report if available
    if report_path.exists():
        print(f"[INFO] Found existing health report at {report_path}", flush=True)
        data = extract_score_from_html(report_path)
        score = data["score"]
        grade = data["grade"]
        opportunities = data["opportunities"]
    else:
        print(f"[ERROR] No health report found at {report_path}", file=sys.stderr)
        print("[INFO] Please create the health report first using the template.", file=sys.stderr)
        sys.exit(1)

    # Build public URL
    public_url = f"https://{args.slug}-health.digital-ai.tech"

    # Build callback payload
    payload = {
        "score": score,
        "grade": grade,
        "opportunities": opportunities,
        "url": public_url,
        "slug": args.slug,
        "brand_name": args.brand_name,
        "city": args.city,
        "sector": args.sector,
        "ig_handle": args.ig_handle,
        "website_url": args.website_url,
    }

    # Output result JSON
    result = {"score": score, "grade": grade, "opportunities": opportunities, "url": public_url}
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)

    # Send callback
    print(f"[INFO] Sending callback to {args.callback_url}", flush=True)
    success = send_callback(args.callback_url, payload)
    if success:
        print("[OK] Callback sent successfully.", flush=True)
    else:
        print("[WARN] Callback may not have been received — check webhook.", flush=True)


if __name__ == "__main__":
    main()
