"""
Simple semantic model that learns word relationships from context
"""
import numpy as np
from collections import defaultdict
import re

class SimpleSinhalaSemanticModel:
    """
    Super simple semantic model that learns from context
    Builds word relationships from your scraped data
    """
    
    def __init__(self, window_size=3):
        self.window_size = window_size
        self.word_vectors = {}      #  custom word embeddings
        self.word_contexts = defaultdict(set)  # What words appear together
        
    def train_from_texts(self, texts):
        """Train semantic relationships from Sinhala texts"""
        print("Training simple semantic model...")
        
        # Build co-occurrence relationships
        for text in texts:
            words = self._tokenize_sinhala(text)
            for i, word in enumerate(words):
                # Get context words around this word
                start = max(0, i - self.window_size)
                end = min(len(words), i + self.window_size + 1)
                
                context_words = words[start:i] + words[i+1:end]
                self.word_contexts[word].update(context_words)
        
        # Create simple vector representations
        all_words = list(self.word_contexts.keys())
        self.vocab_size = len(all_words)
        
        # Assign each word a unique ID
        self.word_to_id = {word: i for i, word in enumerate(all_words)}
        self.id_to_word = {i: word for word, i in self.word_to_id.items()}
        
        # Create simple vectors based on context
        for word in all_words:
            # Vector = one-hot of context words
            vector = np.zeros(self.vocab_size)
            for context_word in self.word_contexts[word]:
                if context_word in self.word_to_id:
                    vector[self.word_to_id[context_word]] = 1
            
            # Normalize
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            self.word_vectors[word] = vector
        
        print(f"✓ Trained on {len(texts)} texts, {self.vocab_size} words")
    
    def get_sentence_similarity(self, sentence1, sentence2):
        """Calculate semantic similarity between sentences"""
        words1 = self._tokenize_sinhala(sentence1)
        words2 = self._tokenize_sinhala(sentence2)
        
        # Get vectors for words that exist in our model
        vecs1 = [self.word_vectors[w] for w in words1 if w in self.word_vectors]
        vecs2 = [self.word_vectors[w] for w in words2 if w in self.word_vectors]
        
        if not vecs1 or not vecs2:
            return 0.5  # Default if unknown words
        
        # Average word vectors
        avg_vec1 = np.mean(vecs1, axis=0)
        avg_vec2 = np.mean(vecs2, axis=0)
        
        # Cosine similarity
        dot = np.dot(avg_vec1, avg_vec2)
        norm1 = np.linalg.norm(avg_vec1)
        norm2 = np.linalg.norm(avg_vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def find_semantic_matches(self, text1, text2, threshold=0.7):
        """Find semantically similar sentences"""
        sentences1 = self._split_sentences(text1)
        sentences2 = self._split_sentences(text2)
        
        matches = []
        for s1 in sentences1:
            for s2 in sentences2:
                if len(s1) > 10 and len(s2) > 10:
                    sim = self.get_sentence_similarity(s1, s2)
                    if sim > threshold:
                        matches.append({
                            'sentence1': s1,
                            'sentence2': s2,
                            'semantic_similarity': sim
                        })
        
        return matches
    
    def _tokenize_sinhala(self, text):
        """Simple Sinhala tokenizer"""
        # Remove punctuation
        text = re.sub(r'[^\w\s\u0D80-\u0DFF]', ' ', text)
        return [w for w in text.split() if len(w) > 1]
    
    def _split_sentences(self, text):
        """Split Sinhala text into sentences"""
        # Split by Sinhala sentence endings
        sentences = re.split(r'[।?!]', text)
        return [s.strip() for s in sentences if s.strip()]