"""
Tag management system for FootFix.
Provides configurable tag assignment and management for image processing workflows.
"""

import logging
import json
import time
import asyncio
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class TagStatus(Enum):
    """Status of tag assignment."""
    PENDING = "pending"
    APPLYING = "applying"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class TagResult:
    """Result of tag assignment for a single image."""
    tags: List[str] = field(default_factory=list)
    status: TagStatus = TagStatus.PENDING
    error_message: Optional[str] = None
    application_time: float = 0.0


@dataclass
class TagCategory:
    """Definition of a tag category."""
    name: str
    color: str = "#007AFF"
    description: str = ""
    required: bool = False
    max_tags: Optional[int] = None
    predefined_tags: List[str] = field(default_factory=list)
    allow_custom: bool = True


class TagManager:
    """
    Manages tag assignment and validation for images.
    Provides configurable tag categories and bulk tag operations.
    """
    
    def __init__(self):
        self.categories: Dict[str, TagCategory] = {}
        self.global_tags: Set[str] = set()
        self.auto_suggest: bool = True
        self.max_tags_per_image: int = 10
        self.require_tags: bool = False
        
        # AI tag generation settings
        self.ai_generation_enabled: bool = False
        self.ai_confidence_threshold: float = 0.7
        self.ai_max_tags_per_category: int = 3
        self.fallback_to_patterns: bool = True
        self._ai_tag_generator = None
        
        # Semantic tag extraction settings
        self.semantic_extraction_enabled: bool = True
        self.semantic_confidence_threshold: float = 0.4
        self.semantic_max_tags: int = 10
        self._semantic_extractor = None
        
        # Initialize default categories
        self._initialize_default_categories()
        
        # Initialize semantic tag extraction
        self.enable_semantic_extraction(self.semantic_extraction_enabled)
        
    def _initialize_default_categories(self):
        """Initialize default tag categories for editorial workflows."""
        default_categories = [
            TagCategory(
                name="Content",
                color="#28a745",
                description="Describes what is in the image",
                predefined_tags=["person", "people", "building", "landscape", "object", "food", "technology"]
            ),
            TagCategory(
                name="Style",
                color="#ffc107",
                description="Visual style and composition",
                predefined_tags=["portrait", "wide-shot", "close-up", "black-white", "color", "vintage", "modern"]
            ),
            TagCategory(
                name="Usage",
                color="#17a2b8",
                description="Intended use or context",
                predefined_tags=["hero-image", "thumbnail", "gallery", "article", "social-media", "print"]
            ),
            TagCategory(
                name="Editorial",
                color="#dc3545",
                description="Editorial context and classification",
                predefined_tags=["news", "feature", "opinion", "review", "interview", "breaking", "analysis"]
            )
        ]
        
        for category in default_categories:
            self.categories[category.name] = category
            self.global_tags.update(category.predefined_tags)
    
    def add_category(self, category: TagCategory) -> bool:
        """Add a new tag category."""
        try:
            if category.name in self.categories:
                logger.warning(f"Category '{category.name}' already exists, updating")
            
            self.categories[category.name] = category
            self.global_tags.update(category.predefined_tags)
            
            logger.info(f"Added tag category: {category.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add category {category.name}: {e}")
            return False
    
    def remove_category(self, category_name: str) -> bool:
        """Remove a tag category."""
        try:
            if category_name not in self.categories:
                logger.warning(f"Category '{category_name}' not found")
                return False
                
            # Remove predefined tags from global set
            category = self.categories[category_name]
            for tag in category.predefined_tags:
                # Only remove if not used by other categories
                if not any(tag in cat.predefined_tags for name, cat in self.categories.items() if name != category_name):
                    self.global_tags.discard(tag)
            
            del self.categories[category_name]
            logger.info(f"Removed tag category: {category_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove category {category_name}: {e}")
            return False
    
    def get_suggested_tags(self, existing_tags: List[str] = None) -> List[str]:
        """Get suggested tags based on existing tags and semantic similarity."""
        if not self.auto_suggest:
            return []
            
        existing_tags = existing_tags or []
        suggestions = []
        
        # Use semantic extraction for intelligent suggestions
        if self.semantic_extraction_enabled and self._semantic_extractor:
            # Get semantically related tags from global tag collection
            related_tags = self._get_semantically_related_tags(existing_tags)
            suggestions.extend(related_tags)
        
        # Fallback to popular tags from categories if semantic suggestions are insufficient
        if len(suggestions) < 5:
            for category in self.categories.values():
                for tag in category.predefined_tags[:2]:  # Top 2 from each category
                    if tag not in existing_tags and tag not in suggestions:
                        suggestions.append(tag)
        
        return suggestions[:10]  # Limit suggestions
    
    def validate_tags(self, tags: List[str], filename: str = "") -> TagResult:
        """Validate a list of tags with quality-based filtering."""
        result = TagResult()
        result.status = TagStatus.APPLYING
        
        try:
            # Check maximum tags limit
            if len(tags) > self.max_tags_per_image:
                result.status = TagStatus.ERROR
                result.error_message = f"Too many tags: {len(tags)} > {self.max_tags_per_image}"
                return result
            
            # Quality-based validation (no rigid category constraints)
            validated_tags = []
            
            for tag in tags:
                tag = tag.strip().lower()
                if not tag:
                    continue
                
                # Basic quality checks
                if len(tag) < 2:  # Too short
                    continue
                if len(tag) > 50:  # Too long
                    continue
                if tag.isdigit():  # Pure numbers aren't descriptive
                    continue
                if tag in {'image', 'photo', 'picture', 'view', 'scene'}:  # Generic terms
                    continue
                
                validated_tags.append(tag)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tags = []
            for tag in validated_tags:
                if tag not in seen:
                    seen.add(tag)
                    unique_tags.append(tag)
            
            result.tags = unique_tags
            result.status = TagStatus.COMPLETED
            logger.debug(f"Validated {len(unique_tags)} tags for {filename}")
            
        except Exception as e:
            result.status = TagStatus.ERROR
            result.error_message = f"Tag validation error: {str(e)}"
            logger.error(f"Tag validation failed for {filename}: {e}")
        
        return result
    
    def apply_tags(self, tags: List[str], filename: str, progress_callback: Optional[Callable] = None) -> TagResult:
        """Apply tags to an image with validation."""
        start_time = time.time()
        
        if progress_callback:
            progress_callback(0, f"Validating tags for {filename}")
        
        # Validate tags
        result = self.validate_tags(tags, filename)
        
        if result.status == TagStatus.ERROR:
            return result
        
        if progress_callback:
            progress_callback(50, f"Applying tags to {filename}")
        
        try:
            # Add to global tag set for future suggestions
            self.global_tags.update(result.tags)
            
            # Simulate tag application time
            time.sleep(0.1)  # Small delay to show progress
            
            result.application_time = time.time() - start_time
            result.status = TagStatus.COMPLETED
            
            logger.info(f"Applied {len(result.tags)} tags to {filename}")
            
            if progress_callback:
                progress_callback(100, f"Tags applied to {filename}")
                
        except Exception as e:
            result.status = TagStatus.ERROR
            result.error_message = f"Failed to apply tags: {str(e)}"
            logger.error(f"Tag application failed for {filename}: {e}")
        
        return result
    
    def bulk_apply_tags(self, tags: List[str], filenames: List[str], progress_callback: Optional[Callable] = None) -> Dict[str, TagResult]:
        """Apply tags to multiple images."""
        results = {}
        total_files = len(filenames)
        
        for i, filename in enumerate(filenames):
            if progress_callback:
                progress_callback(
                    int((i / total_files) * 100),
                    f"Applying tags to {filename} ({i+1}/{total_files})"
                )
            
            results[filename] = self.apply_tags(tags, filename)
        
        if progress_callback:
            progress_callback(100, f"Bulk tag application complete")
        
        return results
    
    def get_all_tags(self) -> List[str]:
        """Get all available tags across all categories."""
        return sorted(list(self.global_tags))
    
    def get_category_tags(self, category_name: str) -> List[str]:
        """Get tags for a specific category."""
        if category_name in self.categories:
            return self.categories[category_name].predefined_tags.copy()
        return []
    
    def search_tags(self, query: str) -> List[str]:
        """Search for tags matching a query."""
        query = query.lower().strip()
        if not query:
            return self.get_all_tags()
        
        matching_tags = [tag for tag in self.global_tags if query in tag.lower()]
        return sorted(matching_tags)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current tag manager configuration."""
        return {
            'categories': {
                name: {
                    'name': cat.name,
                    'color': cat.color,
                    'description': cat.description,
                    'required': cat.required,
                    'max_tags': cat.max_tags,
                    'predefined_tags': cat.predefined_tags,
                    'allow_custom': cat.allow_custom
                }
                for name, cat in self.categories.items()
            },
            'auto_suggest': self.auto_suggest,
            'max_tags_per_image': self.max_tags_per_image,
            'require_tags': self.require_tags
        }
    
    def set_config(self, config: Dict[str, Any]) -> bool:
        """Set tag manager configuration."""
        try:
            # Update categories
            if 'categories' in config:
                self.categories.clear()
                self.global_tags.clear()
                
                for cat_name, cat_data in config['categories'].items():
                    category = TagCategory(
                        name=cat_data.get('name', cat_name),
                        color=cat_data.get('color', '#007AFF'),
                        description=cat_data.get('description', ''),
                        required=cat_data.get('required', False),
                        max_tags=cat_data.get('max_tags'),
                        predefined_tags=cat_data.get('predefined_tags', []),
                        allow_custom=cat_data.get('allow_custom', True)
                    )
                    self.add_category(category)
            
            # Update settings
            self.auto_suggest = config.get('auto_suggest', True)
            self.max_tags_per_image = config.get('max_tags_per_image', 10)
            self.require_tags = config.get('require_tags', False)
            
            # Update AI settings
            self.ai_generation_enabled = config.get('ai_generation_enabled', False)
            self.ai_confidence_threshold = config.get('ai_confidence_threshold', 0.7)
            self.ai_max_tags_per_category = config.get('ai_max_tags_per_category', 3)
            self.fallback_to_patterns = config.get('fallback_to_patterns', True)
            
            # Update semantic extraction settings
            self.semantic_extraction_enabled = config.get('semantic_extraction_enabled', True)
            self.semantic_confidence_threshold = config.get('semantic_confidence_threshold', 0.4)
            self.semantic_max_tags = config.get('semantic_max_tags', 10)
            
            logger.info("Tag manager configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set tag manager config: {e}")
            return False
    
    # AI Tag Generation Methods
    
    def enable_ai_generation(self, api_key: str) -> bool:
        """
        Enable AI-powered tag generation.
        
        Args:
            api_key: Anthropic API key for AI tag generation
            
        Returns:
            True if AI generation was enabled successfully
        """
        try:
            from .ai_tag_generator import AITagGenerator
            
            self._ai_tag_generator = AITagGenerator(api_key=api_key, tag_categories=self.categories)
            self.ai_generation_enabled = True
            
            logger.info("AI tag generation enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable AI tag generation: {e}")
            self.ai_generation_enabled = False
            return False
    
    def disable_ai_generation(self):
        """Disable AI-powered tag generation."""
        self.ai_generation_enabled = False
        self._ai_tag_generator = None
        logger.info("AI tag generation disabled")
    
    def update_ai_categories(self):
        """Update AI generator with current categories."""
        if self._ai_tag_generator:
            self._ai_tag_generator.set_tag_categories(self.categories)
            logger.debug("Updated AI generator with current categories")
    
    def enable_semantic_extraction(self, enabled: bool = True):
        """
        Enable or disable semantic tag extraction.
        
        Args:
            enabled: Whether to enable semantic extraction
        """
        self.semantic_extraction_enabled = enabled
        
        if enabled and not self._semantic_extractor:
            # Import here to avoid circular imports
            from .semantic_tag_extractor import SemanticTagExtractor
            self._semantic_extractor = SemanticTagExtractor(max_tags=self.semantic_max_tags)
            logger.info("Semantic tag extraction enabled")
        elif not enabled:
            self._semantic_extractor = None
            logger.info("Semantic tag extraction disabled")
    
    def update_semantic_extractor_settings(self):
        """Update semantic extractor with current settings."""
        if self._semantic_extractor:
            self._semantic_extractor.max_tags = self.semantic_max_tags
            logger.debug("Updated semantic extractor settings")
    
    async def generate_ai_tags(self, image_path: Path, context: Optional[str] = None) -> TagResult:
        """
        Generate tags for an image using AI analysis.
        
        Args:
            image_path: Path to the image file
            context: Optional context about the image
            
        Returns:
            TagResult with AI-generated tags
        """
        result = TagResult()
        
        if not self.ai_generation_enabled or not self._ai_tag_generator:
            result.status = TagStatus.ERROR
            result.error_message = "AI tag generation not enabled"
            return result
            
        try:
            # Generate tags using AI with proper session management
            async with self._ai_tag_generator:
                ai_result = await self._ai_tag_generator.generate_tags(image_path, context)
            
            if ai_result.status.value == "completed" and ai_result.confidence >= self.ai_confidence_threshold:
                # Filter and limit tags based on confidence and settings
                filtered_tags = []
                filtered_categories = {}
                
                for category, tags in ai_result.tag_categories.items():
                    # Limit tags per category
                    limited_tags = tags[:self.ai_max_tags_per_category]
                    if limited_tags:
                        filtered_categories[category] = limited_tags
                        filtered_tags.extend(limited_tags)
                
                # Apply overall tag limit
                if len(filtered_tags) > self.max_tags_per_image:
                    # Prioritize by category order and confidence
                    filtered_tags = filtered_tags[:self.max_tags_per_image]
                    # Rebuild categories with limited tags
                    filtered_categories = {}
                    for category, tags in ai_result.tag_categories.items():
                        category_tags = [tag for tag in tags if tag in filtered_tags]
                        if category_tags:
                            filtered_categories[category] = category_tags
                
                result.tags = filtered_tags
                result.status = TagStatus.COMPLETED
                result.application_time = ai_result.generation_time
                
                logger.info(f"AI generated {len(filtered_tags)} tags for {image_path.name} (confidence: {ai_result.confidence:.2f})")
                
            else:
                # AI failed or low confidence - handle fallback
                if self.fallback_to_patterns:
                    logger.info(f"AI tag generation failed (confidence: {ai_result.confidence:.2f}), falling back to pattern matching")
                    result = self._apply_pattern_tags(image_path)
                else:
                    result.status = TagStatus.ERROR
                    result.error_message = f"AI confidence too low: {ai_result.confidence:.2f} < {self.ai_confidence_threshold}"
                    
        except Exception as e:
            logger.error(f"AI tag generation error for {image_path.name}: {e}")
            
            # Fallback to pattern matching if enabled
            if self.fallback_to_patterns:
                logger.info("AI tag generation failed, falling back to pattern matching")
                result = self._apply_pattern_tags(image_path)
            else:
                result.status = TagStatus.ERROR
                result.error_message = f"AI tag generation failed: {str(e)}"
        
        return result
    
    def extract_tags_from_alt_text(self, alt_text: str) -> TagResult:
        """
        Extract tags from alt text using semantic analysis.
        
        Args:
            alt_text: The alt text description to analyze
            
        Returns:
            TagResult with extracted tags
        """
        result = TagResult()
        
        if not self.semantic_extraction_enabled:
            result.status = TagStatus.ERROR
            result.error_message = "Semantic tag extraction not enabled"
            return result
        
        if not self._semantic_extractor:
            self.enable_semantic_extraction(True)
        
        try:
            start_time = time.time()
            
            # Extract tags using semantic analysis
            extraction_result = self._semantic_extractor.extract_and_validate_tags(
                alt_text, 
                confidence_threshold=self.semantic_confidence_threshold
            )
            
            result.tags = extraction_result.tags
            result.status = extraction_result.status
            result.error_message = extraction_result.error_message
            result.application_time = time.time() - start_time
            
            if result.status == TagStatus.COMPLETED:
                logger.info(f"Extracted {len(result.tags)} semantic tags from alt text")
            else:
                logger.warning(f"Semantic tag extraction failed: {result.error_message}")
                
        except Exception as e:
            result.status = TagStatus.ERROR
            result.error_message = f"Semantic tag extraction error: {str(e)}"
            logger.error(f"Failed to extract semantic tags from alt text: {e}")
        
        return result
    
    def _apply_pattern_tags(self, image_path: Path) -> TagResult:
        """
        Apply tags based on filename patterns (fallback method).
        
        Args:
            image_path: Path to the image file
            
        Returns:
            TagResult with pattern-based tags
        """
        result = TagResult()
        result.status = TagStatus.APPLYING
        
        try:
            assigned_tags = []
            filename_lower = image_path.name.lower()
            
            # Content-based tags
            if any(word in filename_lower for word in ['portrait', 'person', 'people']):
                assigned_tags.extend(['person', 'portrait'])
            elif any(word in filename_lower for word in ['landscape', 'nature', 'outdoor']):
                assigned_tags.extend(['landscape'])
            elif any(word in filename_lower for word in ['food', 'restaurant', 'kitchen']):
                assigned_tags.extend(['food'])
            elif any(word in filename_lower for word in ['tech', 'computer', 'device']):
                assigned_tags.extend(['technology'])
            else:
                assigned_tags.append('object')  # Default content tag
            
            # Style-based tags
            if any(word in filename_lower for word in ['portrait']):
                assigned_tags.append('portrait')
            elif any(word in filename_lower for word in ['wide', 'landscape']):
                assigned_tags.append('wide-shot')
            
            # Remove duplicates and limit
            assigned_tags = list(set(assigned_tags))[:self.max_tags_per_image]
            
            
            result.tags = assigned_tags
            result.status = TagStatus.COMPLETED
            result.application_time = 0.1  # Minimal processing time
            
            logger.debug(f"Applied {len(assigned_tags)} pattern-based tags to {image_path.name}")
            
        except Exception as e:
            result.status = TagStatus.ERROR
            result.error_message = f"Pattern tag assignment failed: {str(e)}"
            logger.error(f"Failed to apply pattern tags to {image_path.name}: {e}")
        
        return result
    
    async def apply_ai_tags(self, tags_or_image: List[str] | Path, filename: str = "", progress_callback: Optional[Callable] = None) -> TagResult:
        """
        Apply tags to an image using AI analysis or validate provided tags.
        
        Args:
            tags_or_image: Either a list of tags to validate or an image path for AI analysis
            filename: Filename for logging (if providing tags)
            progress_callback: Optional progress callback
            
        Returns:
            TagResult with applied tags
        """
        start_time = time.time()
        
        if isinstance(tags_or_image, Path):
            # AI analysis mode
            if progress_callback:
                progress_callback(0, f"Analyzing image with AI: {tags_or_image.name}")
            
            result = await self.generate_ai_tags(tags_or_image)
            
            if progress_callback:
                progress_callback(100, f"AI analysis complete: {tags_or_image.name}")
                
        else:
            # Tag validation mode
            if progress_callback:
                progress_callback(0, f"Validating tags for {filename}")
            
            result = self.validate_tags(tags_or_image, filename)
            
            if progress_callback:
                progress_callback(100, f"Tags validated for {filename}")
        
        return result
    
    async def bulk_ai_tag_generation(self, image_paths: List[Path], progress_callback: Optional[Callable] = None) -> Dict[str, TagResult]:
        """
        Generate AI tags for multiple images.
        
        Args:
            image_paths: List of image paths to process
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary mapping image paths to TagResults
        """
        results = {}
        total_images = len(image_paths)
        
        if not self.ai_generation_enabled:
            logger.error("AI tag generation not enabled for bulk operation")
            return results
        
        try:
            # Use AI tag generator's async context manager
            async with self._ai_tag_generator:
                for i, image_path in enumerate(image_paths):
                    if progress_callback:
                        progress_callback(
                            int((i / total_images) * 100),
                            f"AI analyzing {image_path.name} ({i+1}/{total_images})"
                        )
                    
                    result = await self.generate_ai_tags(image_path)
                    results[str(image_path)] = result
                    
                    # Small delay to avoid overwhelming the API
                    await asyncio.sleep(0.1)
            
            if progress_callback:
                progress_callback(100, f"AI tag generation complete for {total_images} images")
                
        except Exception as e:
            logger.error(f"Bulk AI tag generation failed: {e}")
            
        return results
    
    def _get_semantically_related_tags(self, existing_tags: List[str]) -> List[str]:
        """
        Get tags that are semantically related to existing tags.
        
        Args:
            existing_tags: List of current tags
            
        Returns:
            List of related tags
        """
        if not existing_tags:
            return []
        
        related = []
        
        # Define semantic relationships
        semantic_groups = {
            'people': ['person', 'people', 'man', 'woman', 'child', 'professional', 'executive', 'individual'],
            'business': ['office', 'corporate', 'professional', 'meeting', 'conference', 'workplace', 'executive'],
            'nature': ['landscape', 'outdoor', 'natural', 'environment', 'scenic', 'countryside', 'garden'],
            'technology': ['computer', 'device', 'digital', 'software', 'tech', 'electronic', 'modern'],
            'photography': ['portrait', 'close-up', 'wide-shot', 'lighting', 'composition', 'artistic', 'professional'],
            'mood': ['serious', 'cheerful', 'confident', 'relaxed', 'dynamic', 'peaceful', 'energetic'],
            'style': ['modern', 'contemporary', 'vintage', 'classic', 'elegant', 'minimalist', 'artistic']
        }
        
        # Find semantic groups that match existing tags
        for tag in existing_tags:
            tag_lower = tag.lower()
            for group_name, group_tags in semantic_groups.items():
                if tag_lower in group_tags:
                    # Add other tags from the same semantic group
                    for related_tag in group_tags:
                        if related_tag != tag_lower and related_tag not in existing_tags and related_tag not in related:
                            related.append(related_tag)
        
        return related[:6]  # Limit to prevent overwhelming suggestions
    
    def organize_tags_semantically(self, tags: List[str]) -> Dict[str, List[str]]:
        """
        Organize tags into semantic groups dynamically.
        
        Args:
            tags: List of tags to organize
            
        Returns:
            Dictionary mapping semantic groups to tag lists
        """
        organization = {
            'Content': [],      # What's in the image
            'People': [],       # Human subjects
            'Style': [],        # Visual and aesthetic qualities
            'Technical': [],    # Photography and technical aspects
            'Context': [],      # Setting and environment
            'Mood': []          # Emotional and atmospheric qualities
        }
        
        # Define flexible categorization patterns
        categorization_rules = {
            'People': [
                r'\b(?:person|people|man|woman|child|individual|professional|executive|team|group)\b',
                r'\b(?:sitting|standing|walking|smiling|working|presenting|meeting)\b'
            ],
            'Content': [
                r'\b(?:building|object|food|product|tool|equipment|furniture|vehicle)\b',
                r'\b(?:document|book|screen|display|artwork|plant|animal)\b'
            ],
            'Style': [
                r'\b(?:modern|contemporary|vintage|classic|elegant|minimalist|artistic|colorful)\b',
                r'\b(?:black-white|monochrome|vibrant|muted|dramatic|soft|bright)\b'
            ],
            'Technical': [
                r'\b(?:portrait|close-up|wide-shot|macro|aerial|overhead|telephoto)\b',
                r'\b(?:lighting|natural|artificial|studio|professional|high-resolution)\b'
            ],
            'Context': [
                r'\b(?:office|outdoor|indoor|studio|conference|meeting|restaurant|home)\b',
                r'\b(?:background|environment|setting|workspace|urban|rural)\b'
            ],
            'Mood': [
                r'\b(?:serious|cheerful|confident|relaxed|dynamic|peaceful|energetic)\b',
                r'\b(?:contemplative|focused|casual|formal|friendly|professional)\b'
            ]
        }
        
        # Organize tags based on patterns
        for tag in tags:
            tag_lower = tag.lower()
            categorized = False
            
            for category, patterns in categorization_rules.items():
                if any(re.search(pattern, tag_lower) for pattern in patterns):
                    organization[category].append(tag)
                    categorized = True
                    break
            
            # If not categorized by patterns, use simple heuristics
            if not categorized:
                if len(tag.split()) > 1:  # Multi-word tags often describe style or context
                    organization['Style'].append(tag)
                else:  # Single words often describe content
                    organization['Content'].append(tag)
        
        # Remove empty categories
        return {category: tags for category, tags in organization.items() if tags}
    
    def get_ai_status(self) -> Dict[str, Any]:
        """
        Get current AI tag generation status.
        
        Returns:
            Dictionary with AI status information
        """
        status = {
            "ai_enabled": self.ai_generation_enabled,
            "confidence_threshold": self.ai_confidence_threshold,
            "max_tags_per_category": self.ai_max_tags_per_category,
            "fallback_enabled": self.fallback_to_patterns
        }
        
        if self._ai_tag_generator:
            status.update(self._ai_tag_generator.get_rate_limit_status())
        
        return status