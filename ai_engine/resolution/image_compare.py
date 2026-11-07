"""
ai_engine/resolution/image_compare.py
Before/After image comparison for resolution verification.

Usage:
    python image_compare.py --before ./before.jpg --after ./after.jpg
"""

import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.services.vision_service import compare_images


def main(before: str, after: str):
    print(f"Before: {before}")
    print(f"After:  {after}\n")
    result = compare_images(before, after)

    for k, v in result.items():
        print(f"  {k:30s}: {v}")

    # Verdict
    prob = result.get("resolved_probability", 0)
    verdict = "✅ LIKELY RESOLVED" if prob > 0.65 else \
              "⚠️  NEEDS REVIEW"     if prob > 0.40 else \
              "❌ NOT RESOLVED"
    print(f"\n  Verdict: {verdict}  (confidence: {prob:.1%})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after",  required=True)
    args = parser.parse_args()
    main(args.before, args.after)
