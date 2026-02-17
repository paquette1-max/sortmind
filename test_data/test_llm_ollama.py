#!/usr/bin/env python3
"""
LLM Document Analysis Test Runner - Ollama Integration
======================================================

Tests the File Organizer using actual Ollama LLM calls with document content.
Improved extraction logic for vendor and date detection.

Usage:
    python3 test_llm_ollama.py
    python3 test_llm_ollama.py --model llama3.1:8b --verbose
"""

import json
import argparse
import requests
import re
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResult:
    """Result of a single document analysis test."""
    filename: str
    expected_type: str
    expected_vendor: str
    expected_date: str
    
    # LLM results
    detected_type: str = ""
    detected_vendor: str = ""
    detected_date: str = ""
    suggested_path: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    
    # Test outcome
    type_correct: bool = False
    vendor_correct: bool = False
    date_correct: bool = False
    overall_success: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "filename": self.filename,
            "expected": {
                "type": self.expected_type,
                "vendor": self.expected_vendor,
                "date": self.expected_date,
            },
            "detected": {
                "type": self.detected_type,
                "vendor": self.detected_vendor,
                "date": self.detected_date,
                "suggested_path": self.suggested_path,
                "confidence": self.confidence,
                "reasoning": self.reasoning,
            },
            "correct": {
                "type": self.type_correct,
                "vendor": self.vendor_correct,
                "date": self.date_correct,
                "overall": self.overall_success,
            }
        }


class OllamaDocumentAnalyzer:
    """Analyzes documents using Ollama LLM."""
    
    def __init__(self, model: str = "llama3.2:3b", url: str = "http://localhost:11434"):
        self.model = model
        self.url = url
        
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a file using Ollama LLM."""
        content = file_path.read_text()
        
        # Truncate if too long (Ollama context limit)
        max_chars = 4000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n...[content truncated]"
        
        prompt = f"""You are a document analysis system. Analyze this scanned document and extract key information.

DOCUMENT CONTENT:
---
{content}
---

Respond ONLY with a JSON object in this exact format:
{{
    "document_type": "One of: Bank Statement, Medical Bill, Utility Bill, Tax Document, Credit Card Statement, Insurance Statement, Pay Stub, or Other",
    "vendor_or_institution": "The company, bank, hospital, or organization name",
    "date": "The primary date mentioned (statement date, bill date, or service date)",
    "account_number": "Any account number found (masked like ****1234)",
    "amount_due": "Any amount due or balance (if applicable)",
    "confidence": 0.0 to 1.0,
    "suggested_folder": "Recommended folder path (e.g., 'Bank Statements/Chase/2024/')",
    "suggested_filename": "Recommended filename",
    "reasoning": "Brief explanation of how you identified this document"
}}

Rules:
- For document_type, be specific (e.g., "Bank Statement" not just "Financial Document")
- For vendor, extract the main institution name (e.g., "Chase Bank" not "JPMorgan Chase Bank, N.A.")
- For date, use format YYYY-MM-DD if possible
- Confidence should reflect certainty (0.9+ for clear matches, 0.5-0.7 for uncertain)
- Consider NOT REAL markers - these are test documents"""

        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for consistent results
                        "num_predict": 500,
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse the LLM response
            return self._parse_llm_response(result.get("response", ""), file_path)
            
        except Exception as e:
            return {
                "document_type": "unknown",
                "vendor_or_institution": "unknown",
                "date": "unknown",
                "confidence": 0.0,
                "suggested_folder": "",
                "suggested_filename": file_path.name,
                "reasoning": f"Error: {str(e)}",
                "raw_response": "",
            }
    
    def _parse_llm_response(self, response: str, file_path: Path) -> Dict[str, Any]:
        """Parse the LLM's JSON response."""
        # Try to extract JSON from the response
        try:
            # Find JSON block
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return {
                    "document_type": data.get("document_type", "unknown"),
                    "vendor_or_institution": data.get("vendor_or_institution", "unknown"),
                    "date": data.get("date", "unknown"),
                    "account_number": data.get("account_number", ""),
                    "amount_due": data.get("amount_due", ""),
                    "confidence": float(data.get("confidence", 0.5)),
                    "suggested_folder": data.get("suggested_folder", ""),
                    "suggested_filename": data.get("suggested_filename", file_path.name),
                    "reasoning": data.get("reasoning", ""),
                    "raw_response": response,
                }
        except json.JSONDecodeError as e:
            pass
        
        # Fallback: extract key info with regex
        return self._extract_with_regex(response, file_path)
    
    def _extract_with_regex(self, response: str, file_path: Path) -> Dict[str, Any]:
        """Extract information using regex as fallback."""
        result = {
            "document_type": "unknown",
            "vendor_or_institution": "unknown",
            "date": "unknown",
            "confidence": 0.5,
            "suggested_folder": "",
            "suggested_filename": file_path.name,
            "reasoning": "Parsed from unstructured response",
            "raw_response": response,
        }
        
        # Extract document type
        type_patterns = [
            r'"document_type"\s*:\s*"([^"]+)"',
            r'document_type["\']?\s*[:=]\s*["\']?([^"\'\n,]+)',
            r'type["\']?\s*[:=]\s*["\']?([^"\'\n,]+)',
        ]
        for pattern in type_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                result["document_type"] = match.group(1).strip()
                break
        
        # Extract vendor
        vendor_patterns = [
            r'"vendor_or_institution"\s*:\s*"([^"]+)"',
            r'"vendor"\s*:\s*"([^"]+)"',
            r'"institution"\s*:\s*"([^"]+)"',
            r'vendor["\']?\s*[:=]\s*["\']?([^"\'\n,]+)',
        ]
        for pattern in vendor_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                result["vendor_or_institution"] = match.group(1).strip()
                break
        
        # Extract date
        date_patterns = [
            r'"date"\s*:\s*"([^"]+)"',
            r'date["\']?\s*[:=]\s*["\']?([^"\'\n,]+)',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                result["date"] = match.group(1).strip()
                break
        
        # Extract confidence
        conf_match = re.search(r'"confidence"\s*:\s*(0?\.\d+|1\.0)', response)
        if conf_match:
            result["confidence"] = float(conf_match.group(1))
        
        return result


class LLMTestRunner:
    """Runs LLM analysis tests on test documents using Ollama."""
    
    def __init__(self, test_data_dir: Path, model: str = "llama3.2:3b", verbose: bool = False):
        self.test_data_dir = test_data_dir
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.analyzer = OllamaDocumentAnalyzer(model=model)
        self.manifest = self._load_manifest()
        
    def _load_manifest(self) -> Dict[str, Dict]:
        """Load the ground truth manifest."""
        manifest_path = self.test_data_dir / "MANIFEST.txt"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        manifest = {}
        current_file = None
        
        with open(manifest_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("File: "):
                    current_file = line.replace("File: ", "").strip()
                    manifest[current_file] = {"type": "", "vendor": "", "date": ""}
                elif current_file and line.startswith("Expected Type: "):
                    manifest[current_file]["type"] = line.replace("Expected Type: ", "").strip()
                elif current_file and line.startswith("Source: "):
                    manifest[current_file]["vendor"] = line.replace("Source: ", "").strip()
                elif current_file and line.startswith("Date: "):
                    manifest[current_file]["date"] = line.replace("Date: ", "").strip()
        
        return manifest
    
    def log(self, message: str):
        """Print message if verbose."""
        if self.verbose:
            print(message)
    
    def _check_result(self, result: TestResult) -> TestResult:
        """Check if LLM result matches expected values."""
        # Normalize strings for comparison
        expected_type = result.expected_type.lower()
        detected_type = result.detected_type.lower()
        
        # Type matching (fuzzy)
        result.type_correct = (
            any(word in detected_type for word in expected_type.split()) or
            any(word in expected_type for word in detected_type.split()) or
            detected_type in expected_type or
            expected_type in detected_type
        )
        
        # Vendor matching (fuzzy - check if key words match)
        expected_vendor = result.expected_vendor.lower()
        detected_vendor = result.detected_vendor.lower()
        result.vendor_correct = (
            any(word in detected_vendor for word in expected_vendor.split() if len(word) > 3) or
            any(word in expected_vendor for word in detected_vendor.split() if len(word) > 3)
        )
        
        # Date matching (various formats)
        result.date_correct = self._dates_match(result.expected_date, result.detected_date)
        
        # Overall success
        result.overall_success = result.type_correct and result.confidence > 0.5
        
        return result
    
    def _dates_match(self, expected: str, detected: str) -> bool:
        """Check if two date strings match (handles different formats)."""
        if expected == "unknown" or detected == "unknown":
            return False
        
        # Normalize both dates
        expected_norm = self._normalize_date(expected)
        detected_norm = self._normalize_date(detected)
        
        return expected_norm == detected_norm
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format."""
        date_str = date_str.strip()
        
        # Try different formats
        formats = [
            "%Y-%m-%d",      # 2024-05-08
            "%B %d, %Y",     # May 08, 2024
            "%b %d, %Y",     # May 08, 2024
            "%m/%d/%Y",      # 05/08/2024
            "%d/%m/%Y",      # 08/05/2024
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # If parsing fails, return as-is for partial matching
        return date_str
    
    def run_tests(self) -> List[TestResult]:
        """Run all tests with Ollama."""
        print("="*80)
        print("OLLAMA LLM DOCUMENT ANALYSIS TEST")
        print("="*80)
        print(f"Test data directory: {self.test_data_dir}")
        print(f"Model: {self.analyzer.model}")
        print(f"Total documents to analyze: {len(self.manifest)}")
        print()
        
        # Check Ollama availability
        if not self.analyzer.is_available():
            print("❌ ERROR: Ollama is not running!")
            print("   Start it with: ollama serve")
            return []
        
        print(f"✓ Ollama is running with model: {self.analyzer.model}")
        print()
        
        # Run analysis on each file
        for i, (filename, expected) in enumerate(self.manifest.items(), 1):
            file_path = self.test_data_dir / filename
            
            if not file_path.exists():
                print(f"⚠️  [{i}/{len(self.manifest)}] Skipping {filename} - file not found")
                continue
            
            print(f"[{i}/{len(self.manifest)}] Analyzing: {filename}...")
            
            # Create result object
            result = TestResult(
                filename=filename,
                expected_type=expected.get("type", "unknown"),
                expected_vendor=expected.get("vendor", "unknown"),
                expected_date=expected.get("date", "unknown"),
            )
            
            # Run LLM analysis
            try:
                llm_result = self.analyzer.analyze_file(file_path)
                
                result.detected_type = llm_result.get("document_type", "unknown")
                result.detected_vendor = llm_result.get("vendor_or_institution", "unknown")
                result.detected_date = llm_result.get("date", "unknown")
                result.suggested_path = llm_result.get("suggested_folder", "")
                result.confidence = llm_result.get("confidence", 0.0)
                result.reasoning = llm_result.get("reasoning", "")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                result.reasoning = f"Error: {str(e)}"
            
            # Check results
            result = self._check_result(result)
            self.results.append(result)
            
            # Print result
            status = "✓" if result.overall_success else "✗"
            print(f"  {status} Type: {result.detected_type} (confidence: {result.confidence:.2f})")
            if self.verbose:
                print(f"     Expected: {result.expected_type}")
                print(f"     Vendor: {result.detected_vendor} (expected: {result.expected_vendor})")
                print(f"     Date: {result.detected_date} (expected: {result.expected_date})")
                print(f"     Suggested: {result.suggested_path}")
                print(f"     Reasoning: {result.reasoning[:150]}...")
            print()
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate test report."""
        if not self.results:
            return "No test results available."
        
        total = len(self.results)
        type_correct = sum(1 for r in self.results if r.type_correct)
        vendor_correct = sum(1 for r in self.results if r.vendor_correct)
        date_correct = sum(1 for r in self.results if r.date_correct)
        overall_success = sum(1 for r in self.results if r.overall_success)
        
        report = []
        report.append("="*80)
        report.append("OLLAMA LLM TEST RESULTS SUMMARY")
        report.append("="*80)
        report.append("")
        report.append(f"Model: {self.analyzer.model}")
        report.append(f"Total documents tested: {total}")
        report.append("")
        report.append("Accuracy:")
        report.append(f"  Document Type:  {type_correct}/{total} ({type_correct/total*100:.1f}%)")
        report.append(f"  Vendor:         {vendor_correct}/{total} ({vendor_correct/total*100:.1f}%)")
        report.append(f"  Date:           {date_correct}/{total} ({date_correct/total*100:.1f}%)")
        report.append(f"  Overall Pass:   {overall_success}/{total} ({overall_success/total*100:.1f}%)")
        report.append("")
        
        # List failures
        failures = [r for r in self.results if not r.overall_success]
        if failures:
            report.append("Failed Tests:")
            for r in failures:
                report.append(f"  • {r.filename}")
                report.append(f"    Expected: {r.expected_type}")
                report.append(f"    Detected: {r.detected_type}")
                report.append(f"    Confidence: {r.confidence:.2f}")
            report.append("")
        
        # Confidence stats
        avg_confidence = sum(r.confidence for r in self.results) / total
        report.append(f"Average confidence: {avg_confidence:.2f}")
        report.append("")
        
        if overall_success == total:
            report.append("🎉 ALL TESTS PASSED!")
        elif overall_success >= total * 0.8:
            report.append("✅ Good results - most documents correctly identified")
        elif overall_success >= total * 0.5:
            report.append("⚠️  Mixed results - some documents need better detection")
        else:
            report.append("❌ Poor results - LLM needs tuning")
        
        return "\n".join(report)
    
    def save_results(self, output_path: Path):
        """Save detailed results to JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "model": self.analyzer.model,
            "test_data_dir": str(self.test_data_dir),
            "results": [r.to_dict() for r in self.results],
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nDetailed results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Test LLM document analysis with Ollama")
    parser.add_argument('--test-dir', '-d', type=Path, 
                        default=Path(__file__).parent / "scansnap_test_data",
                        help='Directory containing test files')
    parser.add_argument('--model', '-m', type=str, default="llama3.2:3b",
                        help='Ollama model to use (default: llama3.2:3b)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--output', '-o', type=Path,
                        default=Path(__file__).parent / "ollama_test_results.json",
                        help='Output file for detailed results')
    
    args = parser.parse_args()
    
    # Run tests
    runner = LLMTestRunner(args.test_dir, model=args.model, verbose=args.verbose)
    runner.run_tests()
    
    # Print report
    print(runner.generate_report())
    
    # Save results
    runner.save_results(args.output)
    
    return runner.results


if __name__ == "__main__":
    results = main()
