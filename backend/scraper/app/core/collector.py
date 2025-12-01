from typing import List

from app.schemas.event import ScrapedEvent


async def run_scrape() -> List[ScrapedEvent]:
    # TODO: реализуйте сбор данных и верните список ScrapedEvent
    #
    # Пример:
    # raw_items = await my_scraper.collect()
    # return [ScrapedEvent.model_validate(item) for item in raw_items]
    """
    Временная заглушка: возвращаем фиксированный список событий.
    """
    raw_items = [
        {
            "uuid": "33333333-3334-3333-3333-333333333333",
            "type": "stand_up",
            "title": "Test_stand_up",
            "description": "desc",
            "price": 500,
            "date_prewie": "2024-12-01T18:00:00",
            "date_list": ["2024-12-02T19:00:00"],
            "place": "Main stage",
            "genre": "rock",
            "age": "18+",
            "image_url": "https://avatars.mds.yandex.net/get-afishanew/29022/4c08d32f65e3ecc99501790ff879d16a/s760x440",
            "url": "https://example.com/event",
        },
        {
            "uuid": "33333333-3333-3333-3333-333333333333",
            "type": "concert",
            "title": "Test concert",
            "description": "desc",
            "price": 5555,
            "date_prewie": "2024-12-01T18:00:00",
            "date_list": ["2024-12-02T19:00:00", "2025-12-06T20:00:00"],
            "place": "Main stage",
            "genre": "rock",
            "age": "18+",
            "image_url": "https://avatars.mds.yandex.net/get-afishanew/4768735/e8b4ad522e6f10847a2ab8b117030246/s760x440",
            "url": "https://example.com/event",
        },
        {
            "uuid": "33332333-3333-3333-3333-333333333333",
            "type": "concert",
            "title": "Test concert",
            "description": "desc",
            "price": 1111,
            "date_prewie": "2024-12-01T18:00:00",
            "date_list": ["2024-12-02T19:00:00", "2025-12-06T20:00:00"],
            "place": "Лайв концерт холл",
            "genre": "rock",
            "age": "18+",
            "image_url": "https://avatars.mds.yandex.net/get-afishanew/4768735/e8b4ad522e6f10847a2ab8b117030246/s760x440",
            "url": "https://example.com/event",
        },
        {
            "uuid": "11332333-3333-3333-3333-333333333333",
            "type": "concert",
            "title": "Test concert",
            "description": "desc",
            "price": 1111,
            "date_prewie": "2024-12-01T18:00:00",
            "date_list": ["2024-12-02T19:00:00", "2025-12-06T20:00:00"],
            "place": "Лайв концерт холл",
            "genre": "rock",
            "age": "18+",
            "image_url": "https://avatars.mds.yandex.net/get-afishanew/4768735/e8b4ad522e6f10847a2ab8b117030246/s760x440",
            "url": "https://example.com/event",
        },
        {
            "uuid": "11111233-3333-3333-3333-333333333333",
            "type": "concert",
            "title": "Test Lore, ipsum dolor sit amet, consectetur adipiscing elit.",
            "description": "desc",
            "price": 1111,
            "date_prewie": "2026-12-01T18:00:00",
            "date_list": ["2024-12-02T19:00:00", "2025-12-06T20:00:00", "2025-12-06T20:00:00", "2025-12-06T20:00:00"],
            "place": "Лайв концерт холл",
            "genre": "rock",
            "age": "18+",
            "image_url": "https://avatars.mds.yandex.net/get-afishanew/4768735/e8b4ad522e6f10847a2ab8b117030246/s760x440",
            "url": "https://example.com/event",
        },
        {
            "uuid": "11111234-1333-3333-3333-333333333333",
            "type": "concert",
            "title": "lorem ipsum dolor sit amet  consectetur adipiscing elit",
            "description": "desc",
            "price": 1111,
            "date_prewie": "2026-12-01T18:00:00",
            "date_list": ["2024-12-02T19:00:00", "2025-12-06T20:00:00", "2025-12-06T20:00:00", "2025-12-06T20:00:00"],
            "place": "Лайв концерт холл",
            "genre": "rock",
            "age": "18+",
            "image_url": "https://avatars.mds.yandex.net/get-afishanew/4768735/e8b4ad522e6f10847a2ab8b117030246/s760x440",
            "url": "https://example.com/event",
        },
    ]

    return [ScrapedEvent.model_validate(item) for item in raw_items]