"""
Intelligent document analyzer with multi-pass local analysis.
Pass 1: Pattern-based extraction (high confidence, fast)
Pass 2: LLM analysis (medium confidence)
Pass 3: User review queue (low confidence)
"""
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

from .content_extractor import ContentExtractor, ExtractedContent, DocumentType
from .license_manager import get_license_manager, LicenseManager

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of document analysis."""
    file_path: Path
    suggested_name: str
    suggested_folder: str
    category: str
    confidence: float
    pass_level: int  # 1=pattern, 2=llm, 3=manual
    reasoning: str
    entities: Dict[str, Any] = field(default_factory=dict)
    needs_review: bool = False
    review_reason: Optional[str] = None


class PatternBasedAnalyzer:
    """
    First-pass analyzer using regex patterns for common document types.
    High confidence, fast, no LLM calls.
    """
    
    # Patterns for common document types
    PATTERNS = {
        "bank_statement": {
            "keywords": ["statement", "account", "balance", "deposit", "withdrawal", "transaction"],
            "company_indicators": ["chase", "bank of america", "wells fargo", "citi", "capital one", 
                                  "usbank", "pnc", "td bank", "ally", "schwab", "fidelity"],
            "date_patterns": [
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
                r"\d{1,2}/\d{1,2}/\d{4}",
                r"\d{4}-\d{2}-\d{2}"
            ],
            "account_pattern": r"account\s*(?:number|#)?\s*:?\s*[*x]*(\d{4})",
            "confidence_threshold": 0.85
        },
        "credit_card_statement": {
            "keywords": ["credit card", "statement", "payment due", "minimum payment", "apr", "credit limit"],
            "company_indicators": ["visa", "mastercard", "amex", "american express", "discover"],
            "date_patterns": [
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
                r"statement\s+period.*?\d{1,2}/\d{1,2}/\d{4}"
            ],
            "confidence_threshold": 0.85
        },
        "utility_bill": {
            "keywords": ["bill", "invoice", "amount due", "service address", "meter", "usage"],
            "company_indicators": ["electric", "gas", "water", "sewer", "trash", "waste", 
                                  "comcast", "att", "verizon", "spectrum", "cox"],
            "date_patterns": [
                r"bill\s+date\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
                r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}"
            ],
            "confidence_threshold": 0.80
        },
        "insurance": {
            "keywords": ["policy", "premium", "coverage", "deductible", "claim", "insurance"],
            "company_indicators": ["state farm", "allstate", "progressive", "geico", "farmers", 
                                  "nationwide", "liberty mutual", "travelers", "aaa", "usaa"],
            "date_patterns": [
                r"policy\s+period.*?\d{1,2}/\d{1,2}/\d{4}",
                r"effective\s+date\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})"
            ],
            "policy_pattern": r"policy\s*(?:number|#)?\s*:?\s*([A-Z0-9-]+)",
            "confidence_threshold": 0.80
        },
        "medical": {
            "keywords": ["patient", "diagnosis", "procedure", "prescription", "pharmacy", "doctor", "physician"],
            "company_indicators": ["hospital", "clinic", "medical center", "health", "urgent care"],
            "date_patterns": [
                r"date\s+of\s+service\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
                r"visit\s+date\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})"
            ],
            "confidence_threshold": 0.75
        },
        "receipt": {
            "keywords": ["receipt", "purchase", "total", "subtotal", "tax", "payment method"],
            "company_indicators": ["walmart", "target", "amazon", "costco", "home depot", "lowes",
                                  "best buy", "grocery", "restaurant", "cafe"],
            "date_patterns": [
                r"(\d{1,2}/\d{1,2}/\d{4})\s+\d{1,2}:\d{2}",
                r"date\s*:?\s*(\d{1,2}/\d{1,2}/\d{2,4})"
            ],
            "confidence_threshold": 0.70
        },
        "tax_document": {
            "keywords": ["tax", "irs", "form 1040", "w-2", "1099", "deduction", "refund", "taxable"],
            "company_indicators": ["internal revenue", "turbotax", "h&r block", "accountant"],
            "date_patterns": [
                r"tax\s+year\s*:?\s*(\d{4})",
                r"20\d{2}\s+form"
            ],
            "confidence_threshold": 0.90
        },
        "invoice": {
            "keywords": ["invoice", "invoice number", "bill to", "ship to", "payment terms", "po number"],
            "company_indicators": [],
            "date_patterns": [
                r"invoice\s+date\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
                r"date\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})"
            ],
            "invoice_pattern": r"invoice\s*(?:number|#|no)?\s*:?\s*([A-Z0-9-]+)",
            "confidence_threshold": 0.80
        }
    }
    
    # Company name normalization
    COMPANY_ALIASES = {
        "chase": "Chase",
        "bank of america": "BankOfAmerica",
        "wells fargo": "WellsFargo",
        "citi": "Citi",
        "capital one": "CapitalOne",
        "comcast": "Comcast",
        "att": "ATT",
        "at&t": "ATT",
        "verizon": "Verizon",
        "spectrum": "Spectrum",
        "state farm": "StateFarm",
        "geico": "GEICO",
        "progressive": "Progressive",
    }
    
    def __init__(self):
        self.compiled_patterns = self._compile_patterns()
        logger.info("PatternBasedAnalyzer initialized")
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for efficiency."""
        compiled = {}
        for doc_type, config in self.PATTERNS.items():
            compiled[doc_type] = {
                "keywords": [kw.lower() for kw in config["keywords"]],
                "company_indicators": [c.lower() for c in config["company_indicators"]],
                "date_patterns": [re.compile(p, re.IGNORECASE) for p in config["date_patterns"]],
                "confidence_threshold": config["confidence_threshold"]
            }
            if "account_pattern" in config:
                compiled[doc_type]["account_pattern"] = re.compile(config["account_pattern"], re.IGNORECASE)
            if "policy_pattern" in config:
                compiled[doc_type]["policy_pattern"] = re.compile(config["policy_pattern"], re.IGNORECASE)
            if "invoice_pattern" in config:
                compiled[doc_type]["invoice_pattern"] = re.compile(config["invoice_pattern"], re.IGNORECASE)
        return compiled
    
    def analyze(self, content: ExtractedContent) -> Optional[AnalysisResult]:
        """
        Analyze document using pattern matching.
        
        Returns:
            AnalysisResult if confidence >= threshold, None otherwise
        """
        text = content.text_content.lower()
        filename = content.file_path.stem.lower()
        
        best_match = None
        best_confidence = 0.0
        
        for doc_type, patterns in self.compiled_patterns.items():
            confidence, entities = self._calculate_confidence(text, filename, patterns)
            
            if confidence >= patterns["confidence_threshold"] and confidence > best_confidence:
                best_confidence = confidence
                best_match = (doc_type, patterns, entities)
        
        if best_match:
            doc_type, patterns, entities = best_match
            return self._build_result(content, doc_type, entities, best_confidence)
        
        return None
    
    def _calculate_confidence(self, text: str, filename: str, patterns: Dict) -> Tuple[float, Dict]:
        """Calculate confidence score and extract entities."""
        score = 0.0
        entities = {}
        
        # Check keywords (up to 0.3)
        keyword_matches = sum(1 for kw in patterns["keywords"] if kw in text)
        keyword_score = min(keyword_matches / len(patterns["keywords"]), 1.0) * 0.3
        score += keyword_score
        
        # Check company indicators (up to 0.3)
        if patterns["company_indicators"]:
            company_matches = [c for c in patterns["company_indicators"] if c in text]
            if company_matches:
                score += 0.3
                entities["company"] = self._normalize_company(company_matches[0])
        
        # Check dates (up to 0.2)
        dates = []
        for pattern in patterns["date_patterns"]:
            matches = pattern.findall(text)
            dates.extend(matches)
        if dates:
            score += 0.2
            entities["date"] = self._normalize_date(dates[0])
        
        # Extract specific IDs (up to 0.2)
        if "account_pattern" in patterns:
            match = patterns["account_pattern"].search(text)
            if match:
                score += 0.1
                entities["account_last4"] = match.group(1)
        
        if "policy_pattern" in patterns:
            match = patterns["policy_pattern"].search(text)
            if match:
                score += 0.1
                entities["policy_number"] = match.group(1)
        
        if "invoice_pattern" in patterns:
            match = patterns["invoice_pattern"].search(text)
            if match:
                score += 0.1
                entities["invoice_number"] = match.group(1)
        
        return score, entities
    
    def _normalize_company(self, company: str) -> str:
        """Normalize company name for filename use."""
        company_lower = company.lower()
        for alias, normalized in self.COMPANY_ALIASES.items():
            if alias in company_lower:
                return normalized
        # Capitalize and remove spaces
        return company.title().replace(" ", "")
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM format for sorting."""
        for fmt in ("%B %Y", "%b %Y", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m")
            except ValueError:
                continue
        return date_str.replace(" ", "_")
    
    def _build_result(self, content: ExtractedContent, doc_type: str, entities: Dict, confidence: float) -> AnalysisResult:
        """Build analysis result from pattern match."""
        # Build suggested name
        parts = []
        
        if "company" in entities:
            parts.append(entities["company"])
        
        doc_type_formatted = doc_type.replace("_", " ").title().replace(" ", "")
        parts.append(doc_type_formatted)
        
        if "date" in entities:
            parts.append(entities["date"])
        elif "account_last4" in entities:
            parts.append(f"Acct{entities['account_last4']}")
        elif "policy_number" in entities:
            parts.append(f"Policy{entities['policy_number']}")
        
        suggested_name = "_".join(parts) + content.file_path.suffix
        
        # Build folder path
        category = doc_type.replace("_", "_").title()
        year = entities.get("date", datetime.now().strftime("%Y-%m"))[:4]
        
        if "company" in entities:
            suggested_folder = f"{category}/{year}/{entities['company']}"
        else:
            suggested_folder = f"{category}/{year}"
        
        return AnalysisResult(
            file_path=content.file_path,
            suggested_name=suggested_name,
            suggested_folder=suggested_folder,
            category=category,
            confidence=confidence,
            pass_level=1,
            reasoning=f"Pattern match: {doc_type.replace('_', ' ').title()} detected with high confidence",
            entities=entities
        )


class LLMRetryableError(Exception):
    """Error that can be retried."""
    pass


class IntelligentDocumentAnalyzer:
    """
    Multi-pass document analyzer with configurable sensitivity.
    
    Pass 1: Pattern matching (highest confidence)
    Pass 2: Local LLM via Ollama (medium confidence)
    Pass 3: User review (low confidence or manual flag)
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "llama3.2:3b",
        confidence_threshold_high: float = 0.85,
        confidence_threshold_medium: float = 0.70,
        confidence_threshold_review: float = 0.50,
        enable_learning: bool = True,
        learning_db_path: Optional[Path] = None
    ):
        """
        Initialize analyzer.
        
        Args:
            ollama_url: Ollama API URL
            ollama_model: Model to use
            confidence_threshold_high: Auto-process if above this
            confidence_threshold_medium: Use LLM if between medium and high
            confidence_threshold_review: Flag for review if below this
            enable_learning: Store successful patterns for future
            learning_db_path: Path to learning database
        """
        self.extractor = ContentExtractor()
        self.pattern_analyzer = PatternBasedAnalyzer()
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        
        # Confidence thresholds (configurable sensitivity)
        self.threshold_high = confidence_threshold_high
        self.threshold_medium = confidence_threshold_medium
        self.threshold_review = confidence_threshold_review
        
        # Learning system
        self.enable_learning = enable_learning
        self.learning_db_path = learning_db_path or Path.home() / ".file_organizer" / "learning.json"
        self.learned_patterns = self._load_learned_patterns()
        
        logger.info(f"IntelligentDocumentAnalyzer initialized")
        logger.info(f"  Thresholds: auto≥{threshold_high}, llm≥{threshold_medium}, review<{threshold_review}")
    
    def _load_learned_patterns(self) -> Dict:
        """Load learned patterns from disk."""
        if self.learning_db_path.exists():
            try:
                with open(self.learning_db_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load learning DB: {e}")
        return {"success_patterns": [], "user_corrections": []}
    
    def _save_learned_patterns(self):
        """Save learned patterns to disk."""
        try:
            self.learning_db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.learning_db_path, 'w') as f:
                json.dump(self.learned_patterns, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save learning DB: {e}")
    
    def check_ollama_available(self) -> Tuple[bool, str]:
        """Check if Ollama is running and model is available."""
        try:
            import requests
            
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False, "Ollama is not responding"
            
            # Check if model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", m.get("model", "")) for m in models]
            
            if self.ollama_model not in model_names:
                available = ", ".join(model_names[:5]) if model_names else "none"
                return False, f"Model '{self.ollama_model}' not found. Available: {available}"
            
            return True, "Ready"
            
        except ImportError:
            return False, "requests library not installed (pip install requests)"
        except Exception as e:
            return False, f"Ollama connection failed: {e}"
    
    def analyze_document(self, file_path: Path) -> AnalysisResult:
        """
        Analyze a single document through all passes.
        
        Returns:
            AnalysisResult with suggested name/folder
        """
        logger.info(f"Analyzing: {file_path.name}")
        
        # Check license for AI features
        license_mgr = get_license_manager()
        can_use_ai, license_message = license_mgr.can_use_ai_analysis()
        
        # Step 1: Extract content
        content = self.extractor.extract(file_path)
        
        if content.error:
            logger.warning(f"Extraction error: {content.error}")
            return self._create_review_result(file_path, f"Extraction failed: {content.error}")
        
        if not content.text_content.strip():
            return self._create_review_result(file_path, "No text content extracted (scanned image without OCR?)")
        
        # Pass 1: Pattern-based analysis (always available)
        pattern_result = self.pattern_analyzer.analyze(content)
        if pattern_result and pattern_result.confidence >= self.threshold_high:
            logger.info(f"  → Pass 1 (pattern): {pattern_result.suggested_name} ({pattern_result.confidence:.0%})")
            return pattern_result
        
        # Check if we can use AI (LLM) features
        if not can_use_ai:
            # No AI license - use pattern result if decent, otherwise review
            if pattern_result and pattern_result.confidence >= self.threshold_medium:
                logger.info(f"  → Pass 1 (pattern - no AI license): {pattern_result.suggested_name}")
                return pattern_result
            else:
                return self._create_review_result(
                    file_path, 
                    f"{license_message}. Pattern confidence too low for auto-organization."
                )
        
        # Consume trial use if applicable
        if license_mgr.get_license_status()["status"] == "trial":
            license_mgr.use_trial()
        
        # Pass 2: LLM analysis (if pattern confidence is medium, or no pattern match)
        if pattern_result and pattern_result.confidence >= self.threshold_medium:
            # Pattern matched but not high confidence - try LLM for confirmation
            try:
                llm_result = self._llm_analyze(content, pattern_result)
                # Use LLM result if it's confident enough
                if llm_result.confidence >= self.threshold_medium:
                    logger.info(f"  → Pass 2 (LLM): {llm_result.suggested_name} ({llm_result.confidence:.0%})")
                    return llm_result
                # If LLM is uncertain but pattern was decent, use pattern result
                elif pattern_result.confidence >= self.threshold_medium:
                    logger.info(f"  → Pass 1 (pattern kept): {pattern_result.suggested_name} ({pattern_result.confidence:.0%})")
                    return pattern_result
            except Exception as e:
                logger.warning(f"LLM analysis failed, falling back to pattern: {e}")
                # LLM failed but we have a decent pattern match - use it
                if pattern_result.confidence >= self.threshold_medium:
                    logger.info(f"  → Pass 1 (pattern fallback): {pattern_result.suggested_name} ({pattern_result.confidence:.0%})")
                    return pattern_result
        elif not pattern_result:
            # No pattern match - try LLM
            try:
                llm_result = self._llm_analyze(content, None)
                if llm_result.confidence >= self.threshold_medium:
                    logger.info(f"  → Pass 2 (LLM): {llm_result.suggested_name} ({llm_result.confidence:.0%})")
                    return llm_result
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}")
        
        # Pass 3: Flag for review
        review_reason = "Low confidence in automatic analysis"
        if pattern_result:
            review_reason += f" (pattern: {pattern_result.confidence:.0%})"
        
        logger.info(f"  → Pass 3 (review): {file_path.name}")
        return self._create_review_result(file_path, review_reason)
    
    def _llm_analyze(self, content: ExtractedContent, pattern_hint: Optional[AnalysisResult]) -> AnalysisResult:
        """Analyze document using local LLM via Ollama."""
        # Build prompt
        system_prompt = """You are a document analysis assistant. Your task is to:
1. Identify the document type (bank statement, utility bill, insurance, medical, receipt, invoice, tax document, etc.)
2. Extract key entities: company name, date, account/policy numbers
3. Suggest a descriptive filename and folder location

Respond ONLY in this JSON format:
{
  "document_type": "bank_statement",
  "company": "Chase",
  "date": "2025-05",
  "account_number": "1234",
  "suggested_name": "Chase_Bank_Statement_2025-05.pdf",
  "suggested_folder": "Bank_Statements/2025/Chase",
  "category": "Finance",
  "confidence": 0.92,
  "reasoning": "Chase bank statement for May 2025"
}

Confidence guidelines:
- 0.90-1.00: Very clear document, all entities extracted
- 0.70-0.89: Good match, most entities found
- 0.50-0.69: Uncertain, some entities missing
- Below 0.50: Cannot determine, flag for review"""

        user_prompt = f"""Analyze this document and extract information:

Filename: {content.file_path.name}

Document content:
---
{content.text_content[:4000]}
---

Respond with JSON only."""

        if pattern_hint:
            user_prompt += f"\n\nHint: Pattern analysis suggests this might be a {pattern_hint.category} from {pattern_hint.entities.get('company', 'unknown company')}."

        try:
            import requests
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            
            if response.status_code != 200:
                raise LLMRetryableError(f"Ollama returned {response.status_code}")
            
            result_text = response.json().get("response", "")

            # Parse JSON response
            llm_result = json.loads(result_text)
            
            # Build AnalysisResult
            confidence = float(llm_result.get("confidence", 0.5))
            
            return AnalysisResult(
                file_path=content.file_path,
                suggested_name=llm_result.get("suggested_name", content.file_path.name),
                suggested_folder=llm_result.get("suggested_folder", "Uncategorized"),
                category=llm_result.get("category", llm_result.get("document_type", "Unknown")).title(),
                confidence=confidence,
                pass_level=2,
                reasoning=llm_result.get("reasoning", "LLM analysis"),
                entities={
                    "company": llm_result.get("company"),
                    "date": llm_result.get("date"),
                    "account_number": llm_result.get("account_number"),
                    "document_type": llm_result.get("document_type")
                }
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            return AnalysisResult(
                file_path=content.file_path,
                suggested_name=content.file_path.name,
                suggested_folder="Uncategorized",
                category="Unknown",
                confidence=0.0,
                pass_level=2,
                reasoning="LLM returned invalid format",
                needs_review=True,
                review_reason="LLM output parsing failed"
            )
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return AnalysisResult(
                file_path=content.file_path,
                suggested_name=content.file_path.name,
                suggested_folder="Uncategorized",
                category="Unknown",
                confidence=0.0,
                pass_level=2,
                reasoning=f"LLM error: {e}",
                needs_review=True,
                review_reason=f"LLM analysis failed: {e}"
            )
    
    def _create_review_result(self, file_path: Path, reason: str) -> AnalysisResult:
        """Create a result flagged for manual review."""
        return AnalysisResult(
            file_path=file_path,
            suggested_name=file_path.name,
            suggested_folder="Review_Required",
            category="Unknown",
            confidence=0.0,
            pass_level=3,
            reasoning="Manual review required",
            needs_review=True,
            review_reason=reason
        )
    
    def record_user_correction(self, original: AnalysisResult, user_name: str, user_folder: str):
        """Record a user correction for learning."""
        if not self.enable_learning:
            return
        
        correction = {
            "timestamp": datetime.now().isoformat(),
            "original_name": original.suggested_name,
            "user_name": user_name,
            "original_folder": original.suggested_folder,
            "user_folder": user_folder,
            "entities": original.entities,
            "file_type": original.file_path.suffix
        }
        
        self.learned_patterns["user_corrections"].append(correction)
        self._save_learned_patterns()
        logger.info(f"Recorded user correction for learning")
    
    def analyze_batch(
        self,
        file_paths: List[Path],
        progress_callback=None
    ) -> Tuple[List[AnalysisResult], List[AnalysisResult]]:
        """
        Analyze a batch of documents with prioritization.
        
        Returns:
            (auto_results, review_results) - partitioned by needs_review flag
        """
        auto_results = []
        review_results = []
        
        total = len(file_paths)
        for i, file_path in enumerate(file_paths):
            if progress_callback:
                progress_callback(i + 1, total, file_path.name)
            
            try:
                result = self.analyze_document(file_path)
                
                if result.needs_review:
                    review_results.append(result)
                else:
                    auto_results.append(result)
                    
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                review_results.append(self._create_review_result(file_path, f"Analysis error: {e}"))
        
        return auto_results, review_results
