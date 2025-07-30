"""Format routing system for selecting appropriate text formatting based on deployment type.

This module provides functionality to detect Atlassian deployment types (Cloud vs Server/DC)
and route markdown conversion to the appropriate formatter (ADF for Cloud, wiki markup for Server/DC).

Performance optimizations:
- TTL-based caching for deployment detection results
- Performance metrics for monitoring and optimization
- Efficient URL pattern matching with regex compilation
- Smart caching with configurable TTL and size limits
"""

import logging
import re
import time
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from cachetools import TTLCache

from .adf import ADFGenerator

logger = logging.getLogger(__name__)


class DeploymentType(Enum):
    """Enum representing different Atlassian deployment types."""
    CLOUD = "cloud"
    SERVER = "server"
    DATA_CENTER = "datacenter"
    UNKNOWN = "unknown"


class FormatType(Enum):
    """Enum representing different text format types."""
    ADF = "adf"
    WIKI_MARKUP = "wiki_markup"


class FormatRouter:
    """Router for selecting appropriate text formatting based on deployment type.
    
    Performance optimizations:
    - Compiled regex patterns for faster URL matching
    - TTL cache for deployment detection with configurable size and TTL
    - Performance metrics collection for monitoring
    - Efficient ADF generator initialization with caching
    """

    def __init__(self, cache_ttl: int = 3600, cache_size: int = 100, adf_cache_size: int = 256) -> None:
        """
        Initialize the format router with performance optimizations.
        
        Args:
            cache_ttl: Cache time-to-live in seconds for deployment type detection (default: 1 hour)
            cache_size: Maximum number of deployment detection results to cache (default: 100)
            adf_cache_size: Maximum number of ADF conversions to cache (default: 256)
        """
        self.deployment_cache: TTLCache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        self.adf_generator = ADFGenerator(cache_size=adf_cache_size)

        # Compile regex patterns for better performance
        self._cloud_patterns = [
            re.compile(r'.*\.atlassian\.net', re.IGNORECASE),
            re.compile(r'.*\.atlassian\.com', re.IGNORECASE)
        ]

        # Performance metrics with explicit typing
        self.metrics: dict[str, Any] = {
            'detections_total': 0,
            'detections_cached': 0,
            'conversions_total': 0,
            'detection_time_total': 0.0,
            'conversion_time_total': 0.0,
            'last_error': None
        }

    def convert_markdown(
        self,
        markdown_text: str,
        base_url: str,
        force_format: FormatType | None = None
    ) -> dict[str, Any]:
        """
        Convert markdown text to appropriate format based on deployment type with performance monitoring.
        
        Args:
            markdown_text: Input markdown text to convert
            base_url: Base URL of the Atlassian instance
            force_format: Optional format type to force (bypasses auto-detection)
            
        Returns:
            Dictionary containing:
            - 'content': Converted content (ADF dict or wiki markup string)
            - 'format': Format type used ('adf' or 'wiki_markup')
            - 'deployment_type': Detected deployment type
        """
        start_time = time.time()
        self.metrics['conversions_total'] = self.metrics['conversions_total'] + 1

        try:
            # Determine format type
            if force_format:
                format_type = force_format
                deployment_type = DeploymentType.UNKNOWN
                logger.debug(f"Using forced format: {force_format.value}")
            else:
                deployment_type = self.detect_deployment_type(base_url)
                format_type = self._get_format_for_deployment(deployment_type)
                logger.debug(f"Auto-detected format: {format_type.value} for deployment: {deployment_type.value}")

            # Convert based on format type
            if format_type == FormatType.ADF:
                content = self.adf_generator.markdown_to_adf(markdown_text)
                return {
                    'content': content,
                    'format': 'adf',
                    'deployment_type': deployment_type.value
                }
            else:
                # Use existing wiki markup conversion (fallback)
                wiki_content = self._markdown_to_wiki_markup(markdown_text)
                return {
                    'content': wiki_content,
                    'format': 'wiki_markup',
                    'deployment_type': deployment_type.value
                }

        except Exception as e:
            self.metrics['last_error'] = str(e)
            logger.error(f"Failed to convert markdown: {e}")
            # Fallback to plain text
            return {
                'content': markdown_text,
                'format': 'plain_text',
                'deployment_type': 'unknown',
                'error': str(e)
            }
        finally:
            # Update performance metrics
            conversion_time = time.time() - start_time
            self.metrics['conversion_time_total'] = self.metrics['conversion_time_total'] + conversion_time

            if conversion_time > 0.05:  # Log slow conversions (50ms threshold)
                logger.warning(f"Slow routing conversion: {conversion_time:.3f}s for {len(markdown_text)} chars")

    def detect_deployment_type(self, base_url: str) -> DeploymentType:
        """
        Detect Atlassian deployment type from base URL with performance monitoring.
        
        Args:
            base_url: Base URL of the Atlassian instance
            
        Returns:
            DeploymentType indicating the detected deployment type
        """
        start_time = time.time()
        self.metrics['detections_total'] = self.metrics['detections_total'] + 1

        try:
            if not base_url:
                return DeploymentType.UNKNOWN

            # Check cache first
            cache_key = base_url.lower().strip()
            if cache_key in self.deployment_cache:
                self.metrics['detections_cached'] = self.metrics['detections_cached'] + 1
                logger.debug(f"Deployment detection cache hit for: {cache_key}")
                cached_result = self.deployment_cache[cache_key]
                if isinstance(cached_result, DeploymentType):
                    return cached_result
                # Handle legacy cache entries that might not be DeploymentType
                return DeploymentType.UNKNOWN
            # Check for non-HTTP protocols first (case insensitive)
            lower_url = base_url.lower()
            if lower_url.startswith(('ftp://', 'file://', 'sftp://')):
                # Non-HTTP protocols are not Atlassian services
                return DeploymentType.UNKNOWN
            elif not lower_url.startswith(('http://', 'https://')):
                # URLs without proper schemes are treated as unknown
                return DeploymentType.UNKNOWN

            parsed_url = urlparse(base_url.lower())
            hostname = parsed_url.hostname or ""

            # Use compiled patterns for better performance
            for pattern in self._cloud_patterns:
                if pattern.match(hostname):
                    deployment_type = DeploymentType.CLOUD
                    self.deployment_cache[cache_key] = deployment_type
                    logger.debug(f"Detected Cloud deployment for {hostname}")
                    return deployment_type

            # Check for additional development instances
            if re.match(r'.*\.jira-dev\.com$', hostname):
                deployment_type = DeploymentType.CLOUD
                self.deployment_cache[cache_key] = deployment_type
                logger.debug(f"Detected Cloud development deployment for {hostname}")
                return deployment_type

            # Server/DC detection - typically custom domains
            # If it's not a cloud instance and has a valid hostname, assume Server/DC
            if hostname and not any(cloud_domain in hostname for cloud_domain in ['atlassian.net', 'atlassian.com']):
                deployment_type = DeploymentType.SERVER
                self.deployment_cache[cache_key] = deployment_type
                logger.debug(f"Detected Server/DC deployment for {hostname}")
                return deployment_type

            # Unknown deployment type
            deployment_type = DeploymentType.UNKNOWN
            self.deployment_cache[cache_key] = deployment_type
            logger.warning(f"Could not determine deployment type for {hostname}")
            return deployment_type

        except Exception as e:
            self.metrics['last_error'] = str(e)
            logger.error(f"Error detecting deployment type for {base_url}: {e}")
            return DeploymentType.UNKNOWN
        finally:
            # Update performance metrics
            detection_time = time.time() - start_time
            self.metrics['detection_time_total'] = self.metrics['detection_time_total'] + detection_time

            if detection_time > 0.01:  # Log slow detections (10ms threshold)
                logger.warning(f"Slow deployment detection: {detection_time:.3f}s for {base_url}")

    def _get_format_for_deployment(self, deployment_type: DeploymentType) -> FormatType:
        """
        Get appropriate format type for deployment type.
        
        Args:
            deployment_type: Detected deployment type
            
        Returns:
            FormatType to use for this deployment
        """
        if deployment_type == DeploymentType.CLOUD:
            return FormatType.ADF
        else:
            # Server/DC and Unknown use wiki markup
            return FormatType.WIKI_MARKUP

    def _markdown_to_wiki_markup(self, markdown_text: str) -> str:
        """
        Convert markdown to Jira wiki markup format.
        
        This is a simplified version of the existing conversion logic.
        For production, this should delegate to the existing JiraPreprocessor.
        
        Args:
            markdown_text: Input markdown text
            
        Returns:
            String in Jira wiki markup format
        """
        if not markdown_text:
            return ""

        output = markdown_text

        # Headers - convert # to h1., ## to h2., etc.
        output = re.sub(
            r"^([#]+)(.*?)$",
            lambda match: f"h{len(match.group(1))}.{match.group(2)}",
            output,
            flags=re.MULTILINE,
        )

        # Process formatting: need to handle bold and italic carefully
        # Use a more systematic approach

        # First, handle bold: **text** or __text__ -> BOLD_MARKER_text_BOLD_MARKER
        output = re.sub(r'\*\*([^*]+)\*\*', r'BOLD_MARKER_\1_BOLD_MARKER', output)
        output = re.sub(r'__([^_]+)__', r'BOLD_MARKER_\1_BOLD_MARKER', output)

        # Then handle italic: *text* or _text_ -> _text_
        output = re.sub(r'\*([^*]+)\*', r'_\1_', output)
        output = re.sub(r'(?<!BOLD_MARKER)_([^_]+)_(?!BOLD_MARKER)', r'_\1_', output)

        # Finally convert bold markers back to wiki markup
        output = re.sub(r'BOLD_MARKER_([^_]+)_BOLD_MARKER', r'*\1*', output)

        # Code blocks (```code```) -> {code}code{code}
        output = re.sub(
            r'```(\w+)?\n(.*?)\n```',
            lambda match: f"{{code:{match.group(1) or ''}}}\n{match.group(2)}\n{{code}}",
            output,
            flags=re.DOTALL
        )

        # Inline code (`code`) -> {{code}}
        output = re.sub(r'`([^`]+)`', r'{{\1}}', output)

        # Unordered lists (- item) -> * item
        output = re.sub(r'^- (.*)$', r'* \1', output, flags=re.MULTILINE)

        # Ordered lists (1. item) -> # item
        output = re.sub(r'^\d+\. (.*)$', r'# \1', output, flags=re.MULTILINE)

        # Links [text](url) -> [text|url]
        output = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1|\2]', output)

        return output

    def clear_cache(self) -> None:
        """Clear the deployment type detection cache."""
        self.deployment_cache.clear()
        logger.debug("Cleared deployment type cache")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cache_size': len(self.deployment_cache),
            'cache_maxsize': self.deployment_cache.maxsize,
            'cache_ttl': self.deployment_cache.ttl,
            'cached_deployments': list(self.deployment_cache.keys())
        }

    def get_performance_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive performance metrics for monitoring and optimization.
        
        Returns:
            Dictionary containing performance statistics
        """
        # Get ADF generator metrics
        adf_metrics = self.adf_generator.get_performance_metrics()

        # Calculate router-level metrics
        router_metrics = self.metrics.copy()
        router_metrics.update({
            'detection_cache_hit_rate': (self.metrics['detections_cached'] / max(1, self.metrics['detections_total'])) * 100,
            'average_detection_time': self.metrics['detection_time_total'] / max(1, self.metrics['detections_total']),
            'average_conversion_time': self.metrics['conversion_time_total'] / max(1, self.metrics['conversions_total']),
            'cache_stats': self.get_cache_stats(),
            'adf_generator_metrics': adf_metrics
        })

        return router_metrics

    def reset_metrics(self) -> None:
        """Reset performance metrics counters."""
        self.metrics = {
            'detections_total': 0,
            'detections_cached': 0,
            'conversions_total': 0,
            'detection_time_total': 0.0,
            'conversion_time_total': 0.0,
            'last_error': None
        }
        self.adf_generator.reset_metrics()
        logger.info("FormatRouter performance metrics reset")
