import os
import sys
import time
import logging
import asyncio
import concurrent.futures
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import required libraries
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logger.warning("trafilatura not installed. Run: pip install trafilatura")

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False
        logger.warning("ddgs not installed. Run: pip install ddgs")

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("playwright not installed. Run: pip install playwright && playwright install chromium")

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass


@dataclass
class ScrapedSource:
    """Represents a scraped web source"""
    url: str
    title: str = ""
    content: str = ""
    paragraphs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    scrape_time: float = 0.0


@dataclass
class PlagiarismResult:
    """Represents a plagiarism match result"""
    source_url: str
    source_title: str
    matched_text: str
    similarity_score: float
    case_type: str
    method: str
    custom_score: float
    embedding_score: Optional[float] = None


class DuckDuckGoSearchService:
    """
    FREE web search using DuckDuckGo
    No API key required, no rate limits
    """

    def __init__(self):
        self.available = DDGS_AVAILABLE

    def search(self, query: str, num_results: int = 7, region: str = "lk") -> List[Dict]:
        """
        Search DuckDuckGo for URLs

        Args:
            query: Search query (Sinhala text)
            num_results: Number of results to return
            region: Region code (lk = Sri Lanka)

        Returns:
            List of {url, title, snippet}
        """
        if not self.available:
            logger.error("DuckDuckGo search not available")
            return []

        results = []
        logger.info(f"[DuckDuckGo] Searching: {query[:50]}...")

        try:
            with DDGS() as ddgs:
                # Fetch extra to allow filtering
                search_results = ddgs.text(query, max_results=num_results * 2, region=region)

            for result in search_results:
                url = result.get('href', '')

                # Skip PDFs and other non-text files
                if url.lower().endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx')):
                    continue

                results.append({
                    'url': url,
                    'title': result.get('title', ''),
                    'snippet': result.get('body', '')
                })

                logger.info(f"[Found] {url}")

                if len(results) >= num_results:
                    break

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")

        return results


class PlaywrightScraper:
    """
    Advanced web scraper using Playwright for JavaScript rendering
    + Trafilatura for clean text extraction
    """

    def __init__(self, timeout: int = 30000):
        self.timeout = timeout
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        self.trafilatura_available = TRAFILATURA_AVAILABLE

    def scrape_url(self, url: str) -> ScrapedSource:
        """
        Scrape a URL with JavaScript rendering

        Args:
            url: URL to scrape

        Returns:
            ScrapedSource with extracted content
        """
        start_time = time.time()
        result = ScrapedSource(url=url)

        try:
            if self.playwright_available:
                # Use Playwright for JavaScript-rendered content
                html_content = self._fetch_with_playwright(url)
            else:
                # Fallback to requests
                html_content = self._fetch_with_requests(url)

            if not html_content:
                result.error = "Failed to fetch content"
                return result

            # Extract clean text using Trafilatura
            if self.trafilatura_available:
                extracted = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False
                )
                if extracted:
                    result.content = extracted.replace('\n', ' ').strip()
            else:
                # Fallback: basic extraction
                result.content = self._basic_extract(html_content)

            # Split into paragraphs
            if result.content:
                result.paragraphs = self._split_into_paragraphs(result.content)

            result.scrape_time = time.time() - start_time
            logger.info(f"[Scraped] {url} - {len(result.paragraphs)} paragraphs in {result.scrape_time:.2f}s")

        except Exception as e:
            result.error = str(e)
            logger.error(f"Scrape error for {url}: {e}")

        return result

    def _fetch_with_playwright(self, url: str) -> str:
        """Fetch URL with Playwright (handles JavaScript) - sync wrapper for async"""
        try:
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in async context - create a new event loop in a thread
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_playwright_in_new_loop, url)
                    return future.result(timeout=self.timeout / 1000 + 10)
            except RuntimeError:
                # No event loop - can run directly
                return asyncio.run(self._playwright_async_fetch(url))
        except Exception as e:
            logger.warning(f"Playwright fetch failed: {e}")
            return ""

    def _run_playwright_in_new_loop(self, url: str) -> str:
        """Run playwright in a new event loop (for thread isolation)"""
        try:
            # Create a brand new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._playwright_async_fetch(url))
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"Playwright in new loop failed: {e}")
            return ""

    async def _playwright_async_fetch(self, url: str) -> str:
        """Actually fetch with Playwright using async API"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(ignore_https_errors=True)
                page = await context.new_page()

                await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                html_content = await page.content()

                await browser.close()
                return html_content

        except Exception as e:
            logger.warning(f"Playwright async fetch failed: {e}")
            return ""

    def _fetch_with_requests(self, url: str) -> str:
        """Fallback: fetch with requests (no JavaScript)"""
        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Requests fetch failed: {e}")
            return ""

    def _basic_extract(self, html: str) -> str:
        """Basic text extraction without Trafilatura"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                tag.decompose()

            return soup.get_text(' ', strip=True)
        except:
            return ""

    def _split_into_paragraphs(self, text: str, min_length: int = 50) -> List[str]:
        """Split text into meaningful paragraphs"""
        # Split by multiple spaces or sentence endings
        import re

        # Split by period followed by space and capital letter, or multiple spaces
        paragraphs = re.split(r'(?<=[.!?])\s+(?=[A-Z\u0D80-\u0DFF])|  +', text)

        # Filter and clean
        result = []
        for p in paragraphs:
            p = p.strip()
            if len(p) >= min_length:
                result.append(p)

        return result


class EnhancedWebPlagiarismChecker:
    """
    Complete enhanced web plagiarism checker using HYBRID METHOD

    This is an ADVANCED extension of the Approved Hybrid Detector that works
    WITHOUT the original text - only needs the suspicious/paraphrased paragraph.

    Uses the SAME hybrid method:
    - Custom Algorithm: Jaccard (40%) + 2-gram (20%) + 3-gram (20%) + Word Order (20%)
    - Fine-tuned MiniLM Model for semantic similarity
    - Intelligent routing based on score ranges

    ADVANCED FEATURE: Detects paraphrases from web without original text!
    """

    def __init__(self):
        self.search_service = DuckDuckGoSearchService()
        self.scraper = PlaywrightScraper()

        # Thresholds matching approved_hybrid.py
        self.low_threshold = 0.4   # Below this = easy_negative
        self.high_threshold = 0.7  # Above this = easy_positive

        # Import ApprovedHybridDetector - THE SAME METHOD as direct comparison
        try:
            from approved_hybrid import ApprovedHybridDetector
            self.hybrid_detector = ApprovedHybridDetector()
            self.hybrid_available = True
            logger.info("ApprovedHybridDetector loaded - using SAME hybrid method!")
        except ImportError:
            try:
                from ..approved_hybrid import ApprovedHybridDetector
                self.hybrid_detector = ApprovedHybridDetector()
                self.hybrid_available = True
                logger.info("ApprovedHybridDetector loaded - using SAME hybrid method!")
            except ImportError:
                logger.warning("ApprovedHybridDetector not available")
                self.hybrid_detector = None
                self.hybrid_available = False

        # Import embedding service for ADVANCED paraphrase detection
        # This allows detecting paraphrases even when custom score is low
        try:
            from services import FineTunedEmbeddingService
            self.embedding_service = FineTunedEmbeddingService()
            self.embedding_available = True
            logger.info("Embedding service loaded - ADVANCED paraphrase detection enabled!")
        except ImportError:
            try:
                from ..services import FineTunedEmbeddingService
                self.embedding_service = FineTunedEmbeddingService()
                self.embedding_available = True
                logger.info("Embedding service loaded - ADVANCED paraphrase detection enabled!")
            except ImportError:
                self.embedding_service = None
                self.embedding_available = False

        # Import custom algorithm for score breakdown display
        try:
            from custom_algorithms import HybridSimilarityAlgorithm
            self.custom_algorithm = HybridSimilarityAlgorithm()
            self.custom_available = True
        except ImportError:
            try:
                from ..custom_algorithms import HybridSimilarityAlgorithm
                self.custom_algorithm = HybridSimilarityAlgorithm()
                self.custom_available = True
            except ImportError:
                self.custom_algorithm = None
                self.custom_available = False

    def _create_search_query(self, text: str, max_length: int = 100) -> str:
        """Create optimized search query from input text"""
        # Take first portion of text
        query = text[:max_length].strip()

        # Remove common Sinhala stopwords for better search
        stopwords = {'සහ', 'හා', 'ද', 'ය', 'ක්', 'ම', 'ට', 'ගේ', 'වල', 'බව'}
        words = query.split()
        filtered = [w for w in words if w not in stopwords]

        if len(filtered) >= 3:
            return ' '.join(filtered)
        return query

    def check_plagiarism_from_web(
        self,
        suspicious_text: str,
        num_sources: int = 7,
        threshold: float = 0.5
    ) -> Dict:
        """
        Check suspicious text against the entire web

        This is the main function - user uploads ONLY the suspicious paragraph
        and we find potential sources from the web.

        Args:
            suspicious_text: The text to check for plagiarism
            num_sources: Number of web sources to check
            threshold: Minimum similarity score to report

        Returns:
            Dictionary with matches, statistics, and verdict
        """
        start_time = time.time()

        # Validate input
        if not suspicious_text or len(suspicious_text.strip()) < 20:
            return {
                "success": False,
                "error": "Input text too short (minimum 20 characters)",
                "matches": []
            }

        # Step 1: Search web for potential sources
        query = self._create_search_query(suspicious_text)
        logger.info(f"[Step 1] Searching web for: {query[:50]}...")

        search_results = self.search_service.search(query, num_results=num_sources)

        if not search_results:
            return {
                "success": True,
                "message": "No web sources found",
                "matches": [],
                "sources_checked": 0,
                "verdict": "No Sources Found"
            }

        # Step 2: Scrape each source
        logger.info(f"[Step 2] Scraping {len(search_results)} sources...")
        scraped_sources: List[ScrapedSource] = []

        for result in search_results:
            source = self.scraper.scrape_url(result['url'])
            source.title = result.get('title', source.title)
            scraped_sources.append(source)
            time.sleep(0.5)  # Rate limiting

        # Step 3: Compare using semantic similarity
        logger.info("[Step 3] Comparing with semantic similarity...")
        all_matches: List[PlagiarismResult] = []
        paragraphs_checked = 0

        for source in scraped_sources:
            if source.error or not source.paragraphs:
                continue

            for paragraph in source.paragraphs:
                paragraphs_checked += 1

                # Skip very short paragraphs
                if len(paragraph) < 30:
                    continue

                # Calculate similarity using EMBEDDING-FIRST approach for paraphrase detection
                try:
                    # For web search, we use EMBEDDING-FIRST to catch paraphrases
                    # Paraphrases have different words but same meaning!

                    if self.embedding_available and self.embedding_service:
                        # STEP 1: Calculate embedding similarity (catches paraphrases!)
                        embedding_score = self.embedding_service.similarity(suspicious_text, paragraph)

                        # STEP 2: Calculate custom score (for comparison)
                        if self.custom_available and self.custom_algorithm:
                            custom_result = self.custom_algorithm.calculate_similarity(suspicious_text, paragraph)
                            custom_score = custom_result["similarity_score"]
                        else:
                            # Basic Jaccard fallback
                            words1 = set(suspicious_text.lower().split())
                            words2 = set(paragraph.lower().split())
                            custom_score = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0

                        # STEP 3: Determine case type and final score
                        # For web search: prioritize embedding score for paraphrase detection
                        if embedding_score >= 0.6:
                            # High semantic similarity - likely paraphrase or copy
                            if custom_score >= 0.5:
                                case_type = "easy_positive"
                                method = "both_high"
                                score = max(embedding_score, custom_score)
                            else:
                                # Low custom but high embedding = PARAPHRASE DETECTED!
                                case_type = "paraphrase_detected"
                                method = "embedding_primary"
                                score = embedding_score  # Trust embedding for paraphrases
                        elif embedding_score >= 0.4:
                            # Medium semantic similarity - combine scores
                            case_type = "difficult"
                            method = "hybrid_fine_tuned"
                            score = (custom_score + embedding_score) / 2
                        else:
                            # Low semantic similarity - probably not related
                            case_type = "easy_negative"
                            method = "embedding_checked"
                            score = max(custom_score, embedding_score)

                    elif self.hybrid_available and self.hybrid_detector:
                        # Fallback to hybrid detector
                        result = self.hybrid_detector.detect(suspicious_text, paragraph)
                        score = result["final_score"]
                        case_type = result["case_type"]
                        method = result["method"]
                        custom_score = result["custom_score"]
                        embedding_score = result.get("embedding_score")
                    else:
                        # Final fallback: Jaccard similarity
                        words1 = set(suspicious_text.lower().split())
                        words2 = set(paragraph.lower().split())
                        score = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0
                        case_type = "basic"
                        method = "jaccard"
                        custom_score = score
                        embedding_score = None

                    # Add if above threshold
                    if score >= threshold:
                        match = PlagiarismResult(
                            source_url=source.url,
                            source_title=source.title,
                            matched_text=paragraph[:500],  # Truncate for display
                            similarity_score=score,
                            case_type=case_type,
                            method=method,
                            custom_score=custom_score,
                            embedding_score=embedding_score
                        )
                        all_matches.append(match)

                except Exception as e:
                    logger.warning(f"Comparison error: {e}")
                    continue

        # Sort by similarity score
        all_matches.sort(key=lambda x: x.similarity_score, reverse=True)

        # Deduplicate by URL (keep highest per source)
        seen_urls = set()
        unique_matches = []
        for match in all_matches:
            if match.source_url not in seen_urls:
                seen_urls.add(match.source_url)
                unique_matches.append(match)

        # Calculate verdict
        max_score = max((m.similarity_score for m in unique_matches), default=0)

        if max_score >= 0.85:
            verdict = "High Plagiarism Risk - Very similar content found"
        elif max_score >= 0.7:
            verdict = "Moderate Plagiarism Risk - Similar content found"
        elif max_score >= 0.5:
            verdict = "Low Plagiarism Risk - Some similarity found"
        elif max_score > 0:
            verdict = "Minimal Similarity - Likely original"
        else:
            verdict = "Original - No similar content found"

        processing_time = time.time() - start_time

        return {
            "success": True,
            "verdict": verdict,
            "max_similarity": round(max_score, 4),
            "threshold_used": threshold,
            "matches": [
                {
                    "source_url": m.source_url,
                    "source_title": m.source_title,
                    "matched_text": m.matched_text,
                    "similarity_score": round(m.similarity_score, 4),
                    "case_type": m.case_type,
                    "method": m.method,
                    "custom_score": round(m.custom_score, 4),
                    "embedding_score": round(m.embedding_score, 4) if m.embedding_score else None
                }
                for m in unique_matches[:10]  # Top 10 matches
            ],
            "statistics": {
                "sources_searched": len(search_results),
                "sources_scraped": len([s for s in scraped_sources if not s.error]),
                "paragraphs_checked": paragraphs_checked,
                "matches_found": len(unique_matches),
                "processing_time_seconds": round(processing_time, 2)
            },
            "metadata": {
                "search_engine": "DuckDuckGo",
                "scraper": "Playwright" if PLAYWRIGHT_AVAILABLE else "requests",
                "extractor": "Trafilatura" if TRAFILATURA_AVAILABLE else "BeautifulSoup",
                "detector": "HybridMethod (Embedding-First)" if self.embedding_available else ("ApprovedHybridDetector" if self.hybrid_available else "Jaccard")
            }
        }


def check_dependencies() -> Dict[str, bool]:
    """Check which dependencies are available"""
    return {
        "duckduckgo_search": DDGS_AVAILABLE,
        "playwright": PLAYWRIGHT_AVAILABLE,
        "trafilatura": TRAFILATURA_AVAILABLE,
        "all_available": DDGS_AVAILABLE and PLAYWRIGHT_AVAILABLE and TRAFILATURA_AVAILABLE
    }


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("ENHANCED WEB PLAGIARISM CHECKER")
    print("=" * 60)

    # Check dependencies
    deps = check_dependencies()
    print("\nDependency Status:")
    for dep, available in deps.items():
        status = "OK" if available else "MISSING"
        print(f"  {dep}: {status}")

    if not deps["all_available"]:
        print("\nInstall missing dependencies:")
        print("  pip install duckduckgo_search trafilatura playwright")
        print("  playwright install chromium")
    else:
        print("\nAll dependencies available!")

        # Test with sample text
        checker = EnhancedWebPlagiarismChecker()

        test_text = "ශ්‍රී ලංකාව ඉතා සුන්දර දිවයිනකි"  # Sri Lanka is a beautiful island
        print(f"\nTesting with: {test_text}")

        result = checker.check_plagiarism_from_web(test_text, num_sources=3, threshold=0.3)

        import json
        print(f"\nResult:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
