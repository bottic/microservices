import Redis from 'ioredis';
import { Event } from '../types/event';
import { logger } from '../utils/logger';

export class RedisCache {
  private client: Redis;
  private ttlSeconds: number;

  constructor(redisUrl: string, ttlSeconds: number = 1800) {
    this.client = new Redis(redisUrl, {
      maxRetriesPerRequest: 3,
      retryStrategy: () => null, // не ретраить при ошибках
    });
    this.ttlSeconds = ttlSeconds;
  }

  async getEvents(type?: string): Promise<Event[] | null> {
    try {
      const key = this.getKey(type);
      const cached = await this.client.get(key);
      if (!cached) {
        return null;
      }
      return JSON.parse(cached) as Event[];
    } catch (error) {
      logger.error('Redis get error:', error);
      return null;
    }
  }

  async setEvents(events: Event[], type?: string): Promise<void> {
    try {
      const key = this.getKey(type);
      await this.client.setex(key, this.ttlSeconds, JSON.stringify(events));
      logger.debug(`Cached ${events.length} events with key: ${key}, TTL: ${this.ttlSeconds}s`);
    } catch (error) {
      logger.error('Redis set error:', error);
      // Игнорируем ошибки кэша, это не критично
    }
  }

  private getKey(type?: string): string {
    const prefix = 'bot:events-cache';
    return type ? `${prefix}:${type}` : `${prefix}:all`;
  }

  async close(): Promise<void> {
    await this.client.quit();
  }
}
