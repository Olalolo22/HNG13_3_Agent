"""
Content Processing Module - NLP-based categorization and analysis.
Uses spaCy for intelligent content understanding.
"""
import spacy
from typing import Optional, List, Dict, Any, Set
from collections import Counter
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ContentProcessor:
    """
    Processes article content using NLP for categorization and analysis.
    """
    
    # Predefined categories with associated keywords
    CATEGORY_KEYWORDS = {
        'Technology': {
            'software', 'hardware', 'computer', 'programming', 'code', 'developer',
            'app', 'application', 'digital', 'tech', 'internet', 'web', 'api',
            'algorithm', 'data', 'database', 'cloud', 'server', 'network',
            'cybersecurity', 'security', 'encryption', 'blockchain', 'cryptocurrency',
            'artificial', 'machine learning', 'ai', 'robot', 'automation'
        },
        'Science': {
            'research', 'study', 'scientist', 'scientific', 'experiment', 'theory',
            'biology', 'chemistry', 'physics', 'astronomy', 'space', 'universe',
            'climate', 'environment', 'ecology', 'genetics', 'dna', 'medical',
            'health', 'disease', 'vaccine', 'medicine', 'laboratory', 'discovery'
        },
        'Business': {
            'business', 'company', 'startup', 'entrepreneur', 'ceo', 'market',
            'economy', 'finance', 'investment', 'stock', 'trade', 'revenue',
            'profit', 'sales', 'customer', 'marketing', 'strategy', 'management',
            'corporate', 'enterprise', 'industry', 'commerce', 'brand'
        },
        'Politics': {
            'government', 'politics', 'political', 'election', 'vote', 'democracy',
            'president', 'minister', 'congress', 'parliament', 'law', 'policy',
            'legislation', 'candidate', 'campaign', 'senator', 'representative',
            'diplomacy', 'international', 'nation', 'state', 'federal'
        },
        'Entertainment': {
            'movie', 'film', 'actor', 'actress', 'director', 'cinema', 'television',
            'tv', 'show', 'series', 'music', 'song', 'album', 'concert', 'band',
            'artist', 'entertainment', 'celebrity', 'hollywood', 'streaming',
            'gaming', 'game', 'video game', 'esports'
        },
        'Sports': {
            'sport', 'sports', 'athlete', 'team', 'player', 'coach', 'game',
            'match', 'tournament', 'championship', 'league', 'football', 'soccer',
            'basketball', 'baseball', 'tennis', 'golf', 'olympic', 'competition',
            'training', 'fitness', 'exercise'
        },
        'Education': {
            'education', 'learning', 'student', 'teacher', 'school', 'university',
            'college', 'course', 'lesson', 'study', 'academic', 'degree',
            'curriculum', 'classroom', 'lecture', 'tutorial', 'training',
            'knowledge', 'skill', 'pedagogy'
        },
        'Lifestyle': {
            'lifestyle', 'fashion', 'style', 'design', 'home', 'food', 'recipe',
            'cooking', 'travel', 'vacation', 'destination', 'hotel', 'restaurant',
            'wellness', 'beauty', 'fitness', 'hobby', 'craft', 'diy'
        },
        'Opinion': {
            'opinion', 'editorial', 'commentary', 'perspective', 'viewpoint',
            'analysis', 'critique', 'review', 'argument', 'debate', 'essay',
            'column', 'blog', 'think', 'believe', 'should', 'must'
        }
    }
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize content processor with spaCy model.
        
        Args:
            model_name: spaCy model to use (default: en_core_web_sm)
        """
        self.model_name = model_name
        self.nlp = None
        self._load_model()
        logger.info(f"ContentProcessor initialized with model: {model_name}")
    
    def _load_model(self):
        """Load spaCy model with error handling."""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"spaCy model '{self.model_name}' loaded successfully")
        except OSError:
            logger.warning(f"spaCy model '{self.model_name}' not found. Trying to download...")
            try:
                import subprocess
                subprocess.run(['python', '-m', 'spacy', 'download', self.model_name], 
                             check=True, capture_output=True)
                self.nlp = spacy.load(self.model_name)
                logger.info(f"spaCy model '{self.model_name}' downloaded and loaded")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {e}")
                logger.warning("ContentProcessor will work with limited functionality")
                self.nlp = None
    
    def categorize_article(self, title: str, content: str, 
                          description: Optional[str] = None) -> str:
        """
        Automatically categorize an article based on its content.
        
        Args:
            title: Article title
            content: Article content
            description: Article description (optional)
            
        Returns:
            Category name
        """
        # Combine text sources (title has more weight)
        text_to_analyze = f"{title} {title} {title}"  # Triple title for weight
        
        if description:
            text_to_analyze += f" {description} {description}"  # Double description
        
        # Use first 1000 chars of content
        text_to_analyze += f" {content[:1000]}"
        
        text_to_analyze = text_to_analyze.lower()
        
        # Score each category
        category_scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Count occurrences of keyword
                count = text_to_analyze.count(keyword.lower())
                score += count
            
            category_scores[category] = score
        
        # Get category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            best_score = category_scores[best_category]
            
            # Only assign if score is above threshold
            if best_score >= 2:
                logger.info(f"Categorized as '{best_category}' (score: {best_score})")
                return best_category
        
        logger.info("No clear category match, using 'Uncategorized'")
        return "Uncategorized"
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract important keywords from text using NLP.
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords
        """
        if not self.nlp:
            # Fallback to simple extraction without NLP
            return self._extract_keywords_simple(text, max_keywords)
        
        try:
            # Process text with spaCy
            doc = self.nlp(text[:5000])  # Limit to first 5000 chars
            
            # Extract nouns and proper nouns
            keywords = []
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                    if len(token.text) > 2:  # Skip very short words
                        keywords.append(token.text.lower())
            
            # Count frequency
            keyword_counts = Counter(keywords)
            
            # Return most common
            top_keywords = [word for word, count in keyword_counts.most_common(max_keywords)]
            
            logger.debug(f"Extracted {len(top_keywords)} keywords")
            return top_keywords
        
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return self._extract_keywords_simple(text, max_keywords)
    
    def _extract_keywords_simple(self, text: str, max_keywords: int) -> List[str]:
        """
        Simple keyword extraction without NLP (fallback method).
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords
            
        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
            'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'of', 'to', 'in', 'for',
            'with', 'by', 'from', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'this', 'that', 'these', 'those'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        # Filter stop words
        keywords = [w for w in words if w not in stop_words]
        
        # Count frequency
        keyword_counts = Counter(keywords)
        
        # Return most common
        return [word for word, count in keyword_counts.most_common(max_keywords)]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text (people, organizations, locations, etc.).
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of entity types and their values
        """
        if not self.nlp:
            logger.warning("spaCy not available, cannot extract entities")
            return {}
        
        try:
            doc = self.nlp(text[:5000])
            
            entities = {
                'PERSON': [],
                'ORG': [],
                'GPE': [],  # Geopolitical entities (countries, cities)
                'DATE': [],
                'MONEY': [],
                'PRODUCT': []
            }
            
            for ent in doc.ents:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text)
            
            # Remove duplicates and empty lists
            entities = {k: list(set(v)) for k, v in entities.items() if v}
            
            logger.debug(f"Extracted entities: {len(entities)} types")
            return entities
        
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}
    
    def get_summary_sentences(self, text: str, num_sentences: int = 3) -> str:
        """
        Extract key sentences for a summary.
        
        Args:
            text: Text to summarize
            num_sentences: Number of sentences to extract
            
        Returns:
            Summary text
        """
        if not self.nlp:
            # Simple fallback: return first N sentences
            sentences = text.split('. ')[:num_sentences]
            return '. '.join(sentences) + '.'
        
        try:
            doc = self.nlp(text[:3000])
            
            # Score sentences based on important words
            sentence_scores = {}
            
            for sent in doc.sents:
                score = 0
                for token in sent:
                    # Score based on parts of speech
                    if token.pos_ in ['NOUN', 'PROPN', 'VERB']:
                        score += 1
                    if token.pos_ == 'ADJ':
                        score += 0.5
                
                sentence_scores[sent.text] = score / len(sent)  # Normalize by length
            
            # Get top sentences
            top_sentences = sorted(sentence_scores.items(), 
                                 key=lambda x: x[1], 
                                 reverse=True)[:num_sentences]
            
            # Sort by original order
            summary = '. '.join([sent for sent, score in top_sentences])
            
            return summary
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            sentences = text.split('. ')[:num_sentences]
            return '. '.join(sentences) + '.'
    
    def detect_sentiment(self, text: str) -> str:
        """
        Detect sentiment of text (positive, negative, neutral).
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment string
        """
        # Simple sentiment analysis based on positive/negative words
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'love',
            'like', 'enjoy', 'happy', 'positive', 'success', 'win', 'benefit',
            'improve', 'better', 'perfect', 'fantastic', 'awesome', 'brilliant'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'worst', 'hate', 'dislike', 'poor',
            'negative', 'fail', 'failure', 'problem', 'issue', 'wrong', 'worse',
            'decline', 'loss', 'risk', 'threat', 'danger', 'crisis'
        }
        
        text_lower = text.lower()
        
        positive_count = sum(text_lower.count(word) for word in positive_words)
        negative_count = sum(text_lower.count(word) for word in negative_words)
        
        if positive_count > negative_count * 1.5:
            return 'positive'
        elif negative_count > positive_count * 1.5:
            return 'negative'
        else:
            return 'neutral'
    
    def analyze_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete analysis of an article.
        
        Args:
            article_data: Dictionary with article data (title, content, etc.)
            
        Returns:
            Dictionary with analysis results
        """
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        description = article_data.get('description')
        
        logger.info(f"Analyzing article: {title}")
        
        analysis = {
            'category': self.categorize_article(title, content, description),
            'keywords': self.extract_keywords(f"{title} {content}", max_keywords=10),
            'sentiment': self.detect_sentiment(content),
        }
        
        # Extract entities if spaCy is available
        if self.nlp:
            entities = self.extract_entities(content)
            if entities:
                analysis['entities'] = entities
            
            # Generate summary
            summary = self.get_summary_sentences(content, num_sentences=2)
            if summary:
                analysis['summary'] = summary
        
        logger.info(f"Analysis complete: category={analysis['category']}, "
                   f"keywords={len(analysis['keywords'])}, sentiment={analysis['sentiment']}")
        
        return analysis
    
    def suggest_related_categories(self, category: str, num_suggestions: int = 3) -> List[str]:
        """
        Suggest related categories based on a given category.
        
        Args:
            category: Base category
            num_suggestions: Number of suggestions to return
            
        Returns:
            List of related category names
        """
        # Define category relationships
        related_map = {
            'Technology': ['Science', 'Business', 'Education'],
            'Science': ['Technology', 'Education', 'Business'],
            'Business': ['Technology', 'Politics', 'Education'],
            'Politics': ['Business', 'Opinion', 'Education'],
            'Entertainment': ['Lifestyle', 'Sports', 'Opinion'],
            'Sports': ['Entertainment', 'Lifestyle', 'Business'],
            'Education': ['Science', 'Technology', 'Business'],
            'Lifestyle': ['Entertainment', 'Sports', 'Opinion'],
            'Opinion': ['Politics', 'Lifestyle', 'Entertainment']
        }
        
        related = related_map.get(category, [])
        return related[:num_suggestions]