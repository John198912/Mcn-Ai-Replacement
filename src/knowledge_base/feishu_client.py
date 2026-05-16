"""Feishu (Lark) API client for knowledge base integration."""

import time
from typing import Any, Dict, List, Optional

import httpx

from ..core.logger import get_logger
from ..core.exceptions import MCNAIException

logger = get_logger(__name__)


class FeishuAPIError(MCNAIException):
    """Feishu API error."""
    pass


class FeishuClient:
    """Feishu (Lark) API client for multi-dimensional tables."""

    def __init__(self, app_id: str, app_secret: str):
        """Initialize Feishu client.

        Args:
            app_id: Feishu app ID
            app_secret: Feishu app secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        self.token_expires_at = 0
        self.logger = logger.bind(component="FeishuClient")

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """Get access token (with caching).

        Args:
            force_refresh: Force refresh token even if not expired

        Returns:
            Access token

        Raises:
            FeishuAPIError: If token request fails
        """
        # Check if token is still valid
        if not force_refresh and self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        self.logger.info("Requesting new access token")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/v3/tenant_access_token/internal",
                    json={"app_id": self.app_id, "app_secret": self.app_secret},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    raise FeishuAPIError(
                        f"Failed to get access token: HTTP {response.status_code}"
                    )

                data = response.json()

                if data.get("code") != 0:
                    raise FeishuAPIError(
                        f"Failed to get access token: {data.get('msg', 'Unknown error')}"
                    )

                self.access_token = data["tenant_access_token"]
                # Token expires in 2 hours, refresh 5 minutes before
                self.token_expires_at = time.time() + data.get("expire", 7200) - 300

                self.logger.info("Access token obtained successfully")
                return self.access_token

        except httpx.HTTPError as e:
            raise FeishuAPIError(f"HTTP error while getting access token: {e}")
        except Exception as e:
            raise FeishuAPIError(f"Unexpected error while getting access token: {e}")

    async def add_records(
        self, app_token: str, table_id: str, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add records to a multi-dimensional table.

        Args:
            app_token: App token (bitable ID)
            table_id: Table ID
            records: List of records to add

        Returns:
            API response

        Raises:
            FeishuAPIError: If request fails
        """
        if not records:
            return {"code": 0, "msg": "success", "data": {"records": []}}

        token = await self.get_access_token()

        self.logger.info(
            "Adding records to table", table_id=table_id, count=len(records)
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={"records": [{"fields": r} for r in records]},
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise FeishuAPIError(
                        f"Failed to add records: HTTP {response.status_code}"
                    )

                data = response.json()

                if data.get("code") != 0:
                    raise FeishuAPIError(
                        f"Failed to add records: {data.get('msg', 'Unknown error')}"
                    )

                self.logger.info("Records added successfully", count=len(records))
                return data

        except httpx.HTTPError as e:
            raise FeishuAPIError(f"HTTP error while adding records: {e}")
        except Exception as e:
            raise FeishuAPIError(f"Unexpected error while adding records: {e}")

    async def query_records(
        self,
        app_token: str,
        table_id: str,
        filter_expr: Optional[str] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query records from a multi-dimensional table.

        Args:
            app_token: App token (bitable ID)
            table_id: Table ID
            filter_expr: Optional filter expression
            page_size: Page size (max 500)

        Returns:
            List of records

        Raises:
            FeishuAPIError: If request fails
        """
        token = await self.get_access_token()

        self.logger.info("Querying records from table", table_id=table_id)

        all_records = []
        page_token = None

        try:
            async with httpx.AsyncClient() as client:
                while True:
                    params = {"page_size": min(page_size, 500)}
                    if filter_expr:
                        params["filter"] = filter_expr
                    if page_token:
                        params["page_token"] = page_token

                    response = await client.get(
                        f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                        headers={"Authorization": f"Bearer {token}"},
                        params=params,
                        timeout=60.0,
                    )

                    if response.status_code != 200:
                        raise FeishuAPIError(
                            f"Failed to query records: HTTP {response.status_code}"
                        )

                    data = response.json()

                    if data.get("code") != 0:
                        raise FeishuAPIError(
                            f"Failed to query records: {data.get('msg', 'Unknown error')}"
                        )

                    items = data.get("data", {}).get("items", [])
                    all_records.extend(items)

                    # Check if there are more pages
                    page_token = data.get("data", {}).get("page_token")
                    if not page_token or not data.get("data", {}).get("has_more"):
                        break

                self.logger.info(
                    "Records queried successfully", count=len(all_records)
                )
                return all_records

        except httpx.HTTPError as e:
            raise FeishuAPIError(f"HTTP error while querying records: {e}")
        except Exception as e:
            raise FeishuAPIError(f"Unexpected error while querying records: {e}")

    async def update_record(
        self, app_token: str, table_id: str, record_id: str, fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a record in a multi-dimensional table.

        Args:
            app_token: App token (bitable ID)
            table_id: Table ID
            record_id: Record ID
            fields: Fields to update

        Returns:
            API response

        Raises:
            FeishuAPIError: If request fails
        """
        token = await self.get_access_token()

        self.logger.info("Updating record", table_id=table_id, record_id=record_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={"fields": fields},
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise FeishuAPIError(
                        f"Failed to update record: HTTP {response.status_code}"
                    )

                data = response.json()

                if data.get("code") != 0:
                    raise FeishuAPIError(
                        f"Failed to update record: {data.get('msg', 'Unknown error')}"
                    )

                self.logger.info("Record updated successfully")
                return data

        except httpx.HTTPError as e:
            raise FeishuAPIError(f"HTTP error while updating record: {e}")
        except Exception as e:
            raise FeishuAPIError(f"Unexpected error while updating record: {e}")

    async def delete_record(
        self, app_token: str, table_id: str, record_id: str
    ) -> Dict[str, Any]:
        """Delete a record from a multi-dimensional table.

        Args:
            app_token: App token (bitable ID)
            table_id: Table ID
            record_id: Record ID

        Returns:
            API response

        Raises:
            FeishuAPIError: If request fails
        """
        token = await self.get_access_token()

        self.logger.info("Deleting record", table_id=table_id, record_id=record_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise FeishuAPIError(
                        f"Failed to delete record: HTTP {response.status_code}"
                    )

                data = response.json()

                if data.get("code") != 0:
                    raise FeishuAPIError(
                        f"Failed to delete record: {data.get('msg', 'Unknown error')}"
                    )

                self.logger.info("Record deleted successfully")
                return data

        except httpx.HTTPError as e:
            raise FeishuAPIError(f"HTTP error while deleting record: {e}")
        except Exception as e:
            raise FeishuAPIError(f"Unexpected error while deleting record: {e}")
