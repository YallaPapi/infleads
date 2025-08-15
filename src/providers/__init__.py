"""
Lead data providers for R27 Infinite AI Leads Agent
"""

from .base import BaseProvider
from .apify_provider import ApifyProvider

def get_provider(provider_name: str) -> BaseProvider:
    """Factory function to get the appropriate provider"""
    providers = {
        'apify': ApifyProvider,
        # Add more providers here as needed
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return providers[provider_name]()