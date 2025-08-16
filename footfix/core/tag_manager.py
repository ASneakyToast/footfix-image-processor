"""
Tag management system for FootFix.
Provides configurable tag assignment and management for image processing workflows.
"""

import logging
import json
import time
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
    tag_categories: Dict[str, List[str]] = field(default_factory=dict)  # category -> tags


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
        
        # Initialize default categories
        self._initialize_default_categories()
        
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
        """Get suggested tags based on existing tags and categories."""
        if not self.auto_suggest:
            return []
            
        existing_tags = existing_tags or []
        suggestions = []
        
        # Add popular tags from each category
        for category in self.categories.values():
            for tag in category.predefined_tags[:3]:  # Top 3 from each category
                if tag not in existing_tags and tag not in suggestions:
                    suggestions.append(tag)
        
        return suggestions[:10]  # Limit suggestions
    
    def validate_tags(self, tags: List[str], filename: str = "") -> TagResult:
        """Validate a list of tags against category rules."""
        result = TagResult()
        result.status = TagStatus.APPLYING
        
        try:
            # Check maximum tags limit
            if len(tags) > self.max_tags_per_image:
                result.status = TagStatus.ERROR
                result.error_message = f"Too many tags: {len(tags)} > {self.max_tags_per_image}"
                return result
            
            # Validate against category constraints
            validated_tags = []
            category_counts = {}
            
            for tag in tags:
                tag = tag.strip().lower()
                if not tag:
                    continue
                    
                # Find which category this tag belongs to
                tag_category = None
                for cat_name, category in self.categories.items():
                    if tag in [t.lower() for t in category.predefined_tags] or category.allow_custom:
                        tag_category = cat_name
                        break
                
                if tag_category:
                    category_counts[tag_category] = category_counts.get(tag_category, 0) + 1
                    
                    # Check category max_tags constraint
                    category = self.categories[tag_category]
                    if category.max_tags and category_counts[tag_category] > category.max_tags:
                        result.status = TagStatus.ERROR
                        result.error_message = f"Too many tags for category '{tag_category}': {category_counts[tag_category]} > {category.max_tags}"
                        return result
                
                validated_tags.append(tag)
            
            # Check required categories
            for cat_name, category in self.categories.items():
                if category.required and cat_name not in category_counts:
                    result.status = TagStatus.ERROR
                    result.error_message = f"Required category '{cat_name}' has no tags"
                    return result
            
            # Build category mapping
            result.tag_categories = {}
            for tag in validated_tags:
                for cat_name, category in self.categories.items():
                    if tag in [t.lower() for t in category.predefined_tags] or category.allow_custom:
                        if cat_name not in result.tag_categories:
                            result.tag_categories[cat_name] = []
                        result.tag_categories[cat_name].append(tag)
                        break
            
            result.tags = validated_tags
            result.status = TagStatus.COMPLETED
            logger.debug(f"Validated {len(validated_tags)} tags for {filename}")
            
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
            
            logger.info("Tag manager configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set tag manager config: {e}")
            return False