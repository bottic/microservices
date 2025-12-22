import express, { Express, Request, Response } from 'express';
import { Event } from '../types/event';
import Redis from 'ioredis';
import { logger } from '../utils/logger';

export class LocalApi {
  private app: Express;
  private localEvents: Map<string, Event> = new Map(); // uuid -> Event (кэш в памяти)
  private port: number;
  private redis: Redis | null;
  private readonly redisKey = 'bot:local-events';

  constructor(port: number = 3001, redisClient: Redis | null = null) {
    this.port = port;
    this.redis = redisClient;
    this.app = express();
    this.app.use(express.json());
    this.setupRoutes();
    // Загружаем события из Redis при старте
    this.loadEventsFromRedis();
  }

  // Загрузить события из Redis в память
  private async loadEventsFromRedis(): Promise<void> {
    if (!this.redis) {
      console.log('Redis not available, using in-memory storage only');
      return;
    }

    try {
      const data = await this.redis.get(this.redisKey);
      if (data) {
        const events: Event[] = JSON.parse(data);
        events.forEach(event => {
          this.localEvents.set(event.uuid, event);
        });
        logger.info(`Loaded ${events.length} local events from Redis`);
      }
    } catch (error) {
      logger.error('Error loading events from Redis:', error);
    }
  }

  // Сохранить события в Redis
  private async saveEventsToRedis(): Promise<void> {
    if (!this.redis) {
      return;
    }

    try {
      const events = Array.from(this.localEvents.values());
      await this.redis.set(this.redisKey, JSON.stringify(events));
      logger.debug(`Saved ${events.length} local events to Redis`);
    } catch (error) {
      logger.error('Error saving events to Redis:', error);
      // Игнорируем ошибки Redis, работаем дальше с памятью
    }
  }

  private setupRoutes(): void {
    // Health check
    this.app.get('/health', (req: Request, res: Response) => {
      res.json({ status: 'ok', service: 'bot-local-api' });
    });

    // Получить все локальные события
    this.app.get('/events', (req: Request, res: Response) => {
      const events = Array.from(this.localEvents.values());
      res.json(events);
    });

    // Получить события по типу
    this.app.get('/events/:type', (req: Request, res: Response) => {
      const type = req.params.type;
      const events = Array.from(this.localEvents.values())
        .filter(event => event.event_type === type);
      res.json(events);
    });

    // Получить событие по UUID
    this.app.get('/events/uuid/:uuid', (req: Request, res: Response) => {
      const uuid = req.params.uuid;
      const event = this.localEvents.get(uuid);
      if (!event) {
        return res.status(404).json({ error: 'Event not found' });
      }
      res.json(event);
    });

    // Добавить событие
    this.app.post('/events', async (req: Request, res: Response) => {
      try {
        const eventData = req.body as Event;
        
        // Валидация обязательных полей
        if (!eventData.uuid || !eventData.title || !eventData.event_type) {
          return res.status(400).json({ 
            error: 'Missing required fields: uuid, title, event_type' 
          });
        }

        // Проверяем, не существует ли уже событие с таким UUID
        if (this.localEvents.has(eventData.uuid)) {
          return res.status(409).json({ 
            error: 'Event with this UUID already exists',
            uuid: eventData.uuid 
          });
        }

        // Устанавливаем created_at если не указан
        if (!eventData.created_at) {
          eventData.created_at = new Date().toISOString();
        }

        // Сохраняем событие
        this.localEvents.set(eventData.uuid, eventData);
        await this.saveEventsToRedis();

        res.status(201).json({ 
          message: 'Event added successfully',
          uuid: eventData.uuid,
          event: eventData 
      });
    } catch (error) {
      logger.error('Error adding event:', error);
      res.status(500).json({ error: 'Internal server error' });
      }
    });

    // Обновить событие
    this.app.put('/events/:uuid', async (req: Request, res: Response) => {
      try {
        const uuid = req.params.uuid;
        const event = this.localEvents.get(uuid);
        
        if (!event) {
          return res.status(404).json({ error: 'Event not found' });
        }

        const updatedData = req.body as Partial<Event>;
        const updatedEvent = { ...event, ...updatedData, uuid }; // uuid не меняем
        this.localEvents.set(uuid, updatedEvent as Event);
        await this.saveEventsToRedis();

        res.json({ 
          message: 'Event updated successfully',
          event: updatedEvent 
        });
      } catch (error) {
        console.error('Error updating event:', error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    // Удалить событие
    this.app.delete('/events/:uuid', async (req: Request, res: Response) => {
      const uuid = req.params.uuid;
      const deleted = this.localEvents.delete(uuid);
      
      if (!deleted) {
        return res.status(404).json({ error: 'Event not found' });
      }

      await this.saveEventsToRedis();
      res.json({ message: 'Event deleted successfully', uuid });
    });

    // Добавить несколько событий (batch)
    this.app.post('/events/batch', async (req: Request, res: Response) => {
      try {
        const { events } = req.body as { events: Event[] };
        
        if (!Array.isArray(events)) {
          return res.status(400).json({ error: 'events must be an array' });
        }

        const results = {
          created: [] as string[],
          skipped: [] as Array<{ uuid: string; reason: string }>,
          failed: [] as Array<{ uuid?: string; error: string }>,
        };

        for (const eventData of events) {
          try {
            if (!eventData.uuid || !eventData.title || !eventData.event_type) {
              results.failed.push({ 
                uuid: eventData.uuid, 
                error: 'Missing required fields' 
              });
              continue;
            }

            if (this.localEvents.has(eventData.uuid)) {
              results.skipped.push({ 
                uuid: eventData.uuid, 
                reason: 'already_exists' 
              });
              continue;
            }

            if (!eventData.created_at) {
              eventData.created_at = new Date().toISOString();
            }

            this.localEvents.set(eventData.uuid, eventData);
            results.created.push(eventData.uuid);
          } catch (error) {
            results.failed.push({ 
              uuid: eventData.uuid, 
              error: String(error) 
            });
          }
        }

        // Сохраняем все изменения в Redis
        await this.saveEventsToRedis();

        res.status(201).json(results);
        logger.debug(`Batch added: ${results.created.length} created, ${results.skipped.length} skipped, ${results.failed.length} failed`);
      } catch (error) {
        logger.error('Error adding events batch:', error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    // Получить статистику
    this.app.get('/stats', (req: Request, res: Response) => {
      const events = Array.from(this.localEvents.values());
      const stats = {
        total: events.length,
        by_type: {} as Record<string, number>,
      };

      events.forEach(event => {
        stats.by_type[event.event_type] = (stats.by_type[event.event_type] || 0) + 1;
      });

      res.json(stats);
    });
  }

  // Получить все локальные события
  getLocalEvents(type?: string): Event[] {
    const events = Array.from(this.localEvents.values());
    if (type) {
      return events.filter(event => event.event_type === type);
    }
    return events;
  }

  // Добавить событие программно
  async addEvent(event: Event): Promise<boolean> {
    if (this.localEvents.has(event.uuid)) {
      return false;
    }
    this.localEvents.set(event.uuid, event);
    await this.saveEventsToRedis();
    return true;
  }

  // Запустить сервер
  start(): void {
    this.app.listen(this.port, () => {
      logger.info(`Local API server started on port ${this.port}`);
      logger.info(`  GET  http://localhost:${this.port}/health`);
      logger.info(`  GET  http://localhost:${this.port}/events`);
      logger.info(`  POST http://localhost:${this.port}/events`);
      logger.info(`  POST http://localhost:${this.port}/events/batch`);
    });
  }

  // Получить количество локальных событий
  getEventCount(): number {
    return this.localEvents.size;
  }
}
