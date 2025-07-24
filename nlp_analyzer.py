"""
NLP Analysis utilities for text processing and relevance scoring
"""

import logging
import re
from typing import List, Dict, Any, Set
from collections import Counter
import math

class NLPAnalyzer:
    """Handles natural language processing tasks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stop_words = self._load_stop_words()
        
    def _load_stop_words(self) -> Set[str]:
        """Load common stop words"""
        # Basic English stop words
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'have', 'had', 'been', 'this',
            'these', 'they', 'were', 'not', 'or', 'but', 'can', 'could', 'should',
            'may', 'might', 'must', 'shall', 'do', 'does', 'did', 'get', 'got',
            'make', 'made', 'take', 'took', 'come', 'came', 'go', 'went', 'see',
            'saw', 'know', 'knew', 'think', 'thought', 'say', 'said', 'tell',
            'told', 'give', 'gave', 'find', 'found', 'work', 'worked', 'call',
            'called', 'try', 'tried', 'ask', 'asked', 'need', 'needed', 'feel',
            'felt', 'become', 'became', 'leave', 'left', 'put', 'set'
        }
    
    def calculate_relevance(self, text: str, persona: str, job: str) -> float:
        """Calculate relevance score of text to persona and job"""
        if not text or not text.strip():
            return 0.0
        
        # Tokenize and clean text
        text_tokens = self._tokenize_and_clean(text.lower())
        persona_tokens = self._tokenize_and_clean(persona.lower())
        job_tokens = self._tokenize_and_clean(job.lower())
        
        if not text_tokens:
            return 0.0
        
        # Calculate different relevance components
        persona_score = self._calculate_token_overlap(text_tokens, persona_tokens)
        job_score = self._calculate_token_overlap(text_tokens, job_tokens)
        
        # Calculate TF-IDF like scoring for key terms
        key_terms = persona_tokens + job_tokens
        tfidf_score = self._calculate_tfidf_score(text_tokens, key_terms)
        
        # Calculate domain-specific scoring
        domain_score = self._calculate_domain_relevance(text, persona, job)
        
        # Combine scores with weights
        relevance_score = (
            persona_score * 0.3 +
            job_score * 0.4 +
            tfidf_score * 0.2 +
            domain_score * 0.1
        )
        
        return min(relevance_score, 1.0)  # Cap at 1.0
    
    def _tokenize_and_clean(self, text: str) -> List[str]:
        """Tokenize text and remove stop words"""
        # Simple tokenization
        tokens = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        
        # Remove stop words and short words
        cleaned_tokens = [
            token for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        return cleaned_tokens
    
    def _calculate_token_overlap(self, text_tokens: List[str], target_tokens: List[str]) -> float:
        """Calculate overlap between text tokens and target tokens"""
        if not target_tokens:
            return 0.0
        
        text_set = set(text_tokens)
        target_set = set(target_tokens)
        
        intersection = text_set.intersection(target_set)
        
        if not target_set:
            return 0.0
        
        # Jaccard similarity
        union = text_set.union(target_set)
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Also calculate percentage of target terms found
        target_coverage = len(intersection) / len(target_set)
        
        return (jaccard + target_coverage) / 2
    
    def _calculate_tfidf_score(self, text_tokens: List[str], key_terms: List[str]) -> float:
        """Calculate TF-IDF like score for key terms in text"""
        if not key_terms or not text_tokens:
            return 0.0
        
        # Calculate term frequency
        token_counts = Counter(text_tokens)
        total_tokens = len(text_tokens)
        
        score = 0.0
        for term in set(key_terms):
            if term in token_counts:
                tf = token_counts[term] / total_tokens
                # Simple IDF approximation (assuming key terms are important)
                idf = math.log(10)  # Assume corpus of 10 documents
                score += tf * idf
        
        return min(score, 1.0)
    
    def _calculate_domain_relevance(self, text: str, persona: str, job: str) -> float:
        """Calculate domain-specific relevance"""
        text_lower = text.lower()
        
        # Define domain keywords based on persona types
        domain_keywords = {
            'researcher': ['research', 'study', 'analysis', 'methodology', 'results', 'findings', 'experiment', 'data', 'hypothesis', 'conclusion'],
            'student': ['learn', 'study', 'understand', 'concept', 'theory', 'example', 'practice', 'exercise', 'homework', 'exam'],
            'analyst': ['analysis', 'data', 'trend', 'performance', 'metrics', 'insights', 'report', 'statistics', 'evaluation', 'assessment'],
            'business': ['strategy', 'market', 'revenue', 'growth', 'profit', 'customer', 'sales', 'business', 'company', 'investment'],
            'technical': ['system', 'implementation', 'design', 'architecture', 'technology', 'development', 'software', 'hardware', 'algorithm', 'code']
        }
        
        # Detect persona type
        persona_lower = persona.lower()
        relevant_keywords = []
        
        for domain, keywords in domain_keywords.items():
            if domain in persona_lower:
                relevant_keywords.extend(keywords)
        
        # If no specific domain detected, use job keywords
        if not relevant_keywords:
            job_words = self._tokenize_and_clean(job)
            relevant_keywords = job_words
        
        # Count domain keyword matches
        keyword_matches = 0
        for keyword in relevant_keywords:
            if keyword in text_lower:
                keyword_matches += 1
        
        # Normalize by text length and keyword count
        if relevant_keywords:
            domain_score = keyword_matches / len(relevant_keywords)
            return min(domain_score, 1.0)
        
        return 0.0
    
    def refine_text_for_persona(self, text: str, persona: str, job: str) -> str:
        """Refine text to be more relevant for the specific persona"""
        if not text or len(text) < 50:
            return text
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Score each sentence
        scored_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                score = self.calculate_relevance(sentence, persona, job)
                scored_sentences.append((sentence, score))
        
        # Sort by relevance and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Reconstruct text with most relevant sentences
        top_sentences = [s[0] for s in scored_sentences[:3]]  # Top 3 sentences
        
        refined_text = '. '.join(top_sentences)
        
        # Add context if needed
        if len(refined_text) < 100 and len(scored_sentences) > 3:
            additional_sentence = scored_sentences[3][0]
            refined_text += '. ' + additional_sentence
        
        return refined_text.strip() + '.' if refined_text and not refined_text.endswith('.') else refined_text
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text"""
        if not text:
            return []
        
        # Simple n-gram extraction
        tokens = self._tokenize_and_clean(text)
        
        # Extract unigrams and bigrams
        phrases = []
        
        # Unigrams
        token_counts = Counter(tokens)
        for token, count in token_counts.most_common(max_phrases // 2):
            phrases.append(token)
        
        # Bigrams
        bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
        bigram_counts = Counter(bigrams)
        for bigram, count in bigram_counts.most_common(max_phrases // 2):
            phrases.append(bigram)
        
        return phrases[:max_phrases]
    
    def summarize_text(self, text: str, max_sentences: int = 3) -> str:
        """Generate a simple extractive summary"""
        if not text:
            return ""
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= max_sentences:
            return '. '.join(sentences) + '.'
        
        # Score sentences by position (first and last are often important)
        # and by length (not too short, not too long)
        scored_sentences = []
        
        for i, sentence in enumerate(sentences):
            position_score = 1.0 if i == 0 or i == len(sentences) - 1 else 0.5
            length_score = min(len(sentence) / 100, 1.0)  # Prefer moderate length
            
            total_score = position_score + length_score
            scored_sentences.append((sentence, total_score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:max_sentences]]
        
        # Maintain original order
        summary_sentences = []
        for sentence in sentences:
            if sentence in top_sentences:
                summary_sentences.append(sentence)
        
        return '. '.join(summary_sentences) + '.'
