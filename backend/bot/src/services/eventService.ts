import axios, { AxiosInstance } from 'axios';
import { Event, EventType } from '../types/event';
import { MOCK_EVENTS } from '../data/mockEvents';
import { RedisCache } from '../core/redis';
import { LocalApi } from '../api/localApi';
import { logger } from '../utils/logger';

export class EventService {
  private client: AxiosInstance;
  private useMockData: boolean;
  private cache: RedisCache | null;
  private localApi: LocalApi | null;

  constructor(
    gatewayUrl: string, 
    useMockData: boolean = false,
    cache: RedisCache | null = null,
    localApi: LocalApi | null = null
  ) {
    this.useMockData = useMockData;
    this.cache = cache;
    this.localApi = localApi;
    this.client = axios.create({
      baseURL: gatewayUrl,
      timeout: 10000,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });
  }

  async getEvents(type?: EventType): Promise<Event[]> {
    // Если включен режим моковых данных, возвращаем их (без кэша)
    if (this.useMockData) {
      logger.debug(`Using mock data mode${type ? ` (type: ${type})` : ''}`);
      const mockEvents = this.filterMockEventsByType(MOCK_EVENTS, type);
      // Объединяем локальные события с моками
      if (this.localApi && this.localApi.getEventCount() > 0) {
        const localEvents = this.localApi.getLocalEvents(type);
        logger.debug(`Merging ${localEvents.length} local events with ${mockEvents.length} mock events`);
        return this.mergeEvents(localEvents, mockEvents);
      }
      return mockEvents;
    }

    // Пробуем получить из кэша
    if (this.cache) {
      const cached = await this.cache.getEvents(type);
      if (cached) {
        logger.debug(`Found ${cached.length} cached events${type ? ` (type: ${type})` : ''}`);
        // Объединяем с локальными событиями
        if (this.localApi && this.localApi.getEventCount() > 0) {
          const localEvents = this.localApi.getLocalEvents(type);
          return this.mergeEvents(localEvents, cached);
        }
        return cached;
      } else {
        logger.debug(`Cache miss${type ? ` (type: ${type})` : ''}`);
      }
    }

    // Запрашиваем из Gateway API
    try {
      const url = type 
        ? `/catalog/events/${type}`
        : '/catalog/events';
      
      const response = await this.client.get<Event[]>(url);
      const events = response.data;

      // Сохраняем в кэш
      if (this.cache) {
        await this.cache.setEvents(events, type);
      }

      logger.debug(`Fetched ${events.length} events from Gateway API${type ? ` (type: ${type})` : ''}`);

      // Объединяем с локальными событиями
      if (this.localApi && this.localApi.getEventCount() > 0) {
        const localEvents = this.localApi.getLocalEvents(type);
        const merged = this.mergeEvents(localEvents, events);
        logger.debug(`Merged ${localEvents.length} local events with ${events.length} API events`);
        return merged;
      }

      return events;
    } catch (error: unknown) {
      logger.error('Error fetching events from Gateway API, trying local API:', error);
      
      // При ошибке Gateway API пробуем локальные события
      if (this.localApi && this.localApi.getEventCount() > 0) {
        const localEvents = this.localApi.getLocalEvents(type);
        if (localEvents.length > 0) {
          logger.info(`Using ${localEvents.length} local events as fallback`);
          return localEvents;
        }
      }

      // Fallback на моковые данные только если useMockData=true
      if (this.useMockData) {
        logger.debug(`Using mock data as fallback${type ? ` (type: ${type})` : ''}`);
        return this.filterMockEventsByType(MOCK_EVENTS, type);
      }

      // Если useMockData=false и API недоступен, возвращаем пустой массив
      logger.warn(`Gateway API unavailable and mock data disabled. Returning empty array.`);
      return [];
    }
  }

  // Объединяет события, приоритет локальным (не дублируются по UUID, локальные идут первыми)
  private mergeEvents(localEvents: Event[], apiEvents: Event[]): Event[] {
    const localUuids = new Set(localEvents.map(e => e.uuid));
    const merged: Event[] = [];
    
    // Сначала добавляем локальные события
    merged.push(...localEvents);
    
    // Затем добавляем API события, которых нет в локальных
    apiEvents.forEach(event => {
      if (!localUuids.has(event.uuid)) {
        merged.push(event);
      }
    });
    
    return merged;
  }

  private filterMockEventsByType(events: Event[], type?: EventType): Event[] {
    if (!type) {
      return [...events];
    }
    return events.filter(event => event.event_type === type);
  }

  getUpcomingEvents(events: Event[]): Event[] {
    const now = new Date();
    return events
      .filter(event => {
        const previewDate = new Date(event.date_preview);
        return previewDate >= now;
      })
      .sort((a, b) => {
        const dateA = new Date(a.date_preview).getTime();
        const dateB = new Date(b.date_preview).getTime();
        return dateA - dateB;
      });
  }

  // Фильтрация по датам
  filterByDate(events: Event[], dateFilter: 'today' | 'tomorrow' | 'week' | 'month'): Event[] {
    const now = new Date();
    now.setHours(0, 0, 0, 0);

    return events.filter(event => {
      // Проверяем все даты из date_list, а не только date_preview
      // Если хотя бы одна дата попадает в фильтр - событие показываем
      const eventDates = event.date_list.length > 0 
        ? event.date_list 
        : [event.date_preview]; // fallback на date_preview если date_list пуст

      return eventDates.some(dateStr => {
        const eventDate = new Date(dateStr);
        eventDate.setHours(0, 0, 0, 0);

        switch (dateFilter) {
          case 'today':
            return eventDate.getTime() === now.getTime();
          
          case 'tomorrow':
            const tomorrow = new Date(now);
            tomorrow.setDate(tomorrow.getDate() + 1);
            return eventDate.getTime() === tomorrow.getTime();
          
          case 'week':
            const weekLater = new Date(now);
            weekLater.setDate(weekLater.getDate() + 7);
            return eventDate >= now && eventDate <= weekLater;
          
          case 'month':
            const monthLater = new Date(now);
            monthLater.setMonth(monthLater.getMonth() + 1);
            return eventDate >= now && eventDate <= monthLater;
          
          default:
            return true;
        }
      });
    });
  }

  // Фильтрация по цене
  filterByPrice(events: Event[], priceFilter: 'free' | 'cheap' | 'medium' | 'expensive' | 'luxury'): Event[] {
    return events.filter(event => {
      switch (priceFilter) {
        case 'free':
          return event.price === 0;
        case 'cheap':
          return event.price > 0 && event.price <= 500;
        case 'medium':
          return event.price > 500 && event.price <= 1500;
        case 'expensive':
          return event.price > 1500 && event.price <= 3000;
        case 'luxury':
          return event.price > 3000;
        default:
          return true;
      }
    });
  }
}
