"""
Заглушка для вашей бизнес-логики сбора событий.
Импортируйте сюда конкретные скраперы и верните список ScrapedEvent.
"""
from typing import List

from app.schemas.event import ScrapedEvent


async def run_scrape() -> List[ScrapedEvent]:
    # TODO: реализуйте сбор данных и верните список ScrapedEvent
    #
    # Пример:
    # raw_items = await my_scraper.collect()
    # return [ScrapedEvent.model_validate(item) for item in raw_items]
    return []
