"""
AI-powered alt text generation for FootFix.
Integrates with Anthropic's Claude Vision API to generate editorial-quality alt text descriptions.
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

logger = logging.getLogger(__name__)


class AltTextStatus(Enum):
    """Status of alt text generation."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class AltTextResult:
    """Result of alt text generation for a single image."""
    alt_text: Optional[str] = None
    status: AltTextStatus = AltTextStatus.PENDING
    error_message: Optional[str] = None
    generation_time: float = 0.0
    api_cost: float = 0.0  # Estimated cost in USD


class AltTextGenerator:
    """
    Generates alt text descriptions for images using Claude Vision API.
    Optimized for editorial content with rate limiting and error recovery.
    """
    
    # API configuration
    API_BASE_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    MODEL = "claude-3-5-sonnet-20241022"  # Using Claude 3.5 Sonnet for cost-effectiveness and vision support
    MAX_TOKENS = 300
    TEMPERATURE = 0.3  # Lower temperature for more consistent descriptions
    
    # Rate limiting configuration
    MAX_REQUESTS_PER_MINUTE = 50
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    RETRY_BACKOFF_FACTOR = 2.0  # Exponential backoff multiplier
    MAX_RETRY_DELAY = 60.0  # Maximum delay between retries
    
    # Cost estimation (approximate)
    COST_PER_IMAGE = 0.006  # $0.006 per image analysis
    
    # Error handling configuration
    NETWORK_TIMEOUT = 30  # seconds
    CONNECTION_TIMEOUT = 10  # seconds
    READ_TIMEOUT = 20  # seconds
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the alt text generator.
        
        Args:
            api_key: Anthropic API key (if not provided, will look in preferences)
        """
        self.api_key = api_key
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
        
        # Editorial content prompt optimization
        self.system_prompt = """You are an expert at writing alt text descriptions for editorial images. 
Your descriptions should be:
- Concise yet informative (50-150 words)
- Focused on the main subject and context
- Descriptive of visual elements important for understanding
- Professional and appropriate for publication
- Avoiding redundant phrases like "image of" or "picture showing"

For editorial content, emphasize:
- People: their appearance, expressions, clothing, and actions
- Settings: location, atmosphere, and relevant background elements
- Products: key features, styling, and presentation
- Composition: how elements are arranged and what draws attention"""
        
    def set_api_key(self, api_key: str):
        """Set or update the API key."""
        self.api_key = api_key
        logger.info("API key updated")
        
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
        Encode image to base64 for API submission.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string or None if error
        """
        try:
            # Open and potentially resize image to optimize API usage
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                    
                # Resize if very large (max 2048px on longest side)
                max_size = 2048
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                # Save to bytes
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                
                # Encode to base64
                return base64.b64encode(buffer.read()).decode('utf-8')
                
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
                logger.info(f"Rate limited, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(1)
                
    async def generate_alt_text(self, image_path: Path, context: Optional[str] = None) -> AltTextResult:
        """
        Generate alt text for a single image.
        
        Args:
            image_path: Path to the image file
            context: Optional context about the image (e.g., "fashion editorial", "product shot")
            
        Returns:
            AltTextResult with generated description or error
        """
        start_time = time.time()
        result = AltTextResult()
        
        if not self.api_key:
            result.status = AltTextStatus.ERROR
            result.error_message = "API key not configured"
            return result
            
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        # Encode image
        image_base64 = self._encode_image(image_path)
        if not image_base64:
            result.status = AltTextStatus.ERROR
            result.error_message = "Failed to encode image"
            return result
            
        # Build user prompt
        user_prompt = "Please write an alt text description for this image."
        if context:
            user_prompt += f" Context: {context}"
            
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
                    
                    result.status = AltTextStatus.GENERATING
                    
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
                            # Extract alt text from response
                            if data.get("content") and len(data["content"]) > 0:
                                result.alt_text = data["content"][0]["text"].strip()
                                result.status = AltTextStatus.COMPLETED
                                result.api_cost = self.COST_PER_IMAGE
                                logger.info(f"Generated alt text for {image_path.name}")
                                
                                # Track usage if enabled
                                self._track_usage(result.api_cost)
                                break
                            else:
                                raise ValueError("No content in API response")
                                
                        elif response.status == 429:
                            # Rate limited
                            result.status = AltTextStatus.RATE_LIMITED
                            result.error_message = "Rate limited by API"
                            retry_after = int(response.headers.get("retry-after", 60))
                            logger.warning(f"Rate limited, retry after {retry_after}s")
                            
                            # Wait for rate limit to clear
                            if attempt < self.MAX_RETRIES - 1:
                                await asyncio.sleep(min(retry_after, self.MAX_RETRY_DELAY))
                                continue
                            
                        elif response.status == 401:
                            # Invalid API key - don't retry
                            result.error_message = "Invalid API key - please check your Anthropic API key"
                            logger.error("Invalid API key provided")
                            break
                            
                        elif response.status == 404:
                            # Model not found - likely deprecated model
                            result.error_message = "Model not found - please update FootFix to the latest version"
                            logger.error(f"Model {self.MODEL} not found - may be deprecated")
                            break
                            
                        elif response.status >= 500:
                            # Server error - retry with backoff
                            error_data = await response.text()
                            result.error_message = f"Anthropic server error: {response.status}"
                            logger.error(f"Server error {response.status}: {error_data}")
                            
                        else:
                            # Client error - log but retry
                            error_data = await response.text()
                            result.error_message = f"API error {response.status}: {error_data[:100]}"
                            logger.error(f"API error {response.status}: {error_data}")
                            
                except asyncio.TimeoutError:
                    result.error_message = "Request timeout - network may be slow"
                    logger.error(f"Timeout generating alt text for {image_path.name}")
                    
                except aiohttp.ClientError as e:
                    # Network errors
                    result.error_message = f"Network error: {type(e).__name__}"
                    logger.error(f"Network error for {image_path.name}: {e}")
                    
                except Exception as e:
                    result.error_message = f"Unexpected error: {str(e)}"
                    logger.error(f"Error generating alt text for {image_path.name}: {e}")
                    
                # Retry with exponential backoff
                if attempt < self.MAX_RETRIES - 1 and result.status != AltTextStatus.COMPLETED:
                    retry_delay = min(
                        self.RETRY_DELAY * (self.RETRY_BACKOFF_FACTOR ** attempt),
                        self.MAX_RETRY_DELAY
                    )
                    logger.info(f"Retrying in {retry_delay:.1f} seconds (attempt {attempt + 2}/{self.MAX_RETRIES})")
                    await asyncio.sleep(retry_delay)
                    
        # Final status check
        if result.status != AltTextStatus.COMPLETED:
            result.status = AltTextStatus.ERROR
            
        result.generation_time = time.time() - start_time
        return result
        
    async def generate_batch(
        self, 
        image_paths: List[Path], 
        progress_callback: Optional[callable] = None
    ) -> Dict[Path, AltTextResult]:
        """
        Generate alt text for multiple images.
        
        Args:
            image_paths: List of image paths to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping image paths to results
        """
        results = {}
        
        for i, image_path in enumerate(image_paths):
            # Generate alt text
            result = await self.generate_alt_text(image_path)
            results[image_path] = result
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, len(image_paths), image_path, result)
                
        return results
        
    def estimate_batch_cost(self, num_images: int) -> Dict[str, float]:
        """
        Estimate the cost for processing a batch of images.
        
        Args:
            num_images: Number of images to process
            
        Returns:
            Dictionary with cost estimates
        """
        return {
            "per_image": self.COST_PER_IMAGE,
            "total": self.COST_PER_IMAGE * num_images,
            "monthly_estimate": self.COST_PER_IMAGE * num_images * 20  # Assuming 20 batches/month
        }
        
    def _track_usage(self, cost: float):
        """
        Track API usage and costs.
        
        Args:
            cost: Cost of the API request
        """
        if not self._prefs_manager or not self._prefs_manager.get('alt_text.enable_cost_tracking', True):
            return
            
        try:
            # Get current stats
            stats = self._prefs_manager.get('alt_text.usage_stats', {})
            if not stats:
                stats = {'total': {'requests': 0, 'cost': 0}, 'monthly': {}}
                
            # Update total stats
            stats['total']['requests'] = stats['total'].get('requests', 0) + 1
            stats['total']['cost'] = stats['total'].get('cost', 0) + cost
            
            # Update monthly stats
            current_month = datetime.now().strftime("%Y-%m")
            if current_month not in stats['monthly']:
                stats['monthly'][current_month] = {'requests': 0, 'cost': 0}
                
            stats['monthly'][current_month]['requests'] += 1
            stats['monthly'][current_month]['cost'] += cost
            
            # Save updated stats
            self._prefs_manager.set('alt_text.usage_stats', stats)
            
        except Exception as e:
            logger.warning(f"Failed to track usage: {e}")
            
    def add_error_callback(self, callback: Callable):
        """
        Add a callback for error notifications.
        
        Args:
            callback: Function to call on errors
        """
        self._error_callbacks.append(callback)
        
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        if not self._prefs_manager:
            return {}
            
        return self._prefs_manager.get('alt_text.usage_stats', {})
        
    async def validate_api_key(self) -> tuple[bool, str]:
        """
        Validate the API key with a minimal vision request.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not self.api_key:
            return False, "No API key provided"
            
        try:
            async with self:
                # Create a minimal test image (1x1 white pixel)
                from PIL import Image
                import io
                import base64
                
                img = Image.new('RGB', (1, 1), color='white')
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                image_data = base64.b64encode(buffer.read()).decode('utf-8')
                
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": self.API_VERSION,
                    "content-type": "application/json"
                }
                
                payload = {
                    "model": self.MODEL,
                    "max_tokens": 10,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": "test"
                            }
                        ]
                    }]
                }
                
                async with self.session.post(
                    self.API_BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True, "API key is valid and supports vision"
                    elif response.status == 401:
                        return False, "Invalid API key"
                    elif response.status == 429:
                        return True, "API key is valid (currently rate limited)"
                    elif response.status == 404:
                        return False, f"Model not found - API may need updating"
                    else:
                        error_text = await response.text()
                        return False, f"API error {response.status}: {error_text[:100]}"
                        
        except Exception as e:
            return False, f"Connection error: {str(e)}"