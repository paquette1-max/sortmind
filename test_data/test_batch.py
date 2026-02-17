#!/usr/bin/env python3
"""
Batch Ollama Test with Progress
==============================

Tests Ollama LLM on multiple documents with progress reporting.
"""

import json
import requests
import re
from pathlib import Path
from datetime import datetime

def analyze_file(file_path: Path, model: str = "llama3.2:3b") -> dict:
    """Analyze a single file with Ollama."""
    content = file_path.read_text()[:2500]
    
    prompt = f"""Analyze this document. Respond ONLY with JSON:

DOCUMENT:
{content}

JSON format:
{{
    "document_type": "Bank Statement/Medical Bill/Utility Bill/Tax Document/Credit Card Statement/Other",
    "vendor_or_institution": "Main company/bank/hospital name",
    "date": "YYYY-MM-DD",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation"
}}"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        # Parse JSON from response
        text = result.get("response", "")
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return {"error": "No JSON found", "raw": text}
    except Exception as e:
        return {"error": str(e)}

# Load manifest
test_dir = Path(__file__).parent / "scansnap_test_data"
manifest_path = test_dir / "MANIFEST.txt"

manifest = {}
current_file = None
with open(manifest_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("File: "):
            current_file = line.replace("File: ", "").strip()
            manifest[current_file] = {}
        elif current_file and line.startswith("Expected Type: "):
            manifest[current_file]["type"] = line.replace("Expected Type: ", "").strip()
        elif current_file and line.startswith("Source: "):
            manifest[current_file]["vendor"] = line.replace("Source: ", "").strip()
        elif current_file and line.startswith("Date: "):
            manifest[current_file]["date"] = line.replace("Date: ", "").strip()

print("="*70)
print("OLLAMA BATCH TEST")
print("="*70)
print(f"Testing {len(manifest)} documents with llama3.2:3b")
print()

results = []
for i, (filename, expected) in enumerate(manifest.items(), 1):
    print(f"[{i}/{len(manifest)}] {filename}...", flush=True)
    
    file_path = test_dir / filename
    result = analyze_file(file_path)
    
    detected_type = result.get("document_type", "unknown")
    confidence = result.get("confidence", 0)
    
    # Check if type matches
    expected_type = expected.get("type", "").lower()
    detected_lower = detected_type.lower()
    matches = any(word in detected_lower for word in expected_type.split() if len(word) > 2)
    
    status = "✓" if matches else "✗"
    print(f"  {status} {detected_type} (conf: {confidence:.2f})")
    
    results.append({
        "file": filename,
        "expected_type": expected.get("type"),
        "detected_type": detected_type,
        "detected_vendor": result.get("vendor_or_institution"),
        "detected_date": result.get("date"),
        "confidence": confidence,
        "matches": matches,
    })
    print()

# Summary
print("="*70)
print("SUMMARY")
print("="*70)
total = len(results)
correct = sum(1 for r in results if r["matches"])
print(f"Correct: {correct}/{total} ({correct/total*100:.1f}%)")
print()

for r in results:
    status = "✓" if r["matches"] else "✗"
    print(f"{status} {r['file']}: {r['detected_type']} (expected: {r['expected_type']})")

# Save results
output = Path(__file__).parent / "ollama_batch_results.json"
with open(output, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {output}")
