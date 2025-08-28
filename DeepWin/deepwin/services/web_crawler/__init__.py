#!/usr/bin/env python3
"""
DeepWin Web Crawler Service Package

This package provides comprehensive web crawling capabilities for the DeepWin system,
including:

- UnsplashApiCrawler: Official Unsplash API integration for high-quality images
- BaiduCrawler: Baidu image search crawler with anti-detection strategies
- CrawlerManager: Centralized crawler orchestration and management

Features:
- Anti-bot detection evasion
- Intelligent retry mechanisms
- Configurable download limits and delays
- Multi-crawler support
- Batch processing capabilities
- Comprehensive logging and error handling

Usage:
    from deepwin.services.web_crawler import CrawlerManager
    
    # Create manager instance
    manager = CrawlerManager(log_manager, config_manager)
    
    # Download images
    result = manager.download_images('unsplash', 'nature', 1)
"""

from .unsplash_api_crawler import UnsplashApiCrawler
from .baidu_crawler import BaiduCrawler
from .crawler_manager import CrawlerManager

__version__ = "2.0.0"
__author__ = "DeepWin Team"
__description__ = "Web crawling service package for DeepWin system"

# Export main classes
__all__ = [
    'UnsplashApiCrawler',
    'BaiduCrawler', 
    'CrawlerManager'
]
