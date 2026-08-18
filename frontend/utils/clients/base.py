"""
Base HTTP Client wrapper for frontend domain clients.
"""

import os
import httpx
from typing import Optional, Dict, Any

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class BaseHTTPClient:
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = httpx.get(f"{self.base_url}{endpoint}", params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP GET Error on {endpoint}: {e}")
            raise

    def _post(self, endpoint: str, json_data: Any = None, files: Any = None) -> Any:
        try:
            if files:
                response = httpx.post(f"{self.base_url}{endpoint}", files=files, timeout=30.0)
            else:
                response = httpx.post(f"{self.base_url}{endpoint}", json=json_data, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP POST Error on {endpoint}: {e}")
            raise

    def _put(self, endpoint: str, json_data: Any) -> Any:
        try:
            response = httpx.put(f"{self.base_url}{endpoint}", json=json_data, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP PUT Error on {endpoint}: {e}")
            raise

    def _delete(self, endpoint: str) -> None:
        try:
            response = httpx.delete(f"{self.base_url}{endpoint}", timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"HTTP DELETE Error on {endpoint}: {e}")
            raise
