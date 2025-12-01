from typing import Any, Dict, List
from uuid import UUID

import httpx
from app.config import settings
from app.core.redis import mark_processed, was_processed
from app.schemas.event import ScrapedEvent

def _chunked(seq, size):
    for i in range(0, len(seq), size):  # шаг size, не 1
        yield seq[i : i + size]

async def forward_events_to_catalog(events: List[ScrapedEvent]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"sent": 0, "skipped": 0, "failed": []}
    batch_size = settings.batch_size
    async with httpx.AsyncClient(
        base_url=settings.scraper_catalog_service_url,
        timeout=10.0,
    ) as client:
        for chunk in _chunked(events, batch_size):
            payload = []
            for event in chunk:
                event_id: UUID = event.uuid
                if await was_processed(event_id):
                    summary["skipped"] += 1
                    continue
                payload.append(event.to_catalog_payload())
            
            if not payload:
                continue

            try:
                resp = await client.post("/scraperCatalog/upload/batch", json={"events": payload})
            except httpx.RequestError as exc:
                summary["failed"].append(
                    {
                        "uuids": [str(item["uuid"]) for item in payload],
                        "status_code": 502,
                        "detail": f"scraperCatalog unavailable: {exc}",
                    }
                )
                continue

            if resp.is_success:
                try:
                    request_body = resp.json()
                except ValueError:
                    for item in payload:
                        summary["failed"].append(
                            {"uuid": str(item["uuid"]), "status_code": resp.status_code, "detail": "bad json"}
                        )
                    continue
                request_body = resp.json()
                created = request_body.get("created", [])
                skipped = request_body.get("skipped", [])
                failed = request_body.get("failed", [])
                for item in created:
                    event_id: UUID = UUID(item["uuid"])
                    await mark_processed(event_id)
                    summary["sent"] += 1
                for item in skipped:
                    if item.get("reason") == "already_exists":
                        await mark_processed(UUID(item["uuid"]))
                        summary["skipped"] += 1
                summary["failed"].extend(failed)
            else:
                detail = resp.text
                status_code = resp.status_code
                for item in payload:
                    summary["failed"].append(
                        {"uuid": str(item["uuid"]), "status_code": status_code, "detail": detail}
                    )
           
    return summary
