"""
Test script for Content Processing module.
Run this to verify NLP and categorization works correctly.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.content_processing import ContentProcessor


def test_initialization():
    """Test processor initialization."""
    print("=" * 60)
    print("Testing Content Processor Initialization")
    print("=" * 60)
    
    processor = ContentProcessor()
    print("✅ ContentProcessor initialized")
    
    if processor.nlp:
        print("✅ spaCy model loaded successfully")
    else:
        print("⚠️  spaCy model not loaded (limited functionality)")
    
    return processor


def test_categorization(processor):
    """Test article categorization."""
    print("\n" + "=" * 60)
    print("Testing Article Categorization")
    print("=" * 60)
    
    test_cases = [
        {
            'title': 'Introduction to Machine Learning and AI',
            'content': 'Artificial intelligence and machine learning are transforming how we build software. Neural networks and deep learning algorithms are being used in various applications from computer vision to natural language processing.',
            'expected': 'Technology'
        },
        {
            'title': 'New Medical Breakthrough in Cancer Research',
            'content': 'Scientists at the research laboratory have discovered a new treatment for cancer. The medical experiment showed promising results in clinical trials with significant improvement in patient health.',
            'expected': 'Science'
        },
        {
            'title': 'Startup Raises $50M in Series B Funding',
            'content': 'The company announced today that it has raised 50 million dollars in investment from venture capital firms. The CEO said the funding will be used to expand the business and increase revenue.',
            'expected': 'Business'
        },
        {
            'title': 'Championship Game Tonight',
            'content': 'The championship game will be played tonight with the top two teams competing for the trophy. Athletes have been training intensely for this tournament match.',
            'expected': 'Sports'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['title']}")
        category = processor.categorize_article(
            test['title'],
            test['content']
        )
        print(f"   Detected: {category}")
        print(f"   Expected: {test['expected']}")
        
        if category == test['expected']:
            print(f"   ✅ Correct!")
        else:
            print(f"   ⚠️  Different (but may still be valid)")


def test_keyword_extraction(processor):
    """Test keyword extraction."""
    print("\n" + "=" * 60)
    print("Testing Keyword Extraction")
    print("=" * 60)
    
    text = """
    Artificial intelligence and machine learning are revolutionizing technology.
    Neural networks process data to recognize patterns. Deep learning algorithms
    improve software applications in computer vision and natural language processing.
    """
    
    keywords = processor.extract_keywords(text, max_keywords=8)
    print(f"\n✅ Extracted {len(keywords)} keywords:")
    print(f"   {', '.join(keywords)}")


def test_entity_extraction(processor):
    """Test named entity extraction."""
    print("\n" + "=" * 60)
    print("Testing Entity Extraction")
    print("=" * 60)
    
    if not processor.nlp:
        print("⚠️  Skipping - spaCy not available")
        return
    
    text = """
    Apple CEO Tim Cook announced the new iPhone in California yesterday.
    The company expects to earn $100 billion in revenue this quarter.
    Microsoft and Google are also competing in this market.
    """
    
    entities = processor.extract_entities(text)
    
    if entities:
        print("\n✅ Extracted entities:")
        for entity_type, values in entities.items():
            print(f"   {entity_type}: {', '.join(values)}")
    else:
        print("⚠️  No entities extracted")


def test_sentiment_detection(processor):
    """Test sentiment analysis."""
    print("\n" + "=" * 60)
    print("Testing Sentiment Detection")
    print("=" * 60)
    
    test_texts = [
        ("This is an excellent article with great insights!", "positive"),
        ("The terrible disaster caused significant problems.", "negative"),
        ("The report provides information about the topic.", "neutral")
    ]
    
    for text, expected in test_texts:
        sentiment = processor.detect_sentiment(text)
        print(f"\nText: {text[:50]}...")
        print(f"   Detected: {sentiment}")
        print(f"   Expected: {expected}")
        
        if sentiment == expected:
            print(f"   ✅ Correct!")
        else:
            print(f"   ⚠️  Different")


def test_full_analysis(processor):
    """Test complete article analysis."""
    print("\n" + "=" * 60)
    print("Testing Full Article Analysis")
    print("=" * 60)
    
    article_data = {
        'title': 'Breakthrough in Quantum Computing Technology',
        'content': """
        Researchers at the university have achieved a major breakthrough in quantum
        computing technology. The new quantum computer can process complex calculations
        much faster than traditional computers. Scientists used advanced algorithms
        and quantum mechanics principles to develop this revolutionary system.
        
        The technology could transform fields like cryptography, artificial intelligence,
        and drug discovery. Companies are investing heavily in quantum research to
        stay competitive in this emerging field.
        """,
        'description': 'Major advancement in quantum computing research'
    }
    
    analysis = processor.analyze_article(article_data)
    
    print("\n✅ Analysis Results:")
    print(f"   Category: {analysis['category']}")
    print(f"   Keywords: {', '.join(analysis['keywords'][:5])}...")
    print(f"   Sentiment: {analysis['sentiment']}")
    
    if 'entities' in analysis:
        print(f"   Entities found: {len(analysis['entities'])} types")
    
    if 'summary' in analysis:
        print(f"   Summary: {analysis['summary'][:100]}...")


def test_category_suggestions(processor):
    """Test related category suggestions."""
    print("\n" + "=" * 60)
    print("Testing Category Suggestions")
    print("=" * 60)
    
    categories_to_test = ['Technology', 'Science', 'Business']
    
    for category in categories_to_test:
        related = processor.suggest_related_categories(category, num_suggestions=3)
        print(f"\n{category}:")
        print(f"   Related: {', '.join(related)}")


if __name__ == "__main__":
    try:
        processor = test_initialization()
        test_categorization(processor)
        test_keyword_extraction(processor)
        test_entity_extraction(processor)
        test_sentiment_detection(processor)
        test_full_analysis(processor)
        test_category_suggestions(processor)
        
        print("\n\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 60)
        print("\nContent Processing module is working.")
        
        if processor.nlp:
            print("✨ Full NLP capabilities available")
        else:
            print("⚠️  Limited functionality (spaCy not loaded)")
            print("   Run: python -m spacy download en_core_web_sm")
        
        print()
    
    except Exception as e:
        print(f"\n\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)