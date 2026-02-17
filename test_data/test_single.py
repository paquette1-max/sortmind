#!/usr/bin/env python3
"""
Quick Ollama Test - Single File
===============================

Tests Ollama LLM on a single document to verify the integration works.
"""

import json
import requests
from pathlib import Path

# Test file
test_file = Path(__file__).parent / "scansnap_test_data" / "Scan_20240508_DOC0001.txt"

print("Testing Ollama LLM on single document...")
print(f"File: {test_file.name}")
print()

# Read content
content = test_file.read_text()[:3000]  # First 3000 chars

prompt = f"""Analyze this document and respond with JSON:

DOCUMENT:
{content}

Respond with JSON:
{{
    "document_type": "type of document",
    "vendor": "company or institution name",
    "date": "date in YYYY-MM-DD format",
    "confidence": 0.0 to 1.0
}}"""

print("Sending to Ollama (llama3.2:3b)...")
print()

try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False,
        },
        timeout=120
    )
    response.raise_for_status()
    result = response.json()
    
    print("✓ Ollama responded!")
    print()
    print("Response:")
    print(result.get("response", "No response"))
    print()
    print(f"Total duration: {result.get('total_duration', 0)/1e9:.2f}s")
    
except Exception as e:
    print(f"✗ Error: {e}")
