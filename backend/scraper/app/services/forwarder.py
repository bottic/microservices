from typing import Any, Dict, List
from uuid import UUID

import httpx
from app.config import settings
from app.core.redis import mark_processed, was_processed
from app.schemas.event import ScrapedEvent


async def forward_events_to_catalog(events: List[ScrapedEvent]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"sent": 0, "skipped": 0, "failed": []}

    async with httpx.AsyncClient(
        base_url=settings.scraper_catalog_service_url,
        timeout=10.0,
    ) as client:
        for event in events:
            event_id: UUID = event.id
            if await was_processed(event_id):
                summary["skipped"] += 1
                continue

            try:
                resp = await client.post("/scraper/upload", json=event.to_catalog_payload())
                if resp.is_success:
                    await mark_processed(event_id)
                    summary["sent"] += 1
                else:
                    summary["failed"].append(
                        {
                            "uuid": str(event_id),
                            "status_code": resp.status_code,
                            "detail": resp.text,
                        }
                    )
            except httpx.RequestError as exc:
                summary["failed"].append(
                    {
                        "uuid": str(event_id),
                        "status_code": 0,
                        "detail": f"request failed: {exc}",
                    }
                )

    return summary
