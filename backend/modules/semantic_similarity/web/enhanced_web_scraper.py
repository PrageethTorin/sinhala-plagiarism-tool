import os
import sys
import re
import time
import logging
import asyncio
import concurrent.futures
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

import numpy as np

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
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("playwright not installed. Run: pip install playwright && playwright install chromium")

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

try:
    import requests as _requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Google Search API fallback (configured via GOOGLE_API_KEY + CSE_ID in .env)
GOOGLE_SEARCH_AVAILABLE = False
try:
    from .web_search_service import GoogleSearchService
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    try:
        from web_search_service import GoogleSearchService
        GOOGLE_SEARCH_AVAILABLE = True
    except ImportError:
        pass

# Reuse existing utilities (sentence splitting, paragraph splitting)
try:
    from ..utils import split_sentences_simple, split_paragraphs
except ImportError:
    # Fallback if relative import fails
    try:
        from utils import split_sentences_simple, split_paragraphs
    except ImportError:
        def split_sentences_simple(text):
            if not text:
                return []
            parts = re.split(r'(?<=[\.\?\!\u0964])\s+|\n+', str(text))
            return [p.strip() for p in parts if p.strip()]

        def split_paragraphs(text):
            if not text:
                return []
            parts = [p.strip() for p in re.split(r'\n{2,}|\r\n{2,}', str(text)) if p.strip()]
            if not parts and str(text).strip():
                parts = [str(text).strip()]
            return parts

# Full Sinhala stopwords (50+) — used for search query optimization
SINHALA_STOPWORDS = {
    'සහ', 'හා', 'ද', 'ත්', 'ය', 'ක්', 'න්', 'ම', 'ට', 'ගේ',
    'වල', 'බව', 'නම්', 'විසින්', 'සඳහා', 'මෙම', 'එම', 'මේ', 'ඒ',
    'කල', 'කළ', 'වන', 'වූ', 'ඇති', 'නැති', 'පමණ', 'ලෙස', 'අතර',
    'මෙය', 'එය', 'ඔවුන්', 'ඔහු', 'ඇය', 'මම', 'අපි', 'ඔබ',
    'කිරීම', 'කරන', 'කළා', 'කරනු', 'කරන්නේ', 'කරමින්',
    'යන', 'යනු', 'වේ', 'වෙයි', 'විය', 'වෙනවා', 'වුණා',
    'ඇත', 'නැත', 'ඇතත්', 'නැතත්', 'ඇතිව', 'නැතිව',
    'සිට', 'දක්වා', 'පසු', 'පෙර', 'අතරතුර', 'අතරට',
    'නිසා', 'නමුත්', 'එසේම', 'එහෙත්', 'එබැවින්', 'මෙසේ',
    'ලෙසට', 'විට', 'තුළ', 'හරහා', 'මගින්', 'අනුව',
    'පිළිබඳ', 'පිළිබඳව', 'ගැන', 'සමග', 'සමඟ',
    'හෝ', 'වත්', 'වුවද', 'මෙන්', 'මෙන්ම', 'එහෙනම්',
    'බොහෝ', 'සෑම', 'සමහර', 'අනෙකුත්', 'එක', 'එකක්',
    'ලබා', 'දෙන', 'ගත්', 'ගැනීම', 'දීම', 'කිරීමට',
    'කොහේ', 'කවුද', 'මොකද', 'කොහොමද', 'කවදා', 'කොහෙන්', 'මට',
    'එහි', 'මෙහි', 'එවිට', 'මෙවිට', 'එසේ',
}


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
    matched_sentence: Optional[str] = None
    user_matched_text: Optional[str] = None


class DuckDuckGoSearchService:
    """
    Web search using DuckDuckGo (primary) + Google Custom Search API (fallback).
    Google fallback activates when DDG returns too few Sinhala results.
    """

    def __init__(self):
        self.available = DDGS_AVAILABLE
        self.google_service = None
        if GOOGLE_SEARCH_AVAILABLE:
            try:
                self.google_service = GoogleSearchService()
                if self.google_service.is_configured:
                    logger.info("Google Search API configured as fallback")
                else:
                    self.google_service = None
            except Exception:
                self.google_service = None

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
                search_results = ddgs.text(query, max_results=num_results * 3, region=region)

            # Prioritize results with Sinhala content in snippet/title
            sinhala_results = []
            other_results = []

            for result in search_results:
                url = result.get('href', '')

                # Skip PDFs and other non-text files
                if url.lower().endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx')):
                    continue

                entry = {
                    'url': url,
                    'title': result.get('title', ''),
                    'snippet': result.get('body', '')
                }

                # Check if snippet or title contains Sinhala characters
                combined = entry['title'] + ' ' + entry['snippet']
                sinhala_chars = len(re.findall(r'[\u0D80-\u0DFF]', combined))

                if sinhala_chars >= 5:
                    sinhala_results.append(entry)
                else:
                    other_results.append(entry)

            # Sinhala results first, then others
            for entry in sinhala_results + other_results:
                results.append(entry)
                logger.info(f"[Found] {entry['url']}")
                if len(results) >= num_results:
                    break

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")

        # --- Google Search API fallback ---
        # If DDG returned fewer than 2 Sinhala results, try Google (better for Sinhala)
        sinhala_count = sum(1 for r in results
                           if len(re.findall(r'[\u0D80-\u0DFF]', r.get('title', '') + r.get('snippet', ''))) >= 3)

        if sinhala_count < 2 and self.google_service:
            logger.info(f"[Google Fallback] DDG returned only {sinhala_count} Sinhala results, trying Google...")
            try:
                google_results = self.google_service.search(query[:150], num_results=num_results, language="si")
                seen_urls = {r['url'] for r in results}
                for gr in google_results:
                    url = gr.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        results.append({
                            'url': url,
                            'title': gr.get('title', ''),
                            'snippet': gr.get('snippet', '')
                        })
                        logger.info(f"[Google] Added: {url[:80]}")
                logger.info(f"[Google Fallback] Total results now: {len(results)}")
            except Exception as e:
                logger.warning(f"Google fallback search error: {e}")

        return results


def search_wikipedia_directly(text: str, max_results: int = 5) -> List[Dict]:
    """Search Sinhala Wikipedia directly using its API (bypasses DDG entirely)."""
    if not REQUESTS_AVAILABLE:
        return []

    results = []
    sentences = text.split('.')
    # Use first meaningful sentence as search query
    query = sentences[0].strip()[:150] if sentences else text[:150]

    try:
        resp = _requests.get(
            'https://si.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srlimit': max_results,
                'format': 'json',
                'utf8': 1
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('query', {}).get('search', []):
                title = item.get('title', '')
                url = f"https://si.wikipedia.org/wiki/{title.replace(' ', '_')}"
                snippet = re.sub(r'<[^>]+>', '', item.get('snippet', ''))
                results.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet
                })
                logger.info(f"[Wikipedia API] Found: {url}")
    except Exception as e:
        logger.warning(f"Wikipedia API search error: {e}")

    return results


class PlaywrightScraper:
    """
    Advanced web scraper using Playwright for JavaScript rendering
    + Trafilatura for clean text extraction
    """

    def __init__(self, timeout: int = 8000):
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

            # Extract clean text using Trafilatura — KEEP newlines for paragraph splitting
            if self.trafilatura_available:
                extracted = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False
                )
                if extracted:
                    result.content = extracted.strip()
            else:
                # Fallback: basic extraction
                result.content = self._basic_extract(html_content)

            # Split into paragraphs preserving natural boundaries
            if result.content:
                result.paragraphs = self._split_into_paragraphs(result.content)

            result.scrape_time = time.time() - start_time
            logger.info(f"[Scraped] {url} - {len(result.paragraphs)} paragraphs in {result.scrape_time:.2f}s")

        except Exception as e:
            result.error = str(e)
            logger.error(f"Scrape error for {url}: {e}")

        return result

    def _fetch_with_playwright(self, url: str) -> str:
        """Fetch URL with Playwright sync API (handles JavaScript) - with timeout protection"""
        try:
            # Use ThreadPoolExecutor with timeout to prevent hanging
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_playwright_sync, url)
                return future.result(timeout=15)
        except concurrent.futures.TimeoutError:
            logger.warning(f"Playwright fetch TIMEOUT for {url} (exceeded 15 seconds)")
            return ""
        except Exception as e:
            logger.warning(f"Playwright fetch failed for {url}: {e}")
            return ""

    def _run_playwright_sync(self, url: str) -> str:
        """Run Playwright using sync API (thread-safe, no event loop issues on Windows)"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                try:
                    page.goto(url, timeout=8000, wait_until="domcontentloaded")
                    html_content = page.content()
                except Exception as e:
                    logger.warning(f"Playwright page load failed for {url}: {e}")
                    html_content = ""
                finally:
                    browser.close()
                return html_content
        except Exception as e:
            logger.warning(f"Playwright sync fetch failed: {e}")
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

            return soup.get_text('\n', strip=True)
        except Exception:
            return ""

    def _split_into_paragraphs(self, text: str, min_length: int = 40) -> List[str]:
        """Split text into meaningful paragraphs, preserving natural boundaries."""
        # Step 1: Split on double newlines (natural paragraph breaks from trafilatura)
        paragraphs = split_paragraphs(text)

        # Step 2: For very long paragraphs (>500 chars), also split on single newlines
        expanded = []
        for p in paragraphs:
            if len(p) > 500 and '\n' in p:
                sub_parts = [s.strip() for s in p.split('\n') if s.strip()]
                expanded.extend(sub_parts)
            else:
                expanded.append(p)

        # Step 3: Filter by minimum length
        return [p for p in expanded if len(p) >= min_length]


class EnhancedWebPlagiarismChecker:
    """
    Enhanced web plagiarism checker with improved accuracy.

    Improvements over original:
    - Multiple search queries from different text portions
    - Batch encoding (encode suspicious text once, batch per source)
    - Sentence-level matching for long texts (catches partial matches)
    - Snippet pre-filtering (skip irrelevant URLs before scraping)
    - Better deduplication (top 3 per URL instead of 1)
    - Consistent scoring (matches approved_hybrid.py)
    """

    def __init__(self):
        self.search_service = DuckDuckGoSearchService()
        self.scraper = PlaywrightScraper()

        # Import ApprovedHybridDetector
        try:
            from approved_hybrid import ApprovedHybridDetector
            self.hybrid_detector = ApprovedHybridDetector()
            self.hybrid_available = True
        except ImportError:
            try:
                from ..approved_hybrid import ApprovedHybridDetector
                self.hybrid_detector = ApprovedHybridDetector()
                self.hybrid_available = True
            except ImportError:
                self.hybrid_detector = None
                self.hybrid_available = False

        # Import embedding service for batch encoding
        try:
            from services import FineTunedEmbeddingService
            self.embedding_service = FineTunedEmbeddingService()
            self.embedding_available = True
            logger.info("Embedding service loaded - batch encoding enabled!")
        except ImportError:
            try:
                from ..services import FineTunedEmbeddingService
                self.embedding_service = FineTunedEmbeddingService()
                self.embedding_available = True
                logger.info("Embedding service loaded - batch encoding enabled!")
            except ImportError:
                self.embedding_service = None
                self.embedding_available = False

        # Import custom algorithm for score breakdown
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

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _has_sinhala(text: str, min_chars: int = 5) -> bool:
        """Check if text contains enough Sinhala characters to be considered Sinhala content."""
        return len(re.findall(r'[\u0D80-\u0DFF]', text)) >= min_chars

    def _batch_encode(self, texts: List[str]) -> np.ndarray:
        """Batch encode texts into normalized embeddings using the fine-tuned model.
        Returns numpy array of shape (len(texts), 768) with L2-normalized rows.
        Cosine similarity = dot product on these normalized embeddings.
        """
        if not texts:
            return np.array([]).reshape(0, 0)
        return self.embedding_service.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )

    def _classify_match(self, embedding_score: float, custom_score: float) -> Tuple[float, str, str]:
        """Classify a match using embedding-first approach.
        Returns (final_score, case_type, method).
        Consistent with approved_hybrid.py scoring.
        """
        if embedding_score >= 0.6:
            if custom_score >= 0.5:
                case_type = "easy_positive"
                method = "both_high"
                score = (embedding_score + custom_score) / 2
            elif custom_score >= 0.15:
                # Low custom but high embedding = PARAPHRASE (different words, same meaning)
                # Require minimum 0.15 custom to avoid cross-topic false positives
                case_type = "paraphrase_detected"
                method = "embedding_primary"
                score = embedding_score * 0.7 + custom_score * 0.3  # Blend in custom to reduce FP
            else:
                # Very low custom (<0.15) = likely false positive (same language, different topic)
                case_type = "weak_match"
                method = "embedding_only_low_custom"
                score = (embedding_score + custom_score) / 2  # Penalize heavily
        elif embedding_score >= 0.4:
            case_type = "difficult"
            method = "hybrid_fine_tuned"
            score = (custom_score + embedding_score) / 2
        else:
            case_type = "easy_negative"
            method = "embedding_checked"
            score = max(custom_score, embedding_score)
        return score, case_type, method

    def _remove_stopwords(self, text: str) -> str:
        """Remove Sinhala stopwords from text for better search queries."""
        words = text.split()
        filtered = [w for w in words if w not in SINHALA_STOPWORDS and len(w) > 1]
        return ' '.join(filtered) if len(filtered) >= 3 else text

    def _create_search_queries(self, text: str, max_queries: int = 3) -> List[str]:
        """Generate multiple diverse search queries for better web coverage.

        Strategy:
        - Query 1: First sentence(s) — exact Sinhala phrases for best matching
        - Query 2: Middle portion of text
        - Query 3: End/distinctive portion of text
        Uses longer query strings (up to 200 chars) for better Sinhala matching.
        """
        sentences = split_sentences_simple(text)
        queries = []

        # Query 1: First 1-2 sentences (keep Sinhala words intact for exact matching)
        if sentences:
            q1 = sentences[0]
            if len(sentences) > 1 and len(q1) < 100:
                q1 += ' ' + sentences[1]
            q1 = self._remove_stopwords(q1)[:200]
            queries.append(q1)

        # Query 2: Middle portion (different part of text)
        if len(sentences) >= 3:
            mid_idx = len(sentences) // 2
            q2 = sentences[mid_idx]
            if mid_idx + 1 < len(sentences) and len(q2) < 100:
                q2 += ' ' + sentences[mid_idx + 1]
            q2 = self._remove_stopwords(q2)[:200]
            if q2 not in queries:
                queries.append(q2)

        # Query 3: End portion (conclusion, often distinctive)
        if len(sentences) >= 5:
            q3 = sentences[-1]
            if len(sentences) > 1 and len(q3) < 100:
                q3 = sentences[-2] + ' ' + q3
            q3 = self._remove_stopwords(q3)[:200]
            if q3 not in queries:
                queries.append(q3)

        # Query 4: Site-targeted search for known Sinhala sources
        if sentences:
            site_query = f"site:si.wikipedia.org {self._remove_stopwords(sentences[0])[:120]}"
            if site_query not in queries:
                queries.append(site_query)

        # Fallback
        if not queries:
            queries.append(self._remove_stopwords(text[:200])[:200])

        return queries[:max_queries + 1]  # Allow one extra for site-targeted query

    def _compute_custom_score(self, text1: str, text2: str) -> float:
        """Compute custom algorithm score between two texts."""
        if self.custom_available and self.custom_algorithm:
            result = self.custom_algorithm.calculate_similarity(text1, text2)
            return result["similarity_score"]
        # Fallback: basic Jaccard
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        union = words1 | words2
        return len(words1 & words2) / len(union) if union else 0

    # ==================== MAIN METHOD ====================

    def check_plagiarism_from_web(
        self,
        suspicious_text: str,
        num_sources: int = 7,
        threshold: float = 0.5
    ) -> Dict:
        """
        Check suspicious text against the entire web.

        Improvements:
        - Multiple search queries from different text portions
        - Batch encoding (suspicious text encoded once)
        - Sentence-level matching for ambiguous scores
        - Snippet pre-filtering before expensive scraping
        - Better deduplication (top 3 per URL)
        """
        start_time = time.time()

        # Validate input
        if not suspicious_text or len(suspicious_text.strip()) < 20:
            return {
                "success": False,
                "error": "Input text too short (minimum 20 characters)",
                "matches": []
            }

        # ===== Step 1: Pre-encode suspicious text ONCE =====
        suspicious_sentences = split_sentences_simple(suspicious_text)
        # Filter very short sentences
        suspicious_sentences = [s for s in suspicious_sentences if len(s) >= 10]

        suspicious_full_emb = None
        suspicious_sent_embs = None

        if self.embedding_available:
            try:
                texts_to_encode = [suspicious_text] + suspicious_sentences
                all_embs = self._batch_encode(texts_to_encode)
                suspicious_full_emb = all_embs[0]       # shape: (768,)
                suspicious_sent_embs = all_embs[1:]      # shape: (N, 768)
                logger.info(f"[Step 1] Encoded suspicious text: 1 full + {len(suspicious_sentences)} sentences")
            except Exception as e:
                logger.warning(f"Batch encode failed: {e}")

        # ===== Step 1b: Split user text into paragraphs for paragraph-level matching =====
        user_paragraphs = split_paragraphs(suspicious_text)
        user_paragraphs = [p for p in user_paragraphs if len(p.strip()) >= 20]
        if not user_paragraphs:
            user_paragraphs = [suspicious_text]

        user_para_embs = None
        if self.embedding_available and len(user_paragraphs) > 0:
            try:
                user_para_embs = self._batch_encode(user_paragraphs)
                logger.info(f"[Step 1b] Encoded {len(user_paragraphs)} user paragraphs for matching")
            except Exception as e:
                logger.warning(f"User paragraph encoding failed: {e}")

        # ===== Step 2: Search web with MULTIPLE queries =====
        queries = self._create_search_queries(suspicious_text, max_queries=3)
        logger.info(f"[Step 2] Searching web with {len(queries)} queries...")

        all_search_results = []
        seen_urls = set()
        for query in queries:
            results = self.search_service.search(query, num_results=num_sources)
            for r in results:
                if r['url'] not in seen_urls:
                    seen_urls.add(r['url'])
                    all_search_results.append(r)
            time.sleep(0.05)  # Minimal rate limit between queries

        # ===== Step 2b: Always search Wikipedia directly (DDG is unreliable for Sinhala) =====
        try:
            wiki_results = search_wikipedia_directly(suspicious_text, max_results=5)
            wiki_added = 0
            for r in wiki_results:
                if r['url'] not in seen_urls:
                    seen_urls.add(r['url'])
                    all_search_results.insert(0, r)  # Wikipedia first priority
                    wiki_added += 1
            if wiki_added > 0:
                logger.info(f"[Step 2b] Added {wiki_added} Wikipedia articles via direct API")
        except Exception as e:
            logger.warning(f"Wikipedia direct search failed: {e}")

        if not all_search_results:
            return {
                "success": True,
                "message": "No web sources found",
                "matches": [],
                "sources_checked": 0,
                "verdict": "No Sources Found",
                "statistics": {"queries_used": len(queries)}
            }

        logger.info(f"[Step 2] Found {len(all_search_results)} unique URLs from {len(queries)} queries")

        # ===== Step 3: Pre-filter using snippet embeddings =====
        scrape_targets = all_search_results
        snippets_filtered = 0

        if suspicious_full_emb is not None:
            filtered_priority = []  # Wikipedia and other priority sources
            filtered_sinhala = []
            filtered_other = []
            for r in all_search_results:
                url = r.get('url', '')

                # Never filter out Wikipedia — always include
                if 'wikipedia.org' in url:
                    filtered_priority.append(r)
                    continue

                snippet = r.get('snippet', '')
                has_sinhala_snippet = self._has_sinhala(snippet, 5)

                if has_sinhala_snippet and len(snippet) >= 20:
                    try:
                        snippet_emb = self._batch_encode([snippet])[0]
                        snippet_score = float(np.dot(suspicious_full_emb, snippet_emb))
                        r['snippet_score'] = snippet_score
                        if snippet_score >= 0.10:
                            filtered_sinhala.append(r)
                        else:
                            snippets_filtered += 1
                            logger.info(f"[Skip] {r['url'][:60]}... snippet_score={snippet_score:.3f}")
                    except Exception:
                        filtered_sinhala.append(r)  # Include on error
                elif self._has_sinhala(r.get('title', ''), 3):
                    # Title has Sinhala even if snippet doesn't — page likely has Sinhala content
                    filtered_sinhala.append(r)
                else:
                    # Non-Sinhala snippet — lower priority but include (page may have Sinhala)
                    filtered_other.append(r)

            # Wikipedia first, then Sinhala-snippet results, then others
            scrape_targets = filtered_priority + filtered_sinhala + filtered_other
            if snippets_filtered > 0:
                logger.info(f"[Step 3] Filtered out {snippets_filtered} irrelevant URLs via snippets")
            if filtered_priority:
                logger.info(f"[Step 3] {len(filtered_priority)} Wikipedia URLs always included")

        # Cap scrape targets — Wikipedia already at front, so they're always included
        scrape_targets = scrape_targets[:8]

        # ===== Step 4: Scrape sources (sequential with short timeouts) =====
        logger.info(f"[Step 4] Scraping {len(scrape_targets)} sources...")
        scraped_sources: List[ScrapedSource] = []

        for result in scrape_targets:
            try:
                source = self.scraper.scrape_url(result['url'])
                source.title = result.get('title', source.title)
                scraped_sources.append(source)
            except Exception as e:
                logger.warning(f"Failed to scrape {result['url']}: {e}")
                # Continue to next URL even if this one fails
                continue
            
            time.sleep(0.1)  # Very minimal rate limiting

        # ===== Step 5: Compare using batch encoding + sentence-level matching =====
        logger.info("[Step 5] Comparing with semantic similarity (batch)...")
        logger.info(f"[DEBUG] Suspicious text (first 150 chars): {suspicious_text[:150]}")
        logger.info(f"[DEBUG] Embedding available: {self.embedding_available}")
        logger.info(f"[DEBUG] Suspicious full emb shape: {suspicious_full_emb.shape if suspicious_full_emb is not None else 'None'}")
        all_matches: List[PlagiarismResult] = []
        paragraphs_checked = 0

        for source in scraped_sources:
            if source.error or not source.paragraphs:
                logger.info(f"[DEBUG] Skipping source {source.url[:60]}: error={source.error}, paras={len(source.paragraphs)}")
                continue

            # Filter paragraphs: keep only those with Sinhala content
            # This prevents cross-language false positives (English matching Sinhala via multilingual model)
            # Require minimum 50 chars and 3+ Sinhala chars to avoid short fragment false matches
            valid_paragraphs = [p for p in source.paragraphs if len(p) >= 50 and self._has_sinhala(p, 3)]

            if not valid_paragraphs:
                # Fallback: slightly relaxed (30 chars, any Sinhala)
                valid_paragraphs = [p for p in source.paragraphs
                                    if len(p) >= 30 and re.search(r'[\u0D80-\u0DFF]', p)]

            if not valid_paragraphs:
                logger.info(f"[DEBUG] No Sinhala paragraphs for {source.url[:60]}, skipping")
                continue

            paragraphs_checked += len(valid_paragraphs)
            logger.info(f"[DEBUG] Source: {source.url[:60]} - {len(valid_paragraphs)} valid paragraphs")

            # --- Batch encode all paragraphs for this source in ONE call ---
            para_embeddings = None
            if self.embedding_available and suspicious_full_emb is not None:
                try:
                    para_embeddings = self._batch_encode(valid_paragraphs)
                    logger.info(f"[DEBUG] Para embeddings shape: {para_embeddings.shape}")
                except Exception as e:
                    logger.warning(f"Batch encode paragraphs failed: {e}")

            # --- Compute full-text scores for all paragraphs at once ---
            full_text_scores = None
            if para_embeddings is not None and suspicious_full_emb is not None:
                full_text_scores = np.dot(para_embeddings, suspicious_full_emb)  # shape: (N,)
                logger.info(f"[DEBUG] Full text scores: min={float(np.min(full_text_scores)):.4f}, max={float(np.max(full_text_scores)):.4f}, mean={float(np.mean(full_text_scores)):.4f}")

            # --- Process each paragraph ---
            for idx, paragraph in enumerate(valid_paragraphs):
                try:
                    embedding_score = None
                    best_sentence_text = None

                    if full_text_scores is not None:
                        embedding_score = float(full_text_scores[idx])
                        if idx < 3:  # Log first 3 paragraphs for debugging
                            logger.info(f"[DEBUG] Para[{idx}] emb_score={embedding_score:.4f}, text={paragraph[:100]}")

                        # Sentence-level matching for ambiguous scores (0.3-0.7)
                        # Catches partial matches in long texts
                        if (0.3 <= embedding_score <= 0.7
                                and suspicious_sent_embs is not None
                                and len(suspicious_sent_embs) > 1):
                            para_sentences = split_sentences_simple(paragraph)
                            para_sentences = [s for s in para_sentences if len(s) >= 10]

                            if para_sentences:
                                try:
                                    para_sent_embs = self._batch_encode(para_sentences)
                                    if para_sent_embs.size > 0:
                                        # Similarity matrix: suspicious_sents x para_sents
                                        sim_matrix = np.dot(suspicious_sent_embs, para_sent_embs.T)
                                        sentence_max = float(np.max(sim_matrix))

                                        # Find best sentence pair for display
                                        if sentence_max > embedding_score:
                                            max_idx = np.unravel_index(np.argmax(sim_matrix), sim_matrix.shape)
                                            susp_sent = suspicious_sentences[max_idx[0]]
                                            para_sent = para_sentences[max_idx[1]]
                                            best_sentence_text = f"{susp_sent[:100]} ↔ {para_sent[:100]}"

                                        embedding_score = max(embedding_score, sentence_max)
                                except Exception as e:
                                    logger.warning(f"Sentence-level comparison error: {e}")

                    # Calculate custom score
                    custom_score = self._compute_custom_score(suspicious_text, paragraph)

                    # Determine final score and case type
                    if embedding_score is not None:
                        score, case_type, method = self._classify_match(embedding_score, custom_score)
                    elif self.hybrid_available and self.hybrid_detector:
                        result = self.hybrid_detector.detect(suspicious_text, paragraph)
                        score = result["final_score"]
                        case_type = result["case_type"]
                        method = result["method"]
                        custom_score = result["custom_score"]
                        embedding_score = result.get("embedding_score")
                    else:
                        score = custom_score
                        case_type = "basic"
                        method = "jaccard"
                        embedding_score = None

                    # Debug: log scores for first few paragraphs
                    if idx < 3:
                        logger.info(f"[DEBUG] Para[{idx}] FINAL: score={score:.4f}, emb={embedding_score}, custom={custom_score:.4f}, case={case_type}, threshold={threshold}")

                    # Add if above threshold
                    if score >= threshold:
                        # Find best matching user paragraph (full text, no truncation)
                        user_matched = suspicious_text
                        if user_para_embs is not None and para_embeddings is not None:
                            try:
                                web_para_emb = para_embeddings[idx]
                                user_sims = np.dot(user_para_embs, web_para_emb)
                                best_user_idx = int(np.argmax(user_sims))
                                user_matched = user_paragraphs[best_user_idx]
                            except Exception as e:
                                logger.warning(f"User paragraph matching failed: {e}")

                        match = PlagiarismResult(
                            source_url=source.url,
                            source_title=source.title,
                            matched_text=paragraph,
                            similarity_score=score,
                            case_type=case_type,
                            method=method,
                            custom_score=custom_score,
                            embedding_score=embedding_score,
                            matched_sentence=best_sentence_text,
                            user_matched_text=user_matched
                        )
                        all_matches.append(match)

                except Exception as e:
                    logger.warning(f"Comparison error: {e}")
                    continue

        # ===== Step 6: Sort and deduplicate (top 3 per URL) =====
        all_matches.sort(key=lambda x: x.similarity_score, reverse=True)

        url_matches = defaultdict(list)
        for match in all_matches:
            url_matches[match.source_url].append(match)

        unique_matches = []
        for url, matches in url_matches.items():
            matches.sort(key=lambda x: x.similarity_score, reverse=True)
            unique_matches.extend(matches[:3])

        unique_matches.sort(key=lambda x: x.similarity_score, reverse=True)

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
                    "embedding_score": round(m.embedding_score, 4) if m.embedding_score is not None else None,
                    "matched_sentence": m.matched_sentence,
                    "user_matched_text": m.user_matched_text
                }
                for m in unique_matches[:10]
            ],
            "statistics": {
                "queries_used": len(queries),
                "sources_searched": len(all_search_results),
                "sources_scraped": len([s for s in scraped_sources if not s.error]),
                "snippets_filtered": snippets_filtered,
                "paragraphs_checked": paragraphs_checked,
                "matches_found": len(unique_matches),
                "processing_time_seconds": round(processing_time, 2)
            },
            "metadata": {
                "search_engine": "DuckDuckGo",
                "scraper": "Playwright" if PLAYWRIGHT_AVAILABLE else "requests",
                "extractor": "Trafilatura" if TRAFILATURA_AVAILABLE else "BeautifulSoup",
                "detector": "HybridMethod (Embedding-First + Sentence-Level)" if self.embedding_available else ("ApprovedHybridDetector" if self.hybrid_available else "Jaccard")
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
