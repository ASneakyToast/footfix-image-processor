"""
AI-powered tag generation for FootFix.
Integrates with Anthropic's Claude Vision API to generate intelligent tag assignments based on image content.
"""

import logging
import asyncio
import base64
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import aiohttp
from PIL import Image
import io

from .tag_manager import TagStatus, TagCategory

logger = logging.getLogger(__name__)


class AITagStatus(Enum):
    """Status of AI tag generation."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class AITagResult:
    """Result of AI tag generation for a single image."""
    tags: List[str] = None
    tag_categories: Dict[str, List[str]] = None
    confidence: float = 0.0
    status: AITagStatus = AITagStatus.PENDING
    error_message: Optional[str] = None
    generation_time: float = 0.0
    api_cost: float = 0.0  # Estimated cost in USD
    raw_response: Optional[str] = None  # For debugging
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.tag_categories is None:
            self.tag_categories = {}


class AITagGenerator:
    """
    Generates intelligent tag assignments for images using Claude Vision API.
    Optimized for editorial content with structured category-based tagging.
    """
    
    # API configuration
    API_BASE_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    MODEL = "claude-3-5-sonnet-20241022"  # Using Claude 3.5 Sonnet for vision support
    MAX_TOKENS = 500  # More tokens for structured JSON response
    TEMPERATURE = 0.2  # Lower temperature for more consistent tag assignment
    
    # Rate limiting configuration (shared with alt text generator)
    MAX_REQUESTS_PER_MINUTE = 50
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    RETRY_BACKOFF_FACTOR = 2.0  # Exponential backoff multiplier
    MAX_RETRY_DELAY = 60.0  # Maximum delay between retries
    
    # Error handling configuration
    NETWORK_TIMEOUT = 30  # seconds
    CONNECTION_TIMEOUT = 10  # seconds
    READ_TIMEOUT = 20  # seconds
    
    def __init__(self, api_key: Optional[str] = None, tag_categories: Optional[Dict[str, TagCategory]] = None):
        """
        Initialize the AI tag generator.
        
        Args:
            api_key: Anthropic API key (if not provided, will look in preferences)
            tag_categories: Available tag categories for assignment
        """
        self.api_key = api_key
        self.tag_categories = tag_categories or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._request_times: List[float] = []
        self._semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        self._error_callbacks: List[Callable] = []
        self._usage_tracker = None
        
        # Initialize preferences manager for usage tracking
        try:
            from ..utils.preferences import PreferencesManager
            self._prefs_manager = PreferencesManager()
        except:
            self._prefs_manager = None
        
        # Build system prompt based on available categories
        self._build_system_prompt()
        
    def _build_system_prompt(self):
        """Build the system prompt based on available tag categories."""
        self.system_prompt = """You are an expert image analyst specializing in editorial content tagging.
Your task is to analyze images and assign appropriate tags from predefined categories.

Guidelines:
- Analyze the visual content carefully and objectively
- Focus on what is clearly visible in the image
- Consider composition, style, subjects, and context
- Be conservative with tag assignments - only assign tags you're confident about
- Provide a confidence score between 0.1 and 1.0 for your overall assessment

Response format: Return ONLY a valid JSON object with this exact structure:
{
  "tags": {
    "Content": ["tag1", "tag2"],
    "Style": ["tag3"],
    "Usage": ["tag4"],
    "Editorial": ["tag5"]
  },
  "confidence": 0.85,
  "reasoning": "Brief explanation of key visual elements that influenced tag selection"
}

Important:
- Only use tags from the provided category lists
- Don't assign tags to categories that don't apply
- Empty categories should be omitted from the response
- Confidence should reflect your certainty about the tag assignments"""

    def set_api_key(self, api_key: str):
        """Set or update the API key."""
        self.api_key = api_key
        logger.info("AI tag generator API key updated")
        
    def set_tag_categories(self, tag_categories: Dict[str, TagCategory]):
        """Set or update the available tag categories."""
        self.tag_categories = tag_categories
        logger.info(f"AI tag generator updated with {len(tag_categories)} categories")
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    def _encode_image(self, image_path: Path) -> Optional[str]:
        """
        Encode image to base64 for API.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string or None if failed
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large (API limits)
                max_size = 1568  # Claude's recommended max dimension
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Encode to JPEG
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                image_bytes = buffer.getvalue()
                
                return base64.b64encode(image_bytes).decode('utf-8')
                
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            return None
            
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.
        
        Returns:
            True if we can make a request, False if rate limited
        """
        current_time = time.time()
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if current_time - t < 60]
        
        # Check if we've hit the limit
        if len(self._request_times) >= self.MAX_REQUESTS_PER_MINUTE:
            return False
            
        # Add current request time
        self._request_times.append(current_time)
        return True
        
    async def _wait_for_rate_limit(self):
        """Wait until we can make another request."""
        while not self._check_rate_limit():
            # Calculate how long to wait
            if self._request_times:
                oldest_request = min(self._request_times)
                wait_time = 60 - (time.time() - oldest_request) + 1
                logger.info(f"AI tag generation rate limited, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(1)
                
    def _build_user_prompt(self, context: Optional[str] = None) -> str:
        """
        Build the user prompt with current tag categories.
        
        Args:
            context: Optional context about the image
            
        Returns:
            Formatted user prompt string
        """
        prompt_parts = ["Analyze this image and assign appropriate tags from these categories:\\n"]
        
        # Add each category with its available tags
        for category_name, category in self.tag_categories.items():
            tag_list = ", ".join(category.predefined_tags)
            prompt_parts.append(f"- {category_name}: [{tag_list}]")
        
        prompt_parts.append("\\nOnly assign tags that clearly apply to the image content.")
        
        if context:
            prompt_parts.append(f"\\nContext: {context}")
            
        prompt_parts.append("\\nReturn the response as JSON following the specified format.")
        
        return "\\n".join(prompt_parts)
        
    def _parse_tag_response(self, response_text: str) -> AITagResult:
        """
        Parse the AI response into structured tag data.
        
        Args:
            response_text: Raw response from Claude
            
        Returns:
            AITagResult with parsed tag data
        """
        result = AITagResult()
        result.raw_response = response_text
        
        try:
            # Clean response text - sometimes Claude adds extra text around JSON
            response_text = response_text.strip()
            
            # Find JSON object in response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in response")
                
            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)
            
            # Extract tags by category
            if "tags" in data and isinstance(data["tags"], dict):
                result.tag_categories = {}
                all_tags = []
                
                for category, tags in data["tags"].items():
                    if isinstance(tags, list) and tags:
                        # Validate tags against available categories
                        if category in self.tag_categories:
                            valid_tags = []
                            available_tags = [tag.lower() for tag in self.tag_categories[category].predefined_tags]
                            
                            for tag in tags:
                                if isinstance(tag, str) and tag.lower() in available_tags:
                                    valid_tags.append(tag.lower())
                            
                            if valid_tags:
                                result.tag_categories[category] = valid_tags
                                all_tags.extend(valid_tags)
                
                result.tags = all_tags
                
            # Extract confidence
            if "confidence" in data:
                try:
                    confidence = float(data["confidence"])
                    result.confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
                except (ValueError, TypeError):
                    result.confidence = 0.5  # Default if invalid
                    
            # If we got valid tags, mark as completed
            if result.tags:
                result.status = AITagStatus.COMPLETED
                logger.debug(f"Parsed {len(result.tags)} tags with confidence {result.confidence}")
            else:
                result.status = AITagStatus.ERROR
                result.error_message = "No valid tags found in AI response"
                
        except json.JSONDecodeError as e:
            result.status = AITagStatus.ERROR
            result.error_message = f"Invalid JSON in AI response: {str(e)}"
            logger.warning(f"Failed to parse AI tag response as JSON: {e}")
            
        except Exception as e:
            result.status = AITagStatus.ERROR
            result.error_message = f"Failed to parse AI response: {str(e)}"
            logger.error(f"Error parsing AI tag response: {e}")
            
        return result
        
    async def generate_tags(self, image_path: Path, context: Optional[str] = None) -> AITagResult:
        """
        Generate tags for a single image using AI analysis.
        
        Args:
            image_path: Path to the image file
            context: Optional context about the image (e.g., "fashion editorial", "product shot")
            
        Returns:
            AITagResult with generated tags or error
        """
        start_time = time.time()
        result = AITagResult()
        
        if not self.api_key:
            result.status = AITagStatus.ERROR
            result.error_message = "No API key provided"
            return result
            
        if not self.tag_categories:
            result.status = AITagStatus.ERROR
            result.error_message = "No tag categories configured"
            return result
            
        # Encode image
        image_base64 = self._encode_image(image_path)
        if not image_base64:
            result.status = AITagStatus.ERROR
            result.error_message = f"Failed to encode image: {image_path}"
            return result
            
        # Build user prompt
        user_prompt = self._build_user_prompt(context)
        
        # Prepare API request
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.MODEL,
            "max_tokens": self.MAX_TOKENS,
            "temperature": self.TEMPERATURE,
            "system": self.system_prompt,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }]
        }
        
        # Make API request with retries
        async with self._semaphore:  # Limit concurrent requests
            for attempt in range(self.MAX_RETRIES):
                try:
                    # Check rate limit
                    await self._wait_for_rate_limit()
                    
                    result.status = AITagStatus.ANALYZING
                    
                    async with self.session.post(
                        self.API_BASE_URL,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(
                            total=self.NETWORK_TIMEOUT,
                            connect=self.CONNECTION_TIMEOUT,
                            sock_read=self.READ_TIMEOUT
                        )
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            # Extract response text
                            if data.get("content") and len(data["content"]) > 0:
                                response_text = data["content"][0]["text"]
                                
                                # Parse the structured tag response
                                result = self._parse_tag_response(response_text)
                                result.generation_time = time.time() - start_time
                                
                                if result.status == AITagStatus.COMPLETED:
                                    logger.info(f"Generated {len(result.tags)} AI tags for {image_path.name} (confidence: {result.confidence:.2f})")
                                
                                # Track usage if enabled
                                self._track_usage(result.api_cost)
                                break
                            else:
                                raise ValueError("No content in API response")
                                
                        elif response.status == 429:
                            # Rate limited
                            result.status = AITagStatus.RATE_LIMITED
                            result.error_message = "Rate limited by API"
                            retry_after = int(response.headers.get("retry-after", 60))
                            logger.warning(f"AI tag generation rate limited, retry after {retry_after}s")
                            
                            # Wait for rate limit to clear
                            if attempt < self.MAX_RETRIES - 1:
                                await asyncio.sleep(min(retry_after, self.MAX_RETRY_DELAY))
                                continue
                            
                        elif response.status == 401:
                            # Invalid API key - don't retry
                            result.error_message = "Invalid API key - please check your Anthropic API key"
                            logger.error("Invalid API key provided for AI tag generation")
                            break
                            
                        elif response.status == 404:
                            # Model not found - likely deprecated model
                            result.error_message = "Model not found - please update FootFix to the latest version"
                            logger.error(f"Model {self.MODEL} not found for AI tag generation")
                            break
                            
                        elif response.status >= 500:
                            # Server error - retry
                            result.error_message = f"Server error: {response.status}"
                            delay = self.RETRY_DELAY * (self.RETRY_BACKOFF_FACTOR ** attempt)
                            delay = min(delay, self.MAX_RETRY_DELAY)
                            logger.warning(f"Server error {response.status}, retrying in {delay:.1f}s")
                            
                            if attempt < self.MAX_RETRIES - 1:
                                await asyncio.sleep(delay)
                                continue
                            
                        else:
                            # Other client error - don't retry
                            result.error_message = f"API error: {response.status}"
                            logger.error(f"AI tag generation API error: {response.status}")
                            break
                            
                except asyncio.TimeoutError:
                    result.error_message = "Request timeout"
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF_FACTOR ** attempt)
                    delay = min(delay, self.MAX_RETRY_DELAY)
                    logger.warning(f"AI tag generation timeout, retrying in {delay:.1f}s")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    
                except aiohttp.ClientError as e:
                    result.error_message = f"Network error: {str(e)}"
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF_FACTOR ** attempt)
                    delay = min(delay, self.MAX_RETRY_DELAY)
                    logger.warning(f"AI tag generation network error: {e}, retrying in {delay:.1f}s")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    
                except Exception as e:
                    result.error_message = f"Unexpected error: {str(e)}"
                    logger.error(f"Unexpected error in AI tag generation: {e}")
                    break
                    
        # Set final error status if we failed all retries
        if result.status == AITagStatus.ANALYZING:
            result.status = AITagStatus.ERROR
            
        result.generation_time = time.time() - start_time
        return result
        
    def _track_usage(self, cost: Optional[float]):
        """Track API usage for billing/monitoring."""
        # Implementation would depend on usage tracking requirements
        pass
        
    def register_error_callback(self, callback: Callable):
        """Register a callback for error notifications."""
        self._error_callbacks.append(callback)
        
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        current_time = time.time()
        recent_requests = [t for t in self._request_times if current_time - t < 60]
        
        return {
            "requests_in_last_minute": len(recent_requests),
            "max_requests_per_minute": self.MAX_REQUESTS_PER_MINUTE,
            "remaining_requests": max(0, self.MAX_REQUESTS_PER_MINUTE - len(recent_requests)),
            "rate_limited": len(recent_requests) >= self.MAX_REQUESTS_PER_MINUTE
        }