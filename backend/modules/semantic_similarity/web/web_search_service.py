"""
Comprehensive Web Search Service for Sinhala Plagiarism Detection
Combines Google Custom Search API with FAISS corpus for complete coverage
"""

import os
import time
import json
import hashlib
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import parent modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import normalize_sinhala, split_paragraphs, split_sentences_simple


# ========================================
# SINHALA STOPWORDS (Enhanced based on Rajamanthri 2020)
# ========================================
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
}


def remove_stopwords(text: str) -> str:
    """Remove Sinhala stopwords from text for better search queries."""
    if not text:
        return ""
    words = text.split()
    filtered = [w for w in words if w not in SINHALA_STOPWORDS]
    return ' '.join(filtered)


@dataclass
class SentenceMatch:
    """Represents a matched sentence pair between input and source"""
    input_sentence: str
    source_sentence: str
    similarity_score: float
    case_type: str
    method: str


@dataclass
class WebSearchResult:
    """Represents a web search result with extracted content"""
    url: str
    title: str
    snippet: str
    paragraphs: List[str] = field(default_factory=list)
    fetch_time: float = 0.0
    error: Optional[str] = None


@dataclass
class PlagiarismMatch:
    """Represents a plagiarism match found in web content"""
    source_url: str
    source_title: str
    matched_text: str
    similarity_score: float
    case_type: str
    method: str
    custom_score: float
    embedding_score: Optional[float] = None


class WebSearchCache:
    """Simple file-based cache for web search results"""

    def __init__(self, cache_dir: str = None, ttl_hours: int = 24):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "search_cache")
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, query: str) -> str:
        """Generate cache file path for a query"""
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{query_hash}.json")

    def get(self, query: str) -> Optional[Dict]:
        """Get cached result if valid"""
        cache_path = self._get_cache_path(query)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check TTL
            cached_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
            if datetime.now() - cached_time > self.ttl:
                os.remove(cache_path)
                return None

            return data.get('results')
        except Exception:
            return None

    def set(self, query: str, results: List[Dict]) -> None:
        """Cache search results"""
        cache_path = self._get_cache_path(query)

        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'results': results
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")


class GoogleSearchService:
    """Google Custom Search API integration"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("CSE_ID") or os.getenv("SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SinhalaPlagiarismChecker/1.0"
        })

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # seconds

        self._check_credentials()

    def _check_credentials(self) -> None:
        """Check if API credentials are configured"""
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not configured - web search will be limited")
        if not self.search_engine_id:
            logger.warning("CSE_ID/SEARCH_ENGINE_ID not configured - web search will be limited")

    @property
    def is_configured(self) -> bool:
        """Check if the service is properly configured"""
        return bool(self.api_key and self.search_engine_id)

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def search(self, query: str, num_results: int = 5, language: str = "si") -> List[Dict]:
        """
        Search Google for Sinhala content

        Args:
            query: Search query (can be Sinhala text)
            num_results: Number of results to return (max 10)
            language: Language restriction

        Returns:
            List of search results with url, title, snippet
        """
        if not self.is_configured:
            logger.warning("Google Search not configured, returning empty results")
            return []

        self._rate_limit()

        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10),
            "lr": f"lang_{language}",  # Language restriction
            "safe": "active"
        }

        try:
            response = self.session.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("items", []):
                results.append({
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "displayLink": item.get("displayLink", "")
                })

            logger.info(f"Google search returned {len(results)} results for query")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Google search failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Google response: {e}")
            return []


class WebContentExtractor:
    """Extract and process content from web pages"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Research Bot",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "si,en;q=0.9"
        })
        self.timeout = 10

    def extract_content(self, url: str) -> WebSearchResult:
        """
        Extract Sinhala text content from a URL

        Args:
            url: Web page URL

        Returns:
            WebSearchResult with extracted paragraphs
        """
        start_time = time.time()
        result = WebSearchResult(url=url, title="", snippet="")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Get title
            title_tag = soup.find("title")
            result.title = title_tag.get_text(strip=True) if title_tag else ""

            # Remove unwanted elements
            for tag in soup(["script", "style", "header", "footer", "nav",
                           "aside", "noscript", "iframe", "form"]):
                tag.extract()

            # Extract paragraphs
            paragraphs = []
            for p in soup.find_all(["p", "article", "div"]):
                text = p.get_text(" ", strip=True)

                # Filter: must have substantial content and Sinhala characters
                if len(text) >= 50:
                    sinhala_chars = sum(1 for c in text if '\u0D80' <= c <= '\u0DFF')
                    sinhala_ratio = sinhala_chars / len(text) if text else 0

                    if sinhala_ratio > 0.3:  # At least 30% Sinhala
                        normalized = normalize_sinhala(text)
                        if normalized and len(normalized) >= 30:
                            paragraphs.append(normalized)

            # Remove duplicates while preserving order
            seen = set()
            unique_paragraphs = []
            for p in paragraphs:
                if p not in seen:
                    seen.add(p)
                    unique_paragraphs.append(p)

            result.paragraphs = unique_paragraphs[:20]  # Limit to 20 paragraphs
            result.fetch_time = time.time() - start_time

            logger.info(f"Extracted {len(result.paragraphs)} paragraphs from {url}")

        except requests.exceptions.RequestException as e:
            result.error = str(e)
            logger.warning(f"Failed to fetch {url}: {e}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"Error extracting content from {url}: {e}")

        return result


class WebPlagiarismChecker:
    """
    Complete web plagiarism checking service
    Combines Google search + content extraction + similarity detection
    """

    def __init__(self):
        self.google_search = GoogleSearchService()
        self.content_extractor = WebContentExtractor()
        self.cache = WebSearchCache()

        # Import hybrid detector
        try:
            from approved_hybrid import ApprovedHybridDetector
            self.detector = ApprovedHybridDetector()
            self.detector_available = True
        except ImportError:
            try:
                from ..approved_hybrid import ApprovedHybridDetector
                self.detector = ApprovedHybridDetector()
                self.detector_available = True
            except ImportError:
                logger.warning("ApprovedHybridDetector not available")
                self.detector = None
                self.detector_available = False

        logger.info("WebPlagiarismChecker initialized")

    def _create_search_query(self, text: str, max_length: int = 150) -> str:
        """
        Create an effective search query from input text.

        ENHANCED (based on Rajamanthri 2020):
        - Remove Sinhala stopwords for better keyword matching
        - Extract key content words for more precise Google search

        Args:
            text: Input text (potentially long)
            max_length: Maximum query length

        Returns:
            Optimized search query with stopwords removed
        """
        # Normalize and get first meaningful portion
        normalized = normalize_sinhala(text)

        # Split into sentences and take first few
        sentences = split_sentences_simple(normalized)

        if sentences:
            query = sentences[0]
            # Add more sentences if under limit
            for sent in sentences[1:3]:
                if len(query) + len(sent) + 1 <= max_length:
                    query += " " + sent
                else:
                    break

            # ENHANCEMENT: Remove stopwords for better search
            query_without_stopwords = remove_stopwords(query)

            # Use stopword-removed version if it has enough content
            if len(query_without_stopwords.split()) >= 3:
                return query_without_stopwords[:max_length]

            return query[:max_length]

        # ENHANCEMENT: Remove stopwords from normalized text
        filtered = remove_stopwords(normalized)
        if len(filtered.split()) >= 3:
            return filtered[:max_length]

        return normalized[:max_length]

    def search_web(self, text: str, num_results: int = 5) -> List[WebSearchResult]:
        """
        Search the web for potential plagiarism sources

        Args:
            text: Text to check for plagiarism
            num_results: Number of web results to fetch

        Returns:
            List of WebSearchResult with extracted content
        """
        query = self._create_search_query(text)

        # Check cache first
        cached = self.cache.get(query)
        if cached:
            logger.info("Using cached search results")
            return [WebSearchResult(**r) for r in cached]

        # Perform Google search
        search_results = self.google_search.search(query, num_results)

        if not search_results:
            logger.warning("No search results found")
            return []

        # Extract content from each URL
        web_results = []
        for result in search_results:
            web_result = self.content_extractor.extract_content(result["url"])
            web_result.title = result.get("title", web_result.title)
            web_result.snippet = result.get("snippet", "")
            web_results.append(web_result)

            # Rate limiting between fetches
            time.sleep(0.5)

        # Cache results
        cache_data = [
            {
                "url": r.url,
                "title": r.title,
                "snippet": r.snippet,
                "paragraphs": r.paragraphs,
                "fetch_time": r.fetch_time,
                "error": r.error
            }
            for r in web_results
        ]
        self.cache.set(query, cache_data)

        return web_results

    def _compare_sentences(
        self,
        input_sentences: List[str],
        source_sentences: List[str],
        threshold: float = 0.4
    ) -> List[SentenceMatch]:
        """
        ENHANCED: Sentence-level comparison (based on Rajamanthri 2020).

        Compares each input sentence against each source sentence
        for granular plagiarism detection.

        Args:
            input_sentences: List of sentences from user input
            source_sentences: List of sentences from web source
            threshold: Minimum similarity to consider a match

        Returns:
            List of SentenceMatch objects for matching sentence pairs
        """
        matches = []

        for input_sent in input_sentences:
            if len(input_sent.strip()) < 10:
                continue

            best_match = None
            best_score = 0.0

            for source_sent in source_sentences:
                if len(source_sent.strip()) < 10:
                    continue

                try:
                    if self.detector_available and self.detector:
                        result = self.detector.detect(input_sent, source_sent)
                        score = result["final_score"]
                        case_type = result["case_type"]
                        method = result["method"]
                    else:
                        # Fallback: Jaccard similarity
                        words1 = set(input_sent.split())
                        words2 = set(source_sent.split())
                        if words1 and words2:
                            score = len(words1 & words2) / len(words1 | words2)
                        else:
                            score = 0.0
                        case_type = "basic"
                        method = "jaccard"

                    if score > best_score and score >= threshold:
                        best_score = score
                        best_match = SentenceMatch(
                            input_sentence=input_sent[:200],
                            source_sentence=source_sent[:200],
                            similarity_score=score,
                            case_type=case_type,
                            method=method
                        )
                except Exception as e:
                    logger.warning(f"Sentence comparison error: {e}")
                    continue

            if best_match:
                matches.append(best_match)

        return matches

    def check_plagiarism(
        self,
        text: str,
        threshold: float = 0.5,
        num_web_results: int = 5,
        enable_sentence_level: bool = True
    ) -> Dict:
        """
        Complete plagiarism check against web sources.

        ENHANCED (based on Rajamanthri 2020):
        - Sentence-level comparison for granular results
        - Shows which specific sentences matched
        - Better query preprocessing with stopword removal

        Args:
            text: Text to check
            threshold: Similarity threshold for flagging
            num_web_results: Number of web pages to search
            enable_sentence_level: Enable sentence-by-sentence comparison

        Returns:
            Dictionary with matches, sentence matches, statistics, and metadata
        """
        start_time = time.time()

        # Normalize input
        normalized_text = normalize_sinhala(text)
        if not normalized_text or len(normalized_text) < 20:
            return {
                "success": False,
                "error": "Input text too short or invalid",
                "matches": [],
                "sentence_matches": [],
                "processing_time": time.time() - start_time
            }

        # Split input into sentences for sentence-level comparison
        input_sentences = split_sentences_simple(normalized_text)

        # Search web
        web_results = self.search_web(text, num_web_results)

        if not web_results:
            return {
                "success": True,
                "message": "No web sources found to compare",
                "matches": [],
                "sentence_matches": [],
                "sources_checked": 0,
                "processing_time": time.time() - start_time
            }

        # Compare against each paragraph from web results
        all_matches: List[PlagiarismMatch] = []
        all_sentence_matches: List[Dict] = []
        sources_checked = 0
        paragraphs_checked = 0
        sentences_checked = 0

        for web_result in web_results:
            if web_result.error or not web_result.paragraphs:
                continue

            sources_checked += 1

            # Collect all sentences from this source
            source_sentences = []
            for paragraph in web_result.paragraphs:
                source_sentences.extend(split_sentences_simple(paragraph))

            for paragraph in web_result.paragraphs:
                paragraphs_checked += 1

                # Use detector if available
                if self.detector_available and self.detector:
                    try:
                        result = self.detector.detect(normalized_text, paragraph)

                        if result["final_score"] >= threshold:
                            match = PlagiarismMatch(
                                source_url=web_result.url,
                                source_title=web_result.title,
                                matched_text=paragraph[:500],  # Limit length
                                similarity_score=result["final_score"],
                                case_type=result["case_type"],
                                method=result["method"],
                                custom_score=result["custom_score"],
                                embedding_score=result.get("embedding_score")
                            )
                            all_matches.append(match)
                    except Exception as e:
                        logger.error(f"Detector error: {e}")
                else:
                    # Fallback: simple word overlap
                    words1 = set(normalized_text.split())
                    words2 = set(paragraph.split())
                    if words1 and words2:
                        overlap = len(words1 & words2) / len(words1 | words2)
                        if overlap >= threshold:
                            match = PlagiarismMatch(
                                source_url=web_result.url,
                                source_title=web_result.title,
                                matched_text=paragraph[:500],
                                similarity_score=overlap,
                                case_type="basic",
                                method="word_overlap",
                                custom_score=overlap
                            )
                            all_matches.append(match)

            # ENHANCEMENT: Sentence-level comparison
            if enable_sentence_level and source_sentences:
                sentences_checked += len(source_sentences)
                sentence_matches = self._compare_sentences(
                    input_sentences,
                    source_sentences,
                    threshold=threshold - 0.1  # Slightly lower threshold for sentences
                )

                for sm in sentence_matches:
                    all_sentence_matches.append({
                        "source_url": web_result.url,
                        "source_title": web_result.title,
                        "input_sentence": sm.input_sentence,
                        "source_sentence": sm.source_sentence,
                        "similarity_score": round(sm.similarity_score, 4),
                        "case_type": sm.case_type,
                        "method": sm.method
                    })

        # Sort by similarity score
        all_matches.sort(key=lambda x: x.similarity_score, reverse=True)
        all_sentence_matches.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Deduplicate by URL (keep highest score per source)
        seen_urls = set()
        unique_matches = []
        for match in all_matches:
            if match.source_url not in seen_urls:
                seen_urls.add(match.source_url)
                unique_matches.append(match)

        # Deduplicate sentence matches (keep top matches)
        seen_input_sentences = set()
        unique_sentence_matches = []
        for sm in all_sentence_matches:
            if sm["input_sentence"] not in seen_input_sentences:
                seen_input_sentences.add(sm["input_sentence"])
                unique_sentence_matches.append(sm)

        # Calculate summary statistics
        max_score = max((m.similarity_score for m in unique_matches), default=0)
        avg_score = sum(m.similarity_score for m in unique_matches) / len(unique_matches) if unique_matches else 0

        # Consider sentence matches for max score
        if unique_sentence_matches:
            sentence_max = max(sm["similarity_score"] for sm in unique_sentence_matches)
            max_score = max(max_score, sentence_max)

        # Determine verdict
        if max_score >= 0.9:
            verdict = "High Plagiarism Risk"
        elif max_score >= 0.7:
            verdict = "Moderate Plagiarism Risk"
        elif max_score >= 0.5:
            verdict = "Low Plagiarism Risk"
        else:
            verdict = "Original"

        processing_time = time.time() - start_time

        return {
            "success": True,
            "verdict": verdict,
            "max_similarity": round(max_score, 4),
            "avg_similarity": round(avg_score, 4),
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
                for m in unique_matches[:10]  # Limit to top 10
            ],
            "sentence_matches": unique_sentence_matches[:15],  # Top 15 sentence matches
            "statistics": {
                "sources_checked": sources_checked,
                "paragraphs_checked": paragraphs_checked,
                "sentences_checked": sentences_checked,
                "matches_found": len(unique_matches),
                "sentence_matches_found": len(unique_sentence_matches),
                "processing_time": round(processing_time, 2)
            },
            "metadata": {
                "threshold": threshold,
                "web_search_enabled": self.google_search.is_configured,
                "detector_available": self.detector_available,
                "sentence_level_enabled": enable_sentence_level,
                "enhancement": "Rajamanthri 2020 inspired"
            }
        }


# Convenience function for API usage
def check_web_plagiarism(text: str, threshold: float = 0.5) -> Dict:
    """
    Quick function to check text for web plagiarism

    Args:
        text: Text to check
        threshold: Similarity threshold

    Returns:
        Plagiarism check results
    """
    checker = WebPlagiarismChecker()
    return checker.check_plagiarism(text, threshold)


if __name__ == "__main__":
    # Test the service
    print("=" * 60)
    print("WEB PLAGIARISM CHECKER TEST")
    print("=" * 60)

    # Check if credentials are configured
    checker = WebPlagiarismChecker()

    if not checker.google_search.is_configured:
        print("\nGoogle API not configured. Set environment variables:")
        print("  GOOGLE_API_KEY=your_api_key")
        print("  CSE_ID=your_search_engine_id")
        print("\nTo get these:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a project and enable Custom Search API")
        print("  3. Create credentials (API key)")
        print("  4. Go to https://programmablesearchengine.google.com/")
        print("  5. Create a search engine and get the ID")
    else:
        print("\nGoogle API configured!")

        # Test with sample text
        test_text = "sri lanka is a beautiful island nation"
        print(f"\nTest query: {test_text[:50]}...")

        result = checker.check_plagiarism(test_text, threshold=0.3)
        print(f"\nResult: {json.dumps(result, indent=2, ensure_ascii=False)}")
