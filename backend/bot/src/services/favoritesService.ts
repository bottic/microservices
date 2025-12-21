import Redis from 'ioredis';
import { Event } from '../types/event';
import { logger } from '../utils/logger';

export class FavoritesService {
  private client: Redis | null;

  constructor(redisClient: Redis | null) {
    this.client = redisClient;
  }

  private getKey(userId: number): string {
    return `bot:favorites:${userId}`;
  }

  async addFavorite(userId: number, event: Event): Promise<boolean> {
    if (!this.client) {
      logger.warn('Redis not available, favorites feature disabled');
      return false;
    }

    try {
      const key = this.getKey(userId);
      const favorites = await this.getFavorites(userId);
      
      // Проверяем, нет ли уже этого события в избранном
      if (favorites.some(fav => fav.uuid === event.uuid)) {
        return false; // Уже в избранном
      }

      favorites.push(event);
      await this.client.set(key, JSON.stringify(favorites));
      logger.debug(`Added event ${event.uuid} to favorites for user ${userId}`);
      return true;
    } catch (error) {
      logger.error('Error adding favorite:', error);
      return false;
    }
  }

  async removeFavorite(userId: number, eventUuid: string): Promise<boolean> {
    if (!this.client) {
      logger.warn('Redis not available, favorites feature disabled');
      return false;
    }

    try {
      const key = this.getKey(userId);
      const favorites = await this.getFavorites(userId);
      
      const filtered = favorites.filter(fav => fav.uuid !== eventUuid);
      
      if (filtered.length === favorites.length) {
        return false; // Событие не было в избранном
      }

      await this.client.set(key, JSON.stringify(filtered));
      logger.debug(`Removed event ${eventUuid} from favorites for user ${userId}`);
      return true;
    } catch (error) {
      logger.error('Error removing favorite:', error);
      return false;
    }
  }

  async getFavorites(userId: number): Promise<Event[]> {
    if (!this.client) {
      return [];
    }

    try {
      const key = this.getKey(userId);
      const data = await this.client.get(key);
      if (!data) {
        return [];
      }
      return JSON.parse(data) as Event[];
    } catch (error) {
      logger.error('Error getting favorites:', error);
      return [];
    }
  }

  async isFavorite(userId: number, eventUuid: string): Promise<boolean> {
    if (!this.client) {
      return false;
    }

    const favorites = await this.getFavorites(userId);
    return favorites.some(fav => fav.uuid === eventUuid);
  }
}

