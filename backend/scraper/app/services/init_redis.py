import logging
from typing import List
from uuid import UUID

import httpx

from app.config import settings
from app.core.redis import mark_processed_batch

logger = logging.getLogger(__name__)

async def _fetch_catalog_uuids() -> List[UUID]:
    async with httpx.AsyncClient(
        base_url=settings.scraper_catalog_service_url,
        timeout=10.0,
    ) as client:
        resp = await client.get("/scraperCatalog/events")
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError as exc:
            logger.warning("Bad JSON from scraperCatalog: %s", exc)
            return []
    uuids: List[UUID] = []
    for item in data:
        try:
            uuids.append(UUID(str(item["uuid"])))
        except (KeyError, ValueError):
            logger.warning("Skip invalid catalog item while bootstrapping: %s", item)
    return uuids

async def warmup_processed_from_catalog() -> int:
    try:
        uuids = await _fetch_catalog_uuids()
    except httpx.HTTPError as exc:
        logger.warning("Could not fetch catalog events: %s", exc)
        return 0
    if not uuids:
        return 0
    added = await mark_processed_batch(uuids)
    logger.info("Bootstrapped %d catalog events into processed set (new: %d)", len(uuids), added)
    return added
