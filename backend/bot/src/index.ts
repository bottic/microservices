import { Bot } from 'grammy';
import dotenv from 'dotenv';
import { EventService } from './services/eventService';
import { BotHandlers } from './handlers/botHandlers';
import { RedisCache } from './core/redis';
import { LocalApi } from './api/localApi';
import { FavoritesService } from './services/favoritesService';
import Redis from 'ioredis';
import { logger } from './utils/logger';

dotenv.config();

const token = process.env.TELEGRAM_BOT_TOKEN;
// Если USE_MOCK_DATA=true или GATEWAY_URL не указан - используем моки
const useMockData = process.env.USE_MOCK_DATA === 'true' || !process.env.GATEWAY_URL;
const gatewayUrl = process.env.GATEWAY_URL || 'http://gateway:8000';
const redisUrl = process.env.REDIS_URL;
const cacheTtl = parseInt(process.env.CACHE_TTL_SECONDS || '1800', 10);
const localApiPort = parseInt(process.env.LOCAL_API_PORT || '3001', 10);
const enableLocalApi = process.env.ENABLE_LOCAL_API !== 'false'; // по умолчанию включен

if (!token) {
  logger.error('TELEGRAM_BOT_TOKEN is not set in environment variables');
  process.exit(1);
}

const debugMode = process.env.DEBUG === 'true';
logger.info(`Debug mode: ${debugMode ? 'ENABLED' : 'DISABLED'}`);

// Инициализируем Redis клиент для Local API и кэша
let redisClient: Redis | null = null;
if (redisUrl) {
  redisClient = new Redis(redisUrl, {
    maxRetriesPerRequest: 3,
    retryStrategy: () => null,
  });
  logger.info(`Redis client initialized: ${redisUrl}`);
}

// Инициализируем Local API (для добавления событий напрямую)
// Используем Redis для персистентности локальных событий
let localApi: LocalApi | null = null;
if (enableLocalApi) {
  localApi = new LocalApi(localApiPort, redisClient);
  localApi.start();
  logger.info(`Local API enabled on port ${localApiPort}${redisClient ? ' (with Redis persistence)' : ' (in-memory only)'}`);
}

// Инициализируем Redis кэш если URL указан и не используем моки
let cache: RedisCache | null = null;
if (redisUrl && !useMockData) {
  cache = new RedisCache(redisUrl, cacheTtl);
  logger.info(`Redis cache enabled: ${redisUrl} (TTL: ${cacheTtl}s)`);
}

logger.info(`Bot starting... Mode: ${useMockData ? 'MOCK DATA' : 'API'}`);

// Создаем бота с grammY
const bot = new Bot(token);

// Обработка ошибок
bot.catch((err: any) => {
  logger.error('Bot error:', err);
});

const eventService = new EventService(gatewayUrl, useMockData, cache, localApi);
const favoritesService = new FavoritesService(redisClient);
const botHandlers = new BotHandlers(bot, eventService, favoritesService);

// Регистрируем обработчики
botHandlers.registerHandlers();

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Shutting down...');
  await bot.stop();
  if (cache) {
    await cache.close();
  }
  if (redisClient) {
    await redisClient.quit();
  }
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('Shutting down...');
  await bot.stop();
  if (cache) {
    await cache.close();
  }
  if (redisClient) {
    await redisClient.quit();
  }
  process.exit(0);
});

// Запускаем бота
bot.start().then(() => {
  logger.info('Bot is running and ready to receive messages!');
}).catch((error: any) => {
  logger.error('Failed to start bot:', error);
  process.exit(1);
});
