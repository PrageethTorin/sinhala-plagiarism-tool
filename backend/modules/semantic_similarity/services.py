"""
Services for text processing and similarity detection
"""
import re
import numpy as np
from typing import List, Set, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import jellyfish
import pdfplumber
import docx
import io
import chardet
from fastapi import UploadFile, HTTPException
import torch
from sentence_transformers import SentenceTransformer
import os


class SinhalaTextProcessor:
    """Processor for Sinhala text"""
    
    def __init__(self):
        self.sinhala_stopwords = self._load_sinhala_stopwords()
        self.sinhala_pattern = re.compile(r'[\u0D80-\u0DFF]+')
        
    def _load_sinhala_stopwords(self) -> Set[str]:
        """Load comprehensive Sinhala stopwords"""
        stopwords = {
            # Pronouns
            'මම', 'ඔබ', 'ඔහු', 'ඇය', 'අපි', 'ඔවුන්', 'මමත්', 'ඔබත්',
            # Articles/Demonstratives
            'මේ', 'ඒ', 'අර', 'මෙහි', 'එහි', 'අරේ',
            # Common Verbs
            'කර', 'කල', 'කරන', 'කරමින්', 'වී', 'වූ', 'වන', 'වේ',
            # Conjunctions
            'සහ', 'හෝ', 'නමුත්', 'එනමුත්', 'එහෙත්', 'වුවත්', 'වුවද',
            # Prepositions
            'ගැන', 'විසින්', 'සමග', 'පිළිබඳ', 'උදෙසා', 'සඳහා',
            # Common words
            'එක', 'දෙක', 'තුන', 'බොහෝ', 'සුළු', 'වැඩි', 'කුඩා', 'මහත්',
            # Question words
            'කවුද', 'මොකද', 'කොහෙද', 'කොහොමද', 'කවදාද', 'ඇයි',
            # Others
            'පමණ', 'තරම්', 'වැනි', 'ලෙස', 'පරිදි', 'යන', 'අයිති'
        }
        return stopwords
    
    def preprocess(self, text: str) -> str:
        """Preprocess Sinhala text with normalization"""
        if not text:
            return ""
        
        
        text = ' '.join(text.split())
        
        
        sinhala_text = ' '.join(self.sinhala_pattern.findall(text))
        
       
        sinhala_text = re.sub(r'[^\u0D80-\u0DFF\s]', '', sinhala_text)
        
       
        sinhala_text = ' '.join(sinhala_text.split())
        
        return sinhala_text
    
    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize Sinhala text into words"""
        
        tokens = [token for token in text.split() if token]
        
        
        tokens = [token for token in tokens if token not in self.sinhala_stopwords]
        
        return tokens
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """Tokenize Sinhala text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def extract_ngrams(self, text: str, n: int = 3) -> List[str]:
        """Extract n-grams from text"""
        tokens = self.tokenize_words(text)
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.append(ngram)
        return ngrams

class SimilarityDetector:
    """Detect similarity between texts"""
    
    def __init__(self):
        self.text_processor = SinhalaTextProcessor()
        
    def calculate_similarity(self, text1: str, text2: str, algorithm: str = "hybrid") -> Dict:
        """Calculate similarity between two Sinhala texts"""
        
     
        processed1 = self.text_processor.preprocess(text1)
        processed2 = self.text_processor.preprocess(text2)
        
        if not processed1 or not processed2:
            return {
                "similarity_score": 0.0,
                "components": {
                    "semantic": 0.0,
                    "lexical": 0.0,
                    "structural": 0.0,
                    "ngram": 0.0
                },
                "matches": []
            }
        
        # Tokenize for various analyses
        tokens1 = self.text_processor.tokenize_words(processed1)
        tokens2 = self.text_processor.tokenize_words(processed2)
        
       
        semantic_score = self._semantic_similarity(processed1, processed2)
        lexical_score = self._lexical_similarity(' '.join(tokens1), ' '.join(tokens2))
        
      
        structural_score = self._structural_similarity(text1, text2, tokens1, tokens2)
        
        # N-gram similarity with multiple n values
        ngram_score = self._multi_ngram_similarity(processed1, processed2)
        
        # Calculate word overlap
        word_overlap = self._calculate_word_overlap(tokens1, tokens2)
        
        # Combine scores based on algorithm
        if algorithm == "semantic":
            final_score = 0.7 * semantic_score + 0.3 * word_overlap
        elif algorithm == "lexical":
            final_score = 0.6 * lexical_score + 0.2 * ngram_score + 0.2 * word_overlap
        else:  # hybrid
            # Weighted combination for Sinhala text
            final_score = (
                0.4 * semantic_score +
                0.3 * lexical_score +
                0.1 * structural_score +
                0.1 * ngram_score +
                0.1 * word_overlap
            )
        
        final_score = max(0.0, min(1.0, final_score))
        
        
        matches = self._find_matches(text1, text2)
        
        return {
            "similarity_score": float(final_score),
            "components": {
                "semantic": float(semantic_score),
                "lexical": float(lexical_score),
                "structural": float(structural_score),
                "ngram": float(ngram_score)
            },
            "matches": matches
        }
    
    def _calculate_word_overlap(self, tokens1: List[str], tokens2: List[str]) -> float:
        """Calculate word overlap between two token lists"""
        if not tokens1 or not tokens2:
            return 0.0
        
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _multi_ngram_similarity(self, text1: str, text2: str) -> float:
        """Calculate n-gram similarity using multiple n values"""
        ngram_scores = []
        
        for n in [1, 2, 3]:  # Unigrams, bigrams, trigrams
            score = self._ngram_similarity(text1, text2, n)
            ngram_scores.append(score)
        
        
        return (0.2 * ngram_scores[0] + 0.3 * ngram_scores[1] + 0.5 * ngram_scores[2])
    
    def _structural_similarity(self, text1: str, text2: str, tokens1: List[str], tokens2: List[str]) -> float:
        """Calculate structural similarity"""
        
       
        sentences1 = self.text_processor.tokenize_sentences(text1)
        sentences2 = self.text_processor.tokenize_sentences(text2)
        
        if not sentences1 or not sentences2:
            return 0.0
        
        sentence_count_sim = 1 - abs(len(sentences1) - len(sentences2)) / max(len(sentences1), len(sentences2))
        
       
        avg_len1 = sum(len(s) for s in sentences1) / len(sentences1)
        avg_len2 = sum(len(s) for s in sentences2) / len(sentences2)
        
        if avg_len1 == 0 or avg_len2 == 0:
            avg_len_sim = 0.0
        else:
            avg_len_sim = 1 - abs(avg_len1 - avg_len2) / max(avg_len1, avg_len2)
        
       
        word_len1 = sum(len(w) for w in tokens1) / len(tokens1) if tokens1 else 0
        word_len2 = sum(len(w) for w in tokens2) / len(tokens2) if tokens2 else 0
        
        if word_len1 == 0 or word_len2 == 0:
            word_len_sim = 0.0
        else:
            word_len_sim = 1 - abs(word_len1 - word_len2) / max(word_len1, word_len2)
        
        
        return (0.4 * sentence_count_sim + 0.4 * avg_len_sim + 0.2 * word_len_sim)
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using TF-IDF"""
        try:
            vectorizer = TfidfVectorizer(tokenizer=self.text_processor.tokenize_words)
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return float(similarity[0][0])
        except Exception as e:
            print(f"Semantic similarity error: {str(e)}")
            return self._jaccard_similarity(text1, text2)
    
    def _lexical_similarity(self, text1: str, text2: str) -> float:
        """Calculate lexical similarity"""
        try:
            return jellyfish.jaro_winkler_similarity(text1, text2)
        except:
            
            return self._simple_string_similarity(text1, text2)
    
    def _simple_string_similarity(self, text1: str, text2: str) -> float:
        """Simple string similarity fallback"""
        if not text1 or not text2:
            return 0.0
        
       
        set1 = set(text1)
        set2 = set(text2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        """Calculate n-gram similarity"""
        ngrams1 = set(self.text_processor.extract_ngrams(text1, n))
        ngrams2 = set(self.text_processor.extract_ngrams(text2, n))
        if not ngrams1 and not ngrams2:
            return 0.0
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        return intersection / union if union > 0 else 0.0
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity"""
        words1 = set(self.text_processor.tokenize_words(text1))
        words2 = set(self.text_processor.tokenize_words(text2))
        if not words1 and not words2:
            return 0.0
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union > 0 else 0.0
    
    def _find_matches(self, text1: str, text2: str) -> List[Dict]:
        """Find matching segments between texts"""
        matches = []
        
        
        sentences1 = self.text_processor.tokenize_sentences(text1)
        sentences2 = self.text_processor.tokenize_sentences(text2)
        
        
        for i, sent1 in enumerate(sentences1[:10]):
            sent1 = sent1.strip()
            if not sent1 or len(sent1) < 10:
                continue
                
            best_match = None
            best_score = 0
            
            for j, sent2 in enumerate(sentences2[:10]):
                sent2 = sent2.strip()
                if not sent2 or len(sent2) < 10:
                    continue
                    
                similarity = self._lexical_similarity(sent1, sent2)
                
                if similarity > 0.5 and similarity > best_score:
                    best_score = similarity
                    best_match = {
                        "original_segment": sent1[:150] + "..." if len(sent1) > 150 else sent1,
                        "suspicious_segment": sent2[:150] + "..." if len(sent2) > 150 else sent2,
                        "similarity_score": similarity,
                        "match_type": "exact" if similarity > 0.9 else ("paraphrase" if similarity > 0.7 else "partial")
                    }
            
            if best_match:
                matches.append(best_match)
        
        
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return matches[:8]  # Return top 8 matches

class FileHandler:
    """Handle file uploads"""
    
    async def read_file(self, file: UploadFile) -> str:
        """Read text from different file types"""
        content = await file.read()

        if file.filename.endswith('.txt'):
            return self._read_text(content)
        elif file.filename.endswith('.pdf'):
            return self._read_pdf(content)
        elif file.filename.endswith('.docx'):
            return self._read_docx(content)
        else:
            return self._read_text(content)

    def _read_text(self, content: bytes) -> str:
        """Read text file with automatic encoding detection for Sinhala support"""
        # Check for UTF-8 BOM
        if content.startswith(b'\xef\xbb\xbf'):
            return content[3:].decode('utf-8')
        # Check for UTF-16 BOM
        if content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
            return content.decode('utf-16')

        # Try UTF-8 first
        try:
            decoded = content.decode('utf-8')
            # Verify it contains valid Sinhala characters (U+0D80-U+0DFF)
            if re.search(r'[\u0D80-\u0DFF]', decoded):
                return decoded
        except UnicodeDecodeError:
            pass

        # Auto-detect encoding using chardet
        detected = chardet.detect(content)
        encoding = detected.get('encoding', 'utf-8')
        confidence = detected.get('confidence', 0)

        try:
            decoded = content.decode(encoding)
            return decoded
        except (UnicodeDecodeError, LookupError):
            # Last resort: try common encodings
            for enc in ['utf-16', 'utf-16-le', 'utf-16-be', 'cp1252', 'latin-1']:
                try:
                    return content.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            raise HTTPException(status_code=400, detail="Could not detect file encoding")
    
    def _read_pdf(self, content: bytes) -> str:
        """Extract text from PDF (with Sinhala-friendly spacing)"""
        try:
            text = ""
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    # Higher x_tolerance prevents false spaces in Sinhala conjuncts
                    page_text = page.extract_text(x_tolerance=5)
                    if page_text:
                        text += page_text + "\n"
            # Remove spurious spaces between Sinhala characters
            text = self._fix_sinhala_spacing(text)
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

    def _fix_sinhala_spacing(self, text: str) -> str:
        """Remove false spaces inserted within Sinhala words by PDF extractors.

        Only removes spaces that break Sinhala conjuncts/ligatures:
        - After virama (්) or virama+ZWJ (්‍) followed by a consonant
        - After a vowel sign (dependent vowel) followed by a consonant
        """
        import re
        # Remove space after virama (්) + optional ZWJ (‍) before next Sinhala char
        # This fixes: ප්‍ර ණීත → ප්‍රණීත, ආශ්‍රි තව → ආශ්‍රිතව
        text = re.sub(r'(\u0DCA[\u200D]?)\s+([\u0D80-\u0DFF])', r'\1\2', text)
        # Remove space after dependent vowel signs before Sinhala consonants
        # Sinhala dependent vowels: \u0DCF-\u0DDF
        # This fixes: මප්‍රෝ ටීන්ද → මප්‍රෝටීන්ද
        text = re.sub(r'([\u0DCF-\u0DDF])\s+([\u0D9A-\u0DC6])', r'\1\2', text)
        return text
    
    def _read_docx(self, content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(io.BytesIO(content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")
        


# Fine-Tuned Transformer Embedding Service (XLM-R)

# HuggingFace Hub configuration
HUGGINGFACE_REPO_ID = "sandalidahanayake/sinhala-plagiarism-model"

def download_model_from_huggingface(model_path: str, repo_id: str = HUGGINGFACE_REPO_ID) -> bool:
    
    #Download the fine-tuned model from HuggingFace Hub if not exists locally.
    #Returns True if model is ready, False if download failed.
    
    if os.path.exists(model_path) and os.path.exists(os.path.join(model_path, "config.json")):
        return True  # Model already exists

    try:
        from huggingface_hub import snapshot_download
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Downloading model from HuggingFace: {repo_id}")
        print(f"[INFO] Model not found locally. Downloading from HuggingFace: {repo_id}")
        print("[INFO] This may take 2-3 minutes on first run...")

        snapshot_download(
            repo_id=repo_id,
            local_dir=model_path,
            local_dir_use_symlinks=False
        )

        logger.info("Model downloaded successfully!")
        print("[INFO] Model downloaded successfully!")
        return True

    except ImportError:
        print("[WARNING] huggingface_hub not installed. Run: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to download model: {e}")
        print("[INFO] Please ensure the model exists at HuggingFace or provide it locally.")
        return False


class FineTunedEmbeddingService:
    
    #Uses the fine-tuned XLM-R model to compute semantic similarity
    #for difficult cases.


    def __init__(self):
        base_dir = os.path.dirname(__file__)
        model_path = os.path.join(base_dir, "sinhala_fine_tuned_model")

        # Try to download from HuggingFace if not exists
        if not os.path.exists(model_path) or not os.path.exists(os.path.join(model_path, "config.json")):
            success = download_model_from_huggingface(model_path)
            if not success:
                raise FileNotFoundError(
                    "Fine-tuned Sinhala model not found and could not be downloaded. "
                    "Options:\n"
                    "  1. Run fine_tune_sinhala.py to train locally\n"
                    "  2. Ensure huggingface_hub is installed: pip install huggingface_hub\n"
                    f"  3. Check if model exists at: https://huggingface.co/{HUGGINGFACE_REPO_ID}"
                )

        self.model = SentenceTransformer(model_path)

    def similarity(self, text1: str, text2: str) -> float:
        embeddings = self.model.encode(
            [text1, text2],
            convert_to_tensor=True
        )

        score = torch.nn.functional.cosine_similarity(
            embeddings[0].unsqueeze(0),
            embeddings[1].unsqueeze(0)
        )

        return float(score.item())
