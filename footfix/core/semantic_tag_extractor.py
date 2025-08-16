"""
Semantic tag extraction for FootFix.
Uses NLP techniques to extract meaningful tags from alt text descriptions.
"""

import logging
import re
import string
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import Counter

from .tag_manager import TagResult, TagStatus

logger = logging.getLogger(__name__)


@dataclass
class TagScore:
    """Represents a tag with its relevance score and metadata."""
    text: str
    score: float
    tag_type: str  # 'descriptive', 'technical', 'contextual', 'entity'
    specificity: float  # How specific vs generic the tag is
    source_context: str  # The sentence/phrase it came from


@dataclass
class SemanticExtractionResult:
    """Result of semantic tag extraction from alt text."""
    tags: List[str]
    scored_tags: List[TagScore]
    confidence: float
    extraction_method: str
    source_text: str
    processing_time: float


class SemanticTagExtractor:
    """
    Extracts meaningful tags from alt text using semantic analysis and NLP techniques.
    Focuses on quality and relevance rather than predefined categories.
    """
    
    def __init__(self, max_tags: int = 10):
        """
        Initialize the semantic tag extractor.
        
        Args:
            max_tags: Maximum number of tags to extract
        """
        self.max_tags = max_tags
        self._build_stop_words()
        self._build_quality_patterns()
        
    def _build_stop_words(self):
        """Build comprehensive stop words list for filtering."""
        # Common stop words that don't add descriptive value
        self.stop_words = {
            # Articles and determiners
            'a', 'an', 'the', 'this', 'that', 'these', 'those',
            # Prepositions
            'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to', 'of', 'as', 'into',
            # Conjunctions
            'and', 'or', 'but', 'so', 'yet', 'nor',
            # Pronouns
            'he', 'she', 'it', 'they', 'them', 'his', 'her', 'its', 'their',
            # Common verbs that don't describe content
            'is', 'are', 'was', 'were', 'being', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'must', 'shall',
            # Generic descriptors
            'image', 'picture', 'photo', 'photograph', 'shot', 'view', 'scene',
            'shows', 'showing', 'depicts', 'depicting', 'features', 'featuring',
            'contains', 'containing', 'includes', 'including',
            # Overly generic terms
            'thing', 'things', 'stuff', 'item', 'items', 'something', 'anything',
            'everything', 'nothing', 'one', 'two', 'three', 'some', 'many', 'few',
            'more', 'most', 'less', 'least', 'all', 'any', 'each', 'every',
            # Common but non-descriptive adjectives
            'good', 'bad', 'nice', 'great', 'big', 'small', 'large', 'little',
            'old', 'new', 'young', 'long', 'short', 'high', 'low', 'first', 'last'
        }
        
        # Photography-specific stop words that are too generic
        self.photography_stop_words = {
            'image', 'photo', 'picture', 'photograph', 'shot', 'capture', 'frame',
            'composition', 'visual', 'scene', 'view', 'angle', 'perspective',
            'shows', 'depicts', 'features', 'displays', 'presents', 'illustrates'
        }
        
        self.all_stop_words = self.stop_words.union(self.photography_stop_words)
        
        # Build concrete object vocabularies for scoring boost
        self._build_concrete_object_vocabularies()
        
    def _build_concrete_object_vocabularies(self):
        """Build vocabularies of concrete objects for scoring boost."""
        
        # Specific concrete objects that should be prioritized over abstract terms
        self.concrete_objects = {
            'buildings': [
                'barn', 'shed', 'garage', 'cabin', 'house', 'church', 'warehouse', 'factory',
                'office', 'store', 'shop', 'restaurant', 'cafe', 'library', 'school', 'hospital',
                'tower', 'castle', 'bridge', 'stadium', 'theater', 'museum', 'gallery', 'hotel'
            ],
            'vehicles': [
                'car', 'truck', 'bus', 'bike', 'van', 'suv', 'sedan', 'coupe', 'wagon',
                'motorcycle', 'scooter', 'bicycle', 'boat', 'ship', 'plane', 'helicopter',
                'train', 'subway', 'tram', 'taxi', 'ambulance', 'firetruck', 'police'
            ],
            'nature': [
                'tree', 'lake', 'hill', 'field', 'rock', 'path', 'river', 'mountain',
                'forest', 'beach', 'ocean', 'pond', 'stream', 'valley', 'cliff', 'canyon',
                'flower', 'grass', 'bush', 'garden', 'park', 'meadow', 'desert', 'island'
            ],
            'furniture': [
                'desk', 'chair', 'table', 'bed', 'sofa', 'shelf', 'lamp', 'cabinet',
                'dresser', 'couch', 'bench', 'stool', 'bookcase', 'wardrobe', 'nightstand',
                'mirror', 'picture', 'painting', 'clock', 'vase', 'plant', 'cushion'
            ],
            'animals': [
                'dog', 'cat', 'horse', 'cow', 'bird', 'sheep', 'pig', 'chicken',
                'duck', 'goose', 'rabbit', 'deer', 'bear', 'fox', 'wolf', 'lion',
                'elephant', 'giraffe', 'zebra', 'tiger', 'monkey', 'fish', 'shark', 'whale'
            ],
            'food': [
                'bread', 'cake', 'pizza', 'burger', 'sandwich', 'salad', 'soup', 'pasta',
                'rice', 'meat', 'chicken', 'beef', 'fish', 'fruit', 'apple', 'banana',
                'orange', 'grape', 'berry', 'vegetable', 'carrot', 'potato', 'onion', 'tomato'
            ],
            'tools': [
                'hammer', 'saw', 'drill', 'wrench', 'screwdriver', 'pliers', 'knife', 'scissors',
                'shovel', 'rake', 'hoe', 'ladder', 'bucket', 'brush', 'pen', 'pencil',
                'computer', 'phone', 'camera', 'keyboard', 'mouse', 'screen', 'monitor', 'printer'
            ]
        }
        
        # Flatten all concrete objects into a single set for quick lookup
        self.all_concrete_objects = set()
        for category, objects in self.concrete_objects.items():
            self.all_concrete_objects.update(objects)
        
        logger.debug(f"Built vocabulary of {len(self.all_concrete_objects)} concrete objects")
        
    def _build_quality_patterns(self):
        """Build patterns for identifying high-quality descriptive terms."""
        
        # Patterns that indicate high-quality descriptive tags
        self.quality_indicators = {
            # Specific materials and textures
            'materials': r'\b(?:wood|wooden|metal|metallic|glass|plastic|fabric|leather|stone|concrete|brick|ceramic|porcelain)\b',
            
            # Colors (more specific than basic colors)
            'specific_colors': r'\b(?:crimson|azure|emerald|golden|silver|bronze|ivory|ebony|turquoise|burgundy|navy|maroon)\b',
            
            # Professional/technical terms
            'professional': r'\b(?:professional|executive|corporate|editorial|commercial|studio|documentary|journalistic)\b',
            
            # Specific actions and poses
            'actions': r'\b(?:sitting|standing|walking|running|laughing|smiling|concentrating|presenting|demonstrating)\b',
            
            # Specific settings and environments
            'environments': r'\b(?:office|workspace|studio|conference|meeting|restaurant|cafe|kitchen|bedroom|living)\b',
            
            # Lighting and atmosphere
            'lighting': r'\b(?:natural|artificial|dramatic|soft|harsh|golden|ambient|directional|diffused|backlighting)\b',
            
            # Composition and framing
            'composition': r'\b(?:close-up|wide-shot|portrait|landscape|overhead|aerial|macro|telephoto|panoramic)\b',
            
            # Emotional and mood descriptors
            'mood': r'\b(?:confident|serious|cheerful|contemplative|focused|relaxed|energetic|peaceful|dynamic)\b',
            
            # Style and aesthetic
            'style': r'\b(?:modern|contemporary|vintage|classic|minimalist|elegant|rustic|industrial|artistic)\b',
            
            # Concrete building types
            'buildings': r'\b(?:barn|shed|garage|cabin|house|church|warehouse|factory|office|store|shop|restaurant|cafe|library|school|hospital)\b',
            
            # Vehicle types
            'vehicles': r'\b(?:car|truck|bus|bike|van|suv|sedan|motorcycle|scooter|bicycle|boat|ship|plane|helicopter|train)\b',
            
            # Natural features
            'nature': r'\b(?:tree|lake|hill|field|rock|path|river|mountain|forest|beach|ocean|pond|stream|valley|flower|garden)\b'
        }
        
        # Patterns for lower-quality terms to avoid
        self.low_quality_patterns = {
            'generic_adjectives': r'\b(?:good|bad|nice|big|small|pretty|ugly|normal|regular|usual|common)\b',
            'vague_terms': r'\b(?:thing|stuff|something|anything|everything|nothing|area|place|space|part)\b',
            'filler_words': r'\b(?:very|quite|rather|somewhat|pretty|really|actually|basically|generally)\b'
        }
        
    def extract_semantic_tags(self, alt_text: str) -> SemanticExtractionResult:
        """
        Extract tags using semantic analysis of alt text.
        
        Args:
            alt_text: The alt text description to analyze
            
        Returns:
            SemanticExtractionResult with extracted tags and metadata
        """
        import time
        start_time = time.time()
        
        if not alt_text or not alt_text.strip():
            return SemanticExtractionResult(
                tags=[],
                scored_tags=[],
                confidence=0.0,
                extraction_method="empty_input",
                source_text=alt_text,
                processing_time=0.0
            )
        
        # Step 1: Extract candidate terms
        candidates = self._extract_candidate_terms(alt_text)
        
        # Step 2: Score each candidate
        scored_candidates = self._score_candidates(candidates, alt_text)
        
        # Step 3: Apply quality filtering
        filtered_candidates = self._apply_quality_filters(scored_candidates)
        
        # Step 4: Select best tags
        final_tags = self._select_final_tags(filtered_candidates)
        
        # Step 5: Calculate overall confidence
        confidence = self._calculate_confidence(final_tags, alt_text)
        
        processing_time = time.time() - start_time
        
        return SemanticExtractionResult(
            tags=[tag.text for tag in final_tags],
            scored_tags=final_tags,
            confidence=confidence,
            extraction_method="semantic_analysis",
            source_text=alt_text,
            processing_time=processing_time
        )
    
    def _extract_candidate_terms(self, alt_text: str) -> List[str]:
        """
        Extract potential tag candidates from alt text.
        
        Args:
            alt_text: Text to analyze
            
        Returns:
            List of candidate terms
        """
        # Clean and normalize text
        text = alt_text.lower().strip()
        
        # Remove punctuation but keep hyphens and apostrophes
        text = re.sub(r'[^\w\s\-\']', ' ', text)
        
        # Extract different types of terms
        candidates = set()
        
        # 1. Single meaningful words (nouns, adjectives)
        words = text.split()
        for word in words:
            word = word.strip('-\'')
            if (len(word) >= 3 and 
                word not in self.all_stop_words and 
                word.isalpha()):
                candidates.add(word)
        
        # 2. Hyphenated compounds
        hyphenated = re.findall(r'\b\w+(?:-\w+)+\b', text)
        for compound in hyphenated:
            if len(compound) >= 5:  # Meaningful compound terms
                candidates.add(compound)
        
        # 3. Two-word descriptive phrases
        words = [w for w in words if w not in self.all_stop_words and len(w) >= 3]
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if self._is_descriptive_phrase(phrase):
                candidates.add(phrase)
        
        # 4. Three-word phrases for highly specific terms
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            if self._is_specific_phrase(phrase):
                candidates.add(phrase)
        
        return list(candidates)
    
    def _is_descriptive_phrase(self, phrase: str) -> bool:
        """Check if a two-word phrase is descriptive and valuable."""
        # Look for adjective + noun or noun + noun combinations
        descriptive_patterns = [
            r'\b(?:natural|artificial|bright|dark|soft|hard|smooth|rough)\s+\w+\b',
            r'\b(?:business|professional|casual|formal)\s+\w+\b',
            r'\b\w+\s+(?:background|lighting|environment|setting|style|design)\b',
            r'\b(?:conference|meeting|dining|living|work)\s+\w+\b'
        ]
        
        return any(re.search(pattern, phrase) for pattern in descriptive_patterns)
    
    def _is_specific_phrase(self, phrase: str) -> bool:
        """Check if a three-word phrase provides specific value."""
        # Only keep very specific, descriptive three-word phrases
        specific_patterns = [
            r'\b(?:shallow|deep)\s+depth\s+(?:of\s+)?field\b',
            r'\b(?:natural|artificial|studio)\s+\w+\s+lighting\b',
            r'\b(?:professional|business|corporate)\s+\w+\s+\w+\b'
        ]
        
        return any(re.search(pattern, phrase) for pattern in specific_patterns)
    
    def _score_candidates(self, candidates: List[str], alt_text: str) -> List[TagScore]:
        """
        Score candidate terms based on various quality metrics.
        
        Args:
            candidates: List of candidate terms
            alt_text: Original alt text for context
            
        Returns:
            List of scored candidates
        """
        scored = []
        text_lower = alt_text.lower()
        
        for candidate in candidates:
            # Base score
            score = 1.0
            
            # Check if this is a concrete object (highest priority)
            is_concrete_object = candidate.lower() in self.all_concrete_objects
            if is_concrete_object:
                score += 0.8  # Strong boost for concrete objects like "barn", "car", "tree"
                logger.debug(f"Concrete object boost: {candidate} (+0.8)")
            
            # Also check if compound terms contain concrete objects (e.g., "red barn", "old car")
            elif ' ' in candidate:
                words = candidate.lower().split()
                contains_concrete = any(word in self.all_concrete_objects for word in words)
                if contains_concrete:
                    score += 0.6  # Boost for phrases containing concrete objects
                    logger.debug(f"Compound concrete boost: {candidate} (+0.6)")
            
            # Length-based scoring (favor specific terms, but don't penalize concrete objects)
            if len(candidate) >= 8:
                score += 0.3  # Longer terms tend to be more specific
            elif len(candidate) <= 4 and not is_concrete_object:
                score -= 0.2  # Very short terms may be too generic (but not concrete objects)
            
            # Pattern-based quality scoring
            for pattern_type, pattern in self.quality_indicators.items():
                if re.search(pattern, candidate):
                    score += 0.4  # Strong boost for quality indicators
            
            # Penalty for low-quality patterns
            for pattern_type, pattern in self.low_quality_patterns.items():
                if re.search(pattern, candidate):
                    score -= 0.5
            
            # Specificity scoring (compound terms and phrases are more specific)
            specificity = 0.5  # Default
            if '-' in candidate or ' ' in candidate:
                specificity += 0.3  # Compound terms are more specific
            if len(candidate.split()) > 1:
                specificity += 0.2  # Multi-word phrases
            
            # Context relevance (how prominently the term appears)
            context_matches = len(re.findall(re.escape(candidate), text_lower))
            if context_matches > 1:
                score += 0.1 * context_matches  # Repeated terms are important
            
            # Determine tag type
            tag_type = self._determine_tag_type(candidate)
            
            # Type-based scoring adjustments
            type_multipliers = {
                'descriptive': 1.2,
                'technical': 1.1,
                'entity': 1.0,
                'contextual': 0.9
            }
            score *= type_multipliers.get(tag_type, 1.0)
            
            # Find source context
            source_context = self._find_source_context(candidate, alt_text)
            
            scored.append(TagScore(
                text=candidate,
                score=max(score, 0.1),  # Minimum score
                tag_type=tag_type,
                specificity=specificity,
                source_context=source_context
            ))
        
        return scored
    
    def _determine_tag_type(self, term: str) -> str:
        """Determine the type of tag based on its characteristics."""
        
        # Technical photography terms
        technical_patterns = [
            r'\b(?:close-up|wide-shot|macro|telephoto|portrait|landscape)\b',
            r'\b(?:lighting|exposure|focus|depth|angle|composition)\b',
            r'\b(?:natural|artificial|studio|ambient)\s+light\b'
        ]
        
        # Descriptive appearance terms
        descriptive_patterns = [
            r'\b(?:wearing|dressed|holding|sitting|standing)\b',
            r'\b\w+(?:ed|ing)\b',  # Past participles and gerunds
            r'\b(?:confident|serious|cheerful|professional)\b'
        ]
        
        # Contextual environment terms
        contextual_patterns = [
            r'\b(?:office|studio|outdoor|indoor|background)\b',
            r'\b(?:meeting|conference|interview|presentation)\b'
        ]
        
        # Entity terms (people, places, objects)
        entity_patterns = [
            r'\b(?:person|people|man|woman|child|executive|professional)\b',
            r'\b(?:building|room|desk|chair|computer|device)\b'
        ]
        
        term_lower = term.lower()
        
        if any(re.search(pattern, term_lower) for pattern in technical_patterns):
            return 'technical'
        elif any(re.search(pattern, term_lower) for pattern in descriptive_patterns):
            return 'descriptive'
        elif any(re.search(pattern, term_lower) for pattern in contextual_patterns):
            return 'contextual'
        elif any(re.search(pattern, term_lower) for pattern in entity_patterns):
            return 'entity'
        else:
            return 'descriptive'  # Default
    
    def _find_source_context(self, term: str, alt_text: str) -> str:
        """Find the sentence or phrase containing the term."""
        sentences = re.split(r'[.!?]+', alt_text)
        
        for sentence in sentences:
            if term.lower() in sentence.lower():
                return sentence.strip()
        
        return alt_text[:100] + '...' if len(alt_text) > 100 else alt_text
    
    def _apply_quality_filters(self, scored_candidates: List[TagScore]) -> List[TagScore]:
        """
        Apply quality filters to remove low-value tags.
        
        Args:
            scored_candidates: List of scored candidate tags
            
        Returns:
            Filtered list of high-quality tags
        """
        filtered = []
        
        for tag_score in scored_candidates:
            # Minimum score threshold
            if tag_score.score < 0.5:
                continue
            
            # Length filters
            if len(tag_score.text) < 3 or len(tag_score.text) > 50:
                continue
            
            # Avoid very generic terms
            if tag_score.text in {'image', 'photo', 'picture', 'view', 'scene'}:
                continue
            
            # Avoid single letters or numbers
            if tag_score.text.isdigit() or len(tag_score.text) == 1:
                continue
            
            # Keep high-quality tags
            filtered.append(tag_score)
        
        return filtered
    
    def _select_final_tags(self, filtered_candidates: List[TagScore]) -> List[TagScore]:
        """
        Select the final set of tags from filtered candidates.
        
        Args:
            filtered_candidates: Quality-filtered candidate tags
            
        Returns:
            Final selected tags
        """
        # Sort by score (descending)
        sorted_candidates = sorted(filtered_candidates, key=lambda x: x.score, reverse=True)
        
        # Ensure diversity in tag types
        selected = []
        type_counts = {}
        
        for candidate in sorted_candidates:
            # Limit tags per type to ensure diversity
            type_limit = {
                'descriptive': 4,
                'technical': 3,
                'entity': 3,
                'contextual': 2
            }
            
            current_count = type_counts.get(candidate.tag_type, 0)
            if current_count < type_limit.get(candidate.tag_type, 2):
                selected.append(candidate)
                type_counts[candidate.tag_type] = current_count + 1
                
                if len(selected) >= self.max_tags:
                    break
        
        # If we don't have enough diverse tags, fill with highest scoring
        if len(selected) < self.max_tags:
            remaining_needed = self.max_tags - len(selected)
            selected_texts = {tag.text for tag in selected}
            
            for candidate in sorted_candidates:
                if candidate.text not in selected_texts:
                    selected.append(candidate)
                    remaining_needed -= 1
                    if remaining_needed <= 0:
                        break
        
        return selected[:self.max_tags]
    
    def _calculate_confidence(self, final_tags: List[TagScore], alt_text: str) -> float:
        """
        Calculate overall confidence in the extraction.
        
        Args:
            final_tags: Final selected tags
            alt_text: Original alt text
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not final_tags:
            return 0.0
        
        # Average score of selected tags
        avg_score = sum(tag.score for tag in final_tags) / len(final_tags)
        
        # Tag count factor (more tags generally means better coverage)
        count_factor = min(len(final_tags) / 6.0, 1.0)  # Optimal around 6 tags
        
        # Text length factor (longer text generally yields better tags)
        length_factor = min(len(alt_text) / 150.0, 1.0)  # Optimal around 150 chars
        
        # Diversity factor (having different tag types is good)
        unique_types = len(set(tag.tag_type for tag in final_tags))
        diversity_factor = min(unique_types / 3.0, 1.0)  # Up to 3 different types
        
        # Weighted combination
        confidence = (avg_score * 0.4) + (count_factor * 0.3) + (length_factor * 0.2) + (diversity_factor * 0.1)
        
        return min(confidence, 1.0)
    
    def extract_and_validate_tags(self, alt_text: str, confidence_threshold: float = 0.4) -> TagResult:
        """
        Extract tags and convert to TagResult format for integration.
        
        Args:
            alt_text: Alt text to analyze
            confidence_threshold: Minimum confidence required
            
        Returns:
            TagResult compatible with existing tag system
        """
        extraction_result = self.extract_semantic_tags(alt_text)
        
        tag_result = TagResult()
        
        if extraction_result.confidence >= confidence_threshold:
            tag_result.tags = extraction_result.tags
            tag_result.tag_categories = {}  # Categories handled by TagManager's flexible organization
            tag_result.status = TagStatus.COMPLETED
            tag_result.application_time = extraction_result.processing_time
            
            logger.info(f"Extracted {len(extraction_result.tags)} semantic tags "
                       f"(confidence: {extraction_result.confidence:.2f})")
        else:
            tag_result.status = TagStatus.ERROR
            tag_result.error_message = f"Low confidence extraction: {extraction_result.confidence:.2f} < {confidence_threshold}"
            
            logger.warning(f"Semantic tag extraction confidence too low: {extraction_result.confidence:.2f}")
        
        return tag_result
    
    def test_concrete_object_scoring(self, test_cases: List[str]) -> Dict[str, float]:
        """
        Test scoring for concrete objects vs abstract terms.
        
        Args:
            test_cases: List of terms to test
            
        Returns:
            Dictionary mapping terms to their scores
        """
        results = {}
        
        for term in test_cases:
            # Simulate scoring for a single term
            scored_candidates = self._score_candidates([term], f"Test image showing {term}")
            if scored_candidates:
                results[term] = scored_candidates[0].score
            else:
                results[term] = 0.0
        
        return results
    
    def get_extraction_stats(self, alt_text: str) -> Dict[str, any]:
        """
        Get detailed extraction statistics for analysis.
        
        Args:
            alt_text: Alt text to analyze
            
        Returns:
            Dictionary with extraction statistics
        """
        result = self.extract_semantic_tags(alt_text)
        
        # Analyze tag types
        type_distribution = {}
        for tag in result.scored_tags:
            type_distribution[tag.tag_type] = type_distribution.get(tag.tag_type, 0) + 1
        
        return {
            'tag_count': len(result.tags),
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'extraction_method': result.extraction_method,
            'text_length': len(alt_text),
            'type_distribution': type_distribution,
            'average_score': sum(tag.score for tag in result.scored_tags) / len(result.scored_tags) if result.scored_tags else 0,
            'score_range': {
                'min': min(tag.score for tag in result.scored_tags) if result.scored_tags else 0,
                'max': max(tag.score for tag in result.scored_tags) if result.scored_tags else 0
            }
        }