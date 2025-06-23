from typing import Generic, TypeVar, List, Optional, Dict, Any
from pydantic import BaseModel, create_model

T = TypeVar('T', bound=BaseModel)

class BaseResponse(Generic[T]):
    """Base response class for single item API responses."""
    
    def __init__(self, data: Dict[str, Any], model_class: type[T]):
        self.data = model_class(**data)
        self.raw_data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return self.data.model_dump()


class ListResponse(Generic[T]):
    """Response class for list-type API responses."""
    
    def __init__(self, data: List[Dict[str, Any]], model_class: type[T]):
        self.data = [model_class(**item) for item in data]
        self.raw_data = data
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert response to list of dictionaries."""
        return [item.model_dump() for item in self.data]


class PaginatedListResponse(ListResponse[T]):
    """Response class for paginated list-type API responses."""
    
    def __init__(self, data: List[Dict[str, Any]], model_class: type[T], 
                 cursor: Optional[int] = None, next_cursor: Optional[int] = None):
        super().__init__(data, model_class)
        self.cursor = cursor
        self.next_cursor = next_cursor
        self.has_more = next_cursor is not None


class BaseAPI(Generic[T]):
    """Base API class with common functionality."""
    
    def __init__(self, client):
        self.client = client
        self.model_class = None
    
    def _get_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> BaseResponse[T]:
        """Get single item data from API."""
        if params is None:
            params = {}
        data = self.client.get(endpoint, params)
        return BaseResponse(data, self.model_class)
    
    def _get_list(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> ListResponse[T]:
        """Get list data from API."""
        if params is None:
            params = {}
        data = self.client.get(endpoint, params)
        return ListResponse(data, self.model_class)
    
    def _get_paginated_list(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> PaginatedListResponse[T]:
        """Get paginated list data from API."""
        if params is None:
            params = {}
        # Filter out None values to avoid passing them as query params
        params = {k: v for k, v in params.items() if v is not None}
        response = self.client.get(endpoint, params)
        
        if isinstance(response, dict) and "data" in response:
            # Handle API response format with metadata
            data = response.get("data", [])
            cursor = response.get("cursor")
            next_cursor = response.get("next_cursor")
        else:
            # Handle direct list response
            data = response
            cursor = params.get("cursor")
            next_cursor = None  # Needs actual implementation based on API
            
        return PaginatedListResponse(data, self.model_class, cursor, next_cursor)