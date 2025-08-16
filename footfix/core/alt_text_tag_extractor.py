"""
Alt text tag extraction for FootFix.
Extracts relevant tags from alt text descriptions to reduce API costs.
"""

import logging
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .tag_manager import TagResult, TagStatus, TagCategory

logger = logging.getLogger(__name__)


@dataclass
class TagExtractionResult:
    """Result of tag extraction from alt text."""
    tags: List[str]
    tag_categories: Dict[str, List[str]]
    confidence: float
    extraction_method: str
    source_text: str


class AltTextTagExtractor:
    """
    Extracts tags from alt text descriptions using keyword matching and NLP techniques.
    Provides cost-efficient alternative to separate AI vision analysis.
    """
    
    def __init__(self, tag_categories: Optional[Dict[str, TagCategory]] = None):
        """
        Initialize the tag extractor.
        
        Args:
            tag_categories: Available tag categories for assignment
        """
        self.tag_categories = tag_categories or {}
        self._build_keyword_mappings()
        
    def _build_keyword_mappings(self):
        """Build comprehensive keyword mappings for tag extraction."""
        
        # Content category keywords
        self.content_keywords = {
            'person': [
                'person', 'people', 'individual', 'man', 'woman', 'child', 'children',
                'adult', 'teenager', 'elderly', 'senior', 'boy', 'girl', 'human',
                'portrait', 'face', 'facial', 'headshot', 'figure', 'silhouette'
            ],
            'building': [
                'building', 'architecture', 'structure', 'house', 'home', 'office',
                'skyscraper', 'tower', 'bridge', 'construction', 'facade', 'exterior',
                'interior', 'room', 'space', 'venue', 'establishment', 'facility'
            ],
            'landscape': [
                'landscape', 'scenery', 'nature', 'outdoors', 'outdoor', 'mountains',
                'hills', 'trees', 'forest', 'park', 'garden', 'field', 'countryside',
                'natural', 'environment', 'scenic', 'vista', 'horizon', 'sky'
            ],
            'food': [
                'food', 'meal', 'dish', 'cuisine', 'restaurant', 'kitchen', 'cooking',
                'dining', 'plate', 'bowl', 'drink', 'beverage', 'coffee', 'tea',
                'fresh', 'delicious', 'culinary', 'chef', 'ingredient', 'recipe'
            ],
            'technology': [
                'technology', 'tech', 'computer', 'device', 'digital', 'electronic',
                'smartphone', 'laptop', 'tablet', 'screen', 'monitor', 'keyboard',
                'software', 'app', 'interface', 'modern', 'innovative', 'high-tech'
            ],
            'object': [
                'object', 'item', 'product', 'tool', 'equipment', 'accessory',
                'furniture', 'decoration', 'artwork', 'sculpture', 'design',
                'craft', 'handmade', 'vintage', 'antique', 'collectible'
            ]
        }
        
        # Style category keywords
        self.style_keywords = {
            'portrait': [
                'portrait', 'close-up', 'closeup', 'tight shot', 'headshot',
                'facial', 'intimate', 'personal', 'detailed view', 'focused'
            ],
            'wide-shot': [
                'wide shot', 'wide-shot', 'full body', 'environmental', 'establishing',
                'panoramic', 'expansive', 'broad view', 'overview', 'comprehensive'
            ],
            'close-up': [
                'close-up', 'closeup', 'macro', 'detailed', 'intricate', 'zoom',
                'magnified', 'intimate detail', 'focused', 'precise'
            ],
            'black-white': [
                'black and white', 'black-and-white', 'monochrome', 'grayscale',
                'noir', 'classic', 'timeless', 'artistic', 'dramatic contrast'
            ],
            'color': [
                'colorful', 'vibrant', 'bright', 'vivid', 'rich colors', 'saturated',
                'multicolored', 'rainbow', 'spectrum', 'chromatic', 'hues'
            ],
            'vintage': [
                'vintage', 'retro', 'classic', 'old-fashioned', 'nostalgic',
                'antique', 'historical', 'period', 'traditional', 'timeless'
            ],
            'modern': [
                'modern', 'contemporary', 'current', 'sleek', 'minimalist',
                'clean', 'fresh', 'updated', 'stylish', 'sophisticated'
            ]
        }
        
        # Usage category keywords
        self.usage_keywords = {
            'hero-image': [
                'banner', 'header', 'main image', 'featured', 'prominent',
                'central', 'focal point', 'highlight', 'showcase', 'primary'
            ],
            'thumbnail': [
                'small', 'compact', 'preview', 'icon', 'miniature', 'reduced',
                'summary', 'overview', 'brief', 'condensed', 'scaled'
            ],
            'gallery': [
                'gallery', 'collection', 'series', 'portfolio', 'exhibition',
                'showcase', 'display', 'arrangement', 'compilation', 'selection'
            ],
            'article': [
                'article', 'story', 'content', 'editorial', 'journalism',
                'news', 'publication', 'magazine', 'newspaper', 'blog'
            ],
            'social-media': [
                'social media', 'social-media', 'instagram', 'facebook', 'twitter',
                'linkedin', 'sharing', 'viral', 'engagement', 'post', 'feed'
            ],
            'print': [
                'print', 'printing', 'publication', 'brochure', 'flyer',
                'poster', 'advertisement', 'marketing', 'promotional', 'physical'
            ]
        }
        
        # Editorial category keywords
        self.editorial_keywords = {
            'news': [
                'news', 'breaking', 'current events', 'journalism', 'reporter',
                'press', 'media', 'announcement', 'update', 'bulletin'
            ],
            'feature': [
                'feature', 'in-depth', 'detailed', 'comprehensive', 'analysis',
                'investigation', 'profile', 'spotlight', 'special report'
            ],
            'opinion': [
                'opinion', 'editorial', 'commentary', 'perspective', 'viewpoint',
                'analysis', 'critique', 'review', 'assessment', 'evaluation'
            ],
            'review': [
                'review', 'rating', 'evaluation', 'critique', 'assessment',
                'recommendation', 'test', 'trial', 'examination', 'inspection'
            ],
            'interview': [
                'interview', 'conversation', 'discussion', 'dialogue', 'Q&A',
                'meeting', 'session', 'chat', 'talk', 'exchange'
            ],
            'breaking': [
                'breaking', 'urgent', 'immediate', 'developing', 'latest',
                'just in', 'live', 'real-time', 'emergency', 'alert'
            ],
            'analysis': [
                'analysis', 'analytical', 'study', 'research', 'investigation',
                'examination', 'exploration', 'insight', 'deep dive', 'breakdown'
            ]
        }
        
        # Compile all keywords for efficient searching
        self._compile_keyword_patterns()
        
    def _compile_keyword_patterns(self):
        """Compile regex patterns for efficient keyword matching."""
        self.category_patterns = {}
        
        categories = {
            'Content': self.content_keywords,
            'Style': self.style_keywords,
            'Usage': self.usage_keywords,
            'Editorial': self.editorial_keywords
        }
        
        for category_name, tag_keywords in categories.items():
            self.category_patterns[category_name] = {}
            
            for tag, keywords in tag_keywords.items():
                # Create regex pattern for each tag
                # Use word boundaries and case-insensitive matching
                pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
                self.category_patterns[category_name][tag] = re.compile(pattern, re.IGNORECASE)
    
    def extract_tags_from_alt_text(self, alt_text: str, max_tags_per_category: int = 3) -> TagExtractionResult:
        """
        Extract tags from alt text description.
        
        Args:
            alt_text: The alt text description to analyze
            max_tags_per_category: Maximum tags to extract per category
            
        Returns:
            TagExtractionResult with extracted tags and metadata
        """
        if not alt_text or not alt_text.strip():
            return TagExtractionResult(
                tags=[],
                tag_categories={},
                confidence=0.0,
                extraction_method="empty_input",
                source_text=alt_text
            )
        
        text = alt_text.lower().strip()
        extracted_categories = {}
        all_tags = []
        total_matches = 0
        
        # Extract tags for each category
        for category_name, tag_patterns in self.category_patterns.items():
            category_tags = []
            category_matches = 0
            
            for tag, pattern in tag_patterns.items():
                matches = pattern.findall(text)
                if matches:
                    category_tags.append(tag)
                    category_matches += len(matches)
                    
                    # Stop if we have enough tags for this category
                    if len(category_tags) >= max_tags_per_category:
                        break
            
            if category_tags:
                extracted_categories[category_name] = category_tags
                all_tags.extend(category_tags)
                total_matches += category_matches
        
        # Calculate confidence based on matches and text length
        confidence = self._calculate_confidence(alt_text, total_matches, len(all_tags))
        
        # If we didn't get enough tags, try fallback extraction
        if len(all_tags) < 2:
            fallback_result = self._fallback_extraction(alt_text)
            if fallback_result.tags:
                return fallback_result
        
        return TagExtractionResult(
            tags=all_tags,
            tag_categories=extracted_categories,
            confidence=confidence,
            extraction_method="keyword_matching",
            source_text=alt_text
        )
    
    def _calculate_confidence(self, alt_text: str, total_matches: int, tag_count: int) -> float:
        """
        Calculate confidence score for extracted tags.
        
        Args:
            alt_text: Original alt text
            total_matches: Number of keyword matches found
            tag_count: Number of unique tags extracted
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not alt_text or tag_count == 0:
            return 0.0
        
        # Base confidence from tag count (more tags = higher confidence up to a point)
        tag_score = min(tag_count / 5.0, 1.0)  # Optimal around 5 tags
        
        # Match density (matches per 100 characters)
        text_length = len(alt_text)
        match_density = (total_matches / max(text_length, 1)) * 100
        density_score = min(match_density / 2.0, 1.0)  # Optimal around 2% density
        
        # Text quality (longer, more descriptive text generally yields better tags)
        length_score = min(text_length / 200.0, 1.0)  # Optimal around 200 characters
        
        # Weighted combination
        confidence = (tag_score * 0.5) + (density_score * 0.3) + (length_score * 0.2)
        
        return min(confidence, 1.0)
    
    def _fallback_extraction(self, alt_text: str) -> TagExtractionResult:
        """
        Fallback extraction using simpler heuristics.
        
        Args:
            alt_text: Alt text to analyze
            
        Returns:
            TagExtractionResult with fallback tags
        """
        text = alt_text.lower()
        fallback_tags = []
        fallback_categories = {}
        
        # Simple presence-based detection
        if any(word in text for word in ['person', 'people', 'man', 'woman', 'child']):
            fallback_tags.append('person')
            fallback_categories['Content'] = ['person']
        
        if any(word in text for word in ['building', 'house', 'structure', 'architecture']):
            fallback_tags.append('building')
            if 'Content' not in fallback_categories:
                fallback_categories['Content'] = []
            fallback_categories['Content'].append('building')
        
        if any(word in text for word in ['landscape', 'nature', 'outdoor', 'scenery']):
            fallback_tags.append('landscape')
            if 'Content' not in fallback_categories:
                fallback_categories['Content'] = []
            fallback_categories['Content'].append('landscape')
        
        # Default to 'object' if nothing else found
        if not fallback_tags:
            fallback_tags.append('object')
            fallback_categories['Content'] = ['object']
        
        confidence = 0.3 if fallback_tags else 0.0  # Lower confidence for fallback
        
        return TagExtractionResult(
            tags=fallback_tags,
            tag_categories=fallback_categories,
            confidence=confidence,
            extraction_method="fallback_heuristics",
            source_text=alt_text
        )
    
    def extract_and_validate_tags(self, alt_text: str, confidence_threshold: float = 0.5) -> TagResult:
        """
        Extract tags and convert to TagResult format for integration.
        
        Args:
            alt_text: Alt text to analyze
            confidence_threshold: Minimum confidence required
            
        Returns:
            TagResult compatible with existing tag system
        """
        extraction_result = self.extract_tags_from_alt_text(alt_text)
        
        tag_result = TagResult()
        
        if extraction_result.confidence >= confidence_threshold:
            tag_result.tags = extraction_result.tags
            tag_result.tag_categories = extraction_result.tag_categories
            tag_result.status = TagStatus.COMPLETED
            tag_result.application_time = 0.05  # Minimal processing time
            
            logger.info(f"Extracted {len(extraction_result.tags)} tags from alt text "
                       f"(confidence: {extraction_result.confidence:.2f})")
        else:
            tag_result.status = TagStatus.ERROR
            tag_result.error_message = f"Low confidence extraction: {extraction_result.confidence:.2f} < {confidence_threshold}"
            
            logger.warning(f"Tag extraction confidence too low: {extraction_result.confidence:.2f}")
        
        return tag_result
    
    def update_keyword_mappings(self, category: str, tag: str, keywords: List[str]):
        """
        Update keyword mappings for a specific tag.
        
        Args:
            category: Category name (Content, Style, Usage, Editorial)
            tag: Tag name
            keywords: List of keywords for this tag
        """
        category_map = {
            'Content': self.content_keywords,
            'Style': self.style_keywords,
            'Usage': self.usage_keywords,
            'Editorial': self.editorial_keywords
        }
        
        if category in category_map:
            category_map[category][tag] = keywords
            self._compile_keyword_patterns()  # Recompile patterns
            logger.info(f"Updated keyword mapping for {category}.{tag}")
    
    def get_extraction_stats(self, alt_text: str) -> Dict[str, any]:
        """
        Get detailed extraction statistics for analysis.
        
        Args:
            alt_text: Alt text to analyze
            
        Returns:
            Dictionary with extraction statistics
        """
        result = self.extract_tags_from_alt_text(alt_text)
        
        return {
            'tag_count': len(result.tags),
            'category_count': len(result.tag_categories),
            'confidence': result.confidence,
            'extraction_method': result.extraction_method,
            'text_length': len(alt_text),
            'categories': list(result.tag_categories.keys()),
            'tags_by_category': {cat: len(tags) for cat, tags in result.tag_categories.items()}
        }