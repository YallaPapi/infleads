"""
Base provider interface for lead data sources
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseProvider(ABC):
    """Abstract base class for lead data providers"""
    
    @abstractmethod
    def fetch_places(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch business leads based on query
        
        Args:
            query: Search query (e.g., "dentists in Miami")
            limit: Maximum number of results to fetch
            
        Returns:
            List of dictionaries containing lead data
        """
        pass
    
    def normalize_field(self, value: Any, default: str = 'NA') -> str:
        """Helper method to normalize field values"""
        if value is None or value == '' or (isinstance(value, float) and pd.isna(value)):
            return default
        return str(value)