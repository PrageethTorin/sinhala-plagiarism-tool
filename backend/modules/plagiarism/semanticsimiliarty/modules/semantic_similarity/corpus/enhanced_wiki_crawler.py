"""
Enhanced Wikipedia Crawler for Sinhala Web Corpus
Target: 10,000+ documents for FAISS indexing

Features:
- Crawl multiple categories systematically
- Extract clean paragraphs
- Store in SQLite for persistence
- Build FAISS index for vector search
"""

import os
import re
import sys
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Generator
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix Windows console encoding for Sinhala characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass  # Python < 3.7

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sinhala_corpus.db")


class EnhancedWikiCrawler:
    """
    Comprehensive Sinhala Wikipedia crawler for building a large corpus
    """

    WIKI_BASE = "https://si.wikipedia.org"
    API_URL = "https://si.wikipedia.org/w/api.php"

    # Extended category list for comprehensive coverage
    CATEGORIES = [
        # History & Culture
        "ශ්‍රී_ලංකාවේ_ඉතිහාසය",
        "සිංහල_සංස්කෘතිය",
        "බෞද්ධ_ධර්මය",
        "හින්දු_ආගම",
        "ශ්‍රී_ලංකාවේ_ප්‍රාදේශීය_ඉතිහාසය",

        # Geography
        "ශ්‍රී_ලංකාවේ_භූගෝලය",
        "ශ්‍රී_ලංකාවේ_නගර",
        "ශ්‍රී_ලංකාවේ_ගම්මාන",
        "ශ්‍රී_ලංකාවේ_ගංගා",
        "ශ්‍රී_ලංකාවේ_කඳු",

        # Science & Technology
        "විද්‍යාව",
        "තාක්ෂණය",
        "ගණිතය",
        "භෞතික_විද්‍යාව",
        "ජීව_විද්‍යාව",
        "රසායන_විද්‍යාව",
        "පරිගණක_විද්‍යාව",

        # Arts & Literature
        "සිංහල_සාහිත්‍යය",
        "සිංහල_කවිය",
        "සිංහල_නාට්‍ය",
        "සිංහල_සංගීතය",
        "සිංහල_චිත්‍ර_කලාව",

        # Sports
        "ක්‍රීඩා",
        "ක්‍රිකට්",
        "පාපන්දු",
        "රග්බි",
        "මලල_ක්‍රීඩා",

        # Education
        "ශ්‍රී_ලංකාවේ_අධ්‍යාපනය",
        "විශ්වවිද්‍යාල",
        "පාසල්",

        # Economy
        "ශ්‍රී_ලංකාවේ_ආර්ථිකය",
        "කෘෂිකර්මාන්තය",
        "සංචාරක_කර්මාන්තය",
        "ධීවර_කර්මාන්තය",

        # Health
        "සෞඛ්‍යය",
        "වෛද්‍ය_විද්‍යාව",
        "රෝග",

        # Environment
        "පරිසරය",
        "ශ්‍රී_ලංකාවේ_සත්ත්ව_විශේෂ",
        "ශ්‍රී_ලංකාවේ_ශාක_විශේෂ",

        # Politics
        "ශ්‍රී_ලංකාවේ_දේශපාලනය",
        "ශ්‍රී_ලංකාවේ_ජනාධිපතිවරු",
        "ශ්‍රී_ලංකාවේ_අගමැතිවරු"
    ]

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SinhalaPlagiarismResearch/1.0 (Academic Research; Contact: research@university.lk)"
        })
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for corpus storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE,
                content TEXT NOT NULL,
                category TEXT,
                word_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paragraphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                paragraph_text TEXT NOT NULL,
                char_count INTEGER,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON documents(category)
        ''')

        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")

    def get_category_pages(self, category: str, limit: int = 100) -> List[Dict]:
        """Get list of pages in a Wikipedia category using API"""
        pages = []

        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"ප්‍රවර්ගය:{category}",
            "cmlimit": min(limit, 500),
            "cmtype": "page",
            "format": "json"
        }

        try:
            response = self.session.get(self.API_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if "query" in data and "categorymembers" in data["query"]:
                for member in data["query"]["categorymembers"]:
                    pages.append({
                        "pageid": member["pageid"],
                        "title": member["title"],
                        "url": f"{self.WIKI_BASE}/wiki/{member['title'].replace(' ', '_')}"
                    })

        except Exception as e:
            print(f"Error fetching category {category}: {e}")

        return pages

    def crawl_page(self, url: str, title: str = None) -> Optional[Dict]:
        """Crawl a single Wikipedia page and extract content"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Get title if not provided
            if not title:
                title_tag = soup.find("h1", {"id": "firstHeading"})
                title = title_tag.get_text(strip=True) if title_tag else "Unknown"

            # Remove unwanted elements
            for tag in soup(["script", "style", "table", "sup", "span.reference",
                             "div.navbox", "div.reflist", "div.infobox"]):
                tag.extract()

            # Get main content
            content_div = soup.find("div", {"id": "mw-content-text"})
            if not content_div:
                return None

            # Extract paragraphs
            paragraphs = []
            full_text = []

            for p in content_div.find_all("p"):
                text = p.get_text(strip=True)

                # Clean text
                text = re.sub(r'\[\d+\]', '', text)  # Remove reference numbers
                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

                # Filter: min 50 chars, contains Sinhala
                if len(text) >= 50 and self._contains_sinhala(text):
                    paragraphs.append(text)
                    full_text.append(text)

            if not paragraphs:
                return None

            content = "\n\n".join(full_text)

            return {
                "title": title,
                "url": url,
                "content": content,
                "paragraphs": paragraphs,
                "word_count": len(content.split())
            }

        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

    def _contains_sinhala(self, text: str) -> bool:
        """Check if text contains significant Sinhala content"""
        sinhala_chars = sum(1 for c in text if '\u0D80' <= c <= '\u0DFF')
        return sinhala_chars > len(text) * 0.3

    def save_document(self, doc: Dict, category: str):
        """Save document to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert document
            cursor.execute('''
                INSERT OR IGNORE INTO documents (title, url, content, category, word_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (doc["title"], doc["url"], doc["content"], category, doc["word_count"]))

            doc_id = cursor.lastrowid

            # Insert paragraphs
            if doc_id:
                for para in doc["paragraphs"]:
                    cursor.execute('''
                        INSERT INTO paragraphs (document_id, paragraph_text, char_count)
                        VALUES (?, ?, ?)
                    ''', (doc_id, para, len(para)))

            conn.commit()
            return True

        except sqlite3.IntegrityError:
            return False  # Duplicate URL
        finally:
            conn.close()

    def crawl_category(self, category: str, max_pages: int = 50) -> int:
        """Crawl all pages in a category"""
        print(f"\n--- Crawling category: {category} ---")

        pages = self.get_category_pages(category, max_pages)
        print(f"Found {len(pages)} pages")

        crawled = 0
        for page in pages:
            doc = self.crawl_page(page["url"], page["title"])
            if doc:
                if self.save_document(doc, category):
                    crawled += 1
                    print(f"  [{crawled}] {page['title'][:40]}... ({doc['word_count']} words)")

            # Rate limiting
            time.sleep(0.5)

        return crawled

    def crawl_all_categories(self, max_per_category: int = 50):
        """Crawl all defined categories"""
        print("=" * 60)
        print("SINHALA WIKIPEDIA CORPUS BUILDER")
        print(f"Categories: {len(self.CATEGORIES)}")
        print(f"Max pages per category: {max_per_category}")
        print("=" * 60)

        total_crawled = 0
        for i, category in enumerate(self.CATEGORIES, 1):
            print(f"\n[{i}/{len(self.CATEGORIES)}] Category: {category}")
            count = self.crawl_category(category, max_per_category)
            total_crawled += count
            print(f"  Crawled: {count} documents")

            # Pause between categories
            time.sleep(1)

        print("\n" + "=" * 60)
        print(f"CRAWLING COMPLETE - Total documents: {total_crawled}")
        print("=" * 60)

        return total_crawled

    def get_corpus_stats(self) -> Dict:
        """Get statistics about the corpus"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total documents
        cursor.execute("SELECT COUNT(*) FROM documents")
        stats["total_documents"] = cursor.fetchone()[0]

        # Total paragraphs
        cursor.execute("SELECT COUNT(*) FROM paragraphs")
        stats["total_paragraphs"] = cursor.fetchone()[0]

        # Total words
        cursor.execute("SELECT SUM(word_count) FROM documents")
        stats["total_words"] = cursor.fetchone()[0] or 0

        # Documents per category
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM documents
            GROUP BY category
            ORDER BY count DESC
        ''')
        stats["by_category"] = dict(cursor.fetchall())

        conn.close()
        return stats

    def export_for_faiss(self, output_path: str = None) -> str:
        """Export paragraphs for FAISS indexing"""
        output_path = output_path or os.path.join(BASE_DIR, "corpus_paragraphs.txt")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT p.paragraph_text, d.title, d.url
            FROM paragraphs p
            JOIN documents d ON p.document_id = d.id
            WHERE p.char_count >= 80
        ''')

        with open(output_path, 'w', encoding='utf-8') as f:
            count = 0
            for row in cursor:
                # Format: paragraph|||title|||url
                f.write(f"{row[0]}|||{row[1]}|||{row[2]}\n")
                count += 1

        conn.close()
        print(f"Exported {count} paragraphs to {output_path}")
        return output_path

    def get_random_paragraphs(self, count: int = 100) -> List[str]:
        """Get random paragraphs for testing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT paragraph_text FROM paragraphs
            WHERE char_count >= 80
            ORDER BY RANDOM()
            LIMIT ?
        ''', (count,))

        paragraphs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return paragraphs


def build_corpus(max_per_category: int = 30):
    """Main function to build the corpus"""
    crawler = EnhancedWikiCrawler()

    # Crawl Wikipedia
    crawler.crawl_all_categories(max_per_category=max_per_category)

    # Show stats
    stats = crawler.get_corpus_stats()
    print("\n=== CORPUS STATISTICS ===")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Paragraphs: {stats['total_paragraphs']}")
    print(f"Total Words: {stats['total_words']:,}")

    print("\nDocuments by Category:")
    for cat, count in list(stats['by_category'].items())[:10]:
        print(f"  {cat}: {count}")

    # Export for FAISS
    crawler.export_for_faiss()

    return stats


if __name__ == "__main__":
    build_corpus(max_per_category=30)
