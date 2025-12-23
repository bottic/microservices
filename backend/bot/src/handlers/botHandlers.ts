import { Bot, Context, InlineKeyboard } from 'grammy';
import { EventService } from '../services/eventService';
import { FavoritesService } from '../services/favoritesService';
import { EVENT_TYPES, EVENT_TYPE_LABELS, EventType } from '../types/event';
import { Event } from '../types/event';
import { formatEventMessage, formatEventsList } from '../utils/formatters';
import { logger } from '../utils/logger';

interface EventsFilterState {
  dateFilter?: 'today' | 'tomorrow' | 'week' | 'month';
  priceFilter?: 'free' | 'cheap' | 'medium' | 'expensive' | 'luxury';
  eventType?: EventType;
}

export class BotHandlers {
  // Храним состояние фильтров для каждого пользователя
  private userFilters: Map<number, EventsFilterState> = new Map();
  // Храним состояние пагинации для каждого пользователя (индекс последней показанной страницы)
  private userPagination: Map<number, number> = new Map();
  private readonly EVENTS_PER_PAGE = 10;

  constructor(
    private bot: Bot,
    private eventService: EventService,
    private favoritesService: FavoritesService
  ) {}

  registerHandlers(): void {
    // Команда /start
    this.bot.command('start', async (ctx: Context) => {
      if (!ctx.chat) return;
      const chatId = ctx.chat.id;
      logger.debug(`/start command from chat ${chatId}`);
      await this.sendWelcomeMessage(ctx);
    });

    // Команда /help
    this.bot.command('help', async (ctx: Context) => {
      if (!ctx.chat) return;
      const chatId = ctx.chat.id;
      logger.debug(`/help command from chat ${chatId}`);
      await this.sendHelpMessage(ctx);
    });

    // Команда /events - показать все ближайшие события
    this.bot.command('events', async (ctx: Context) => {
      if (!ctx.chat) return;
      const chatId = ctx.chat.id;
      logger.debug(`/events command from chat ${chatId}`);
      await this.showEvents(ctx);
    });

    // Команда /types - показать кнопки с типами событий
    this.bot.command('types', async (ctx: Context) => {
      if (!ctx.chat) return;
      const chatId = ctx.chat.id;
      logger.debug(`/types command from chat ${chatId}`);
      await this.showEventTypes(ctx);
    });

    // Обработка callback_query для кнопок выбора типа
    this.bot.callbackQuery('show_all_events', async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery) return;
      const chatId = ctx.chat.id;
      logger.debug(`Showing all events for chat ${chatId}`);
      await ctx.answerCallbackQuery({ text: 'Загрузка...' });
      // Очищаем фильтр по типу события при показе всех событий
      const filters = this.userFilters.get(chatId);
      if (filters) {
        delete filters.eventType;
        if (Object.keys(filters).length === 0) {
          this.userFilters.delete(chatId);
        } else {
          this.userFilters.set(chatId, filters);
        }
      }
      await this.showEvents(ctx, ctx.callbackQuery.message?.message_id);
    });

    this.bot.callbackQuery('show_types', async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery) return;
      const chatId = ctx.chat.id;
      logger.debug(`Showing event types for chat ${chatId}`);
      await ctx.answerCallbackQuery();
      await this.showEventTypes(ctx, ctx.callbackQuery.message?.message_id);
    });

    // Обработка callback_query для кнопки "Назад"
    this.bot.callbackQuery('back_to_menu', async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery) return;
      const chatId = ctx.chat.id;
      logger.debug(`Back to menu from chat ${chatId}`);
      await ctx.answerCallbackQuery();
      await this.showMainMenu(ctx, ctx.callbackQuery.message?.message_id);
    });

    // Показ меню фильтров
    this.bot.callbackQuery('show_filters', async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery) return;
      await ctx.answerCallbackQuery();
      await this.showFiltersMenu(ctx, ctx.callbackQuery.message?.message_id);
    });

    // Показ избранного
    this.bot.callbackQuery('show_favorites', async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery) return;
      await ctx.answerCallbackQuery();
      await this.showFavorites(ctx);
    });

    // Обработка callback_query для типов событий
    for (const eventType of EVENT_TYPES) {
      this.bot.callbackQuery(`event_type_${eventType}`, async (ctx: Context) => {
        if (!ctx.chat || !ctx.callbackQuery) return;
        const chatId = ctx.chat.id;
        logger.debug(`Showing events by type: ${eventType} for chat ${chatId}`);
        await ctx.answerCallbackQuery({ text: 'Загрузка...' });
        // Устанавливаем фильтр по типу и показываем события
        this.setUserEventType(ctx.chat.id, eventType);
        await this.showEvents(ctx, ctx.callbackQuery.message?.message_id);
      });
    }

    // Обработка фильтров по датам
    this.bot.callbackQuery(/^filter_date_(today|tomorrow|week|month)$/, async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery || !ctx.callbackQuery.data) return;
      const match = ctx.callbackQuery.data.match(/^filter_date_(today|tomorrow|week|month)$/);
      if (match) {
        const dateFilter = match[1] as 'today' | 'tomorrow' | 'week' | 'month';
        await ctx.answerCallbackQuery({ text: `Фильтр: ${this.getDateFilterLabel(dateFilter)}` });
        this.setUserDateFilter(ctx.chat.id, dateFilter);
        // Показываем события после применения фильтра
        await this.showEvents(ctx);
      }
    });

    // Обработка фильтров по цене
    this.bot.callbackQuery(/^filter_price_(free|cheap|medium|expensive|luxury)$/, async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery || !ctx.callbackQuery.data) return;
      const match = ctx.callbackQuery.data.match(/^filter_price_(free|cheap|medium|expensive|luxury)$/);
      if (match) {
        const priceFilter = match[1] as 'free' | 'cheap' | 'medium' | 'expensive' | 'luxury';
        await ctx.answerCallbackQuery({ text: `Фильтр: ${this.getPriceFilterLabel(priceFilter)}` });
        this.setUserPriceFilter(ctx.chat.id, priceFilter);
        // Показываем события после применения фильтра
        await this.showEvents(ctx);
      }
    });

    // Сброс фильтров
    this.bot.callbackQuery('filter_reset', async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery) return;
      await ctx.answerCallbackQuery({ text: 'Фильтры сброшены' });
      this.clearUserFilters(ctx.chat.id);
      // Если сообщение было в меню фильтров, возвращаемся к событиям
      // Иначе просто обновляем список событий
      await this.showEvents(ctx, ctx.callbackQuery.message?.message_id);
    });

    // Обработка пагинации
    this.bot.callbackQuery(/^page_(next|prev|info)$/, async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery || !ctx.callbackQuery.data) return;
      const match = ctx.callbackQuery.data.match(/^page_(next|prev|info)$/);
      if (match) {
        const action = match[1];
        if (action === 'info') {
          // Информационная кнопка, просто отвечаем
          await ctx.answerCallbackQuery();
          return;
        }
        const currentPage = this.userPagination.get(ctx.chat.id) || 0;
        if (action === 'next') {
          this.userPagination.set(ctx.chat.id, currentPage + 1);
        } else {
          this.userPagination.set(ctx.chat.id, Math.max(0, currentPage - 1));
        }
        await ctx.answerCallbackQuery();
        await this.showEvents(ctx, ctx.callbackQuery.message?.message_id, true);
      }
    });

    // Добавление/удаление из избранного
    this.bot.callbackQuery(/^favorite_(add|remove)_(.+)$/, async (ctx: Context) => {
      if (!ctx.chat || !ctx.callbackQuery || !ctx.callbackQuery.data) return;
      const match = ctx.callbackQuery.data.match(/^favorite_(add|remove)_(.+)$/);
      if (match) {
        const action = match[1] as 'add' | 'remove';
        const eventUuid = match[2];
        await this.handleFavoriteAction(ctx, eventUuid, action);
      }
    });

    // Обработка неизвестных callback_query (должна быть последней)
    this.bot.on('callback_query', async (ctx: Context) => {
      if (!ctx.callbackQuery || !ctx.chat) return;
      logger.warn(`Unknown callback_query: ${ctx.callbackQuery.data} from chat ${ctx.chat.id}`);
      await ctx.answerCallbackQuery({ text: 'Неизвестная команда', show_alert: false });
    });
  }

  private async sendWelcomeMessage(ctx: Context): Promise<void> {
    if (!ctx.chat) return;
    await this.showMainMenu(ctx);
  }

  private async showMainMenu(ctx: Context, messageId?: number): Promise<void> {
    if (!ctx.chat) return;
    const text = `👋 Привет! Я бот для уведомлений о событиях.

Я могу показать тебе ближайшие мероприятия: концерты, выставки, театральные постановки и многое другое!

Используй команды:
/events - показать все ближайшие события
/types - выбрать тип события
/help - помощь`;

    const keyboard = new InlineKeyboard()
      .text('📅 Все события', 'show_all_events').row()
      .text('🔍 Выбрать тип', 'show_types').row()
      .text('⭐ Избранное', 'show_favorites').row()
      .text('⚙️ Фильтры', 'show_filters');

    // Проверяем, можно ли редактировать сообщение
    // Если это фото-сообщение, то нельзя редактировать через editMessageText
    const isPhotoMessage = ctx.callbackQuery?.message && 'photo' in ctx.callbackQuery.message;
    
    if (messageId && !isPhotoMessage) {
      try {
        await ctx.api.editMessageText(ctx.chat.id, messageId, text, {
          reply_markup: keyboard,
        });
        return;
      } catch (error: any) {
        // Если ошибка о том, что нет текста для редактирования, просто отправляем новое сообщение
        const errorMessage = error.message || '';
        if (errorMessage.includes('no text in the message') || 
            errorMessage.includes('message can\'t be edited') ||
            errorMessage.includes('message to edit not found')) {
          logger.debug('Cannot edit message, sending new one');
        } else {
          logger.warn('Error editing message, sending new one:', errorMessage);
        }
      }
    }
    
    // Отправляем новое сообщение, если не удалось отредактировать или это фото-сообщение
    await ctx.reply(text, { reply_markup: keyboard });
  }

  private async sendHelpMessage(ctx: Context): Promise<void> {
    if (!ctx.chat) return;
    const text = `📖 Справка по командам:

/start - начать работу с ботом
/events - показать все ближайшие события
/types - выбрать тип события из списка
/favorites - показать избранные события
/help - показать эту справку

Ты также можешь использовать кнопки для быстрого доступа к функциям бота.`;

    const keyboard = new InlineKeyboard()
      .text('⬅️ Назад', 'back_to_menu');

    await ctx.reply(text, { reply_markup: keyboard });
  }

  private async showEventTypes(ctx: Context, messageId?: number): Promise<void> {
    if (!ctx.chat) return;
    const keyboard = new InlineKeyboard();
    
    // Добавляем кнопки для каждого типа события
    for (const type of EVENT_TYPES) {
      keyboard.text(EVENT_TYPE_LABELS[type], `event_type_${type}`).row();
    }
    
    // Добавляем кнопку "Все события" и "Назад"
    keyboard.text('📅 Все события', 'show_all_events').row()
      .text('⬅️ Назад', 'back_to_menu');

    const text = 'Выбери тип события:';

    if (messageId) {
      try {
        await ctx.api.editMessageText(ctx.chat.id, messageId, text, {
          reply_markup: keyboard,
        });
      } catch (error: any) {
        logger.warn('Error editing message, sending new one:', error.message);
        await ctx.reply(text, { reply_markup: keyboard });
      }
    } else {
      await ctx.reply(text, { reply_markup: keyboard });
    }
  }

  private async showEvents(ctx: Context, messageId?: number, keepPagination: boolean = false): Promise<void> {
    if (!ctx.chat) return;
    let loadingMessageId: number | undefined;
    
    try {
      logger.debug(`showEvents called for chat ${ctx.chat.id}, messageId: ${messageId}`);
      
      // Сбрасываем пагинацию, если не указано иное
      if (!keepPagination) {
        this.userPagination.set(ctx.chat.id, 0);
      }
      
      if (!messageId) {
        logger.debug(`No messageId, sending loading message to chat ${ctx.chat.id}`);
        const loadingMsg = await ctx.reply('⏳ Загружаю события...');
        loadingMessageId = loadingMsg.message_id;
      }
      
      // Получаем фильтры пользователя
      const filters = this.userFilters.get(ctx.chat.id) || {};
      
      logger.debug(`Fetching events for chat ${ctx.chat.id}, filters:`, filters);
      const events = await this.eventService.getEvents(filters.eventType);
      logger.debug(`Received ${events.length} events from eventService`);
      
      // Применяем фильтры
      let filteredEvents = this.eventService.getUpcomingEvents(events);
      
      // Дополнительная фильтрация по типу события на клиентской стороне
      // (на случай если API вернул неверные данные)
      if (filters.eventType) {
        const beforeFilter = filteredEvents.length;
        filteredEvents = filteredEvents.filter(event => event.event_type === filters.eventType);
        logger.debug(`After client-side type filter (${filters.eventType}): ${filteredEvents.length} events (was ${beforeFilter})`);
      }
      
      if (filters.dateFilter) {
        filteredEvents = this.eventService.filterByDate(filteredEvents, filters.dateFilter);
        logger.debug(`After date filter (${filters.dateFilter}): ${filteredEvents.length} events`);
      }
      
      if (filters.priceFilter) {
        filteredEvents = this.eventService.filterByPrice(filteredEvents, filters.priceFilter);
        logger.debug(`After price filter (${filters.priceFilter}): ${filteredEvents.length} events`);
      }

      if (filteredEvents.length === 0) {
        const text = 'К сожалению, событий по заданным фильтрам не найдено.';
        const keyboard = new InlineKeyboard()
          .text('⚙️ Фильтры', 'show_filters').row()
          .text('🔍 Выбрать тип', 'show_types').row()
          .text('⬅️ Назад', 'back_to_menu');

        const targetMessageId = messageId || loadingMessageId;
        if (targetMessageId) {
          try {
            await ctx.api.editMessageText(ctx.chat.id, targetMessageId, text, {
              reply_markup: keyboard,
            });
          } catch (error: any) {
            logger.warn('Error editing message:', error.message);
            await ctx.reply(text, { reply_markup: keyboard });
          }
        } else {
          await ctx.reply(text, { reply_markup: keyboard });
        }
        return;
      }

      // Пагинация
      const currentPage = this.userPagination.get(ctx.chat.id) || 0;
      const totalPages = Math.ceil(filteredEvents.length / this.EVENTS_PER_PAGE);
      const startIndex = currentPage * this.EVENTS_PER_PAGE;
      const endIndex = startIndex + this.EVENTS_PER_PAGE;
      const paginatedEvents = filteredEvents.slice(startIndex, endIndex);
      
      logger.debug(`Pagination: total=${filteredEvents.length}, page=${currentPage + 1}/${totalPages}, showing=${paginatedEvents.length} events`);

      // Формируем текст без заголовка (только список событий)
      const formattedText = formatEventsList(paginatedEvents);
      
      // Основное сообщение без кнопок (только список событий)
      const keyboard = new InlineKeyboard();
      
      const targetMessageId = messageId || loadingMessageId;
      
      // Отправляем или редактируем сообщение
      if (targetMessageId && formattedText.length <= 4000) {
        try {
          await ctx.api.editMessageText(ctx.chat.id, targetMessageId, formattedText, {
            parse_mode: 'HTML',
            link_preview_options: { is_disabled: true },
            reply_markup: keyboard,
          });
        } catch (editError: any) {
          logger.warn(`Error editing message:`, editError.message || editError);
          await ctx.reply(formattedText, {
            parse_mode: 'HTML',
            link_preview_options: { is_disabled: true },
            reply_markup: keyboard,
          });
        }
      } else {
        await ctx.reply(formattedText, {
          parse_mode: 'HTML',
          link_preview_options: { is_disabled: true },
          reply_markup: keyboard,
        });
      }

      // Отправляем детали по каждому событию на текущей странице
      for (const event of paginatedEvents) {
        const eventText = formatEventMessage(event);
        const isFavorite = await this.favoritesService.isFavorite(ctx.chat.id, event.uuid);
        
        const eventKeyboard = new InlineKeyboard();
        if (isFavorite) {
          eventKeyboard.text('❌ Удалить из избранного', `favorite_remove_${event.uuid}`);
        } else {
          eventKeyboard.text('⭐ В избранное', `favorite_add_${event.uuid}`);
        }
        
        try {
          if (event.image_url) {
            await ctx.replyWithPhoto(event.image_url, {
              caption: eventText,
              parse_mode: 'HTML',
              reply_markup: eventKeyboard,
            });
          } else {
            await ctx.reply(eventText, {
              parse_mode: 'HTML',
              reply_markup: eventKeyboard,
            });
          }
        } catch (error) {
          logger.error('Error sending event:', error);
          try {
            await ctx.reply(eventText, {
              parse_mode: 'HTML',
              reply_markup: eventKeyboard,
            });
          } catch (sendError) {
            logger.error('Error sending event without photo:', sendError);
          }
        }
      }

      // Показываем кнопки пагинации, фильтры и "Главное Меню" в конце списка
      const hasActiveFilters = !!(filters.dateFilter || filters.priceFilter || filters.eventType);
      const endKeyboard = this.createPaginationEndKeyboard(currentPage, totalPages, hasActiveFilters);
      
      if (filteredEvents.length > endIndex) {
        await ctx.reply(`И еще ${filteredEvents.length - endIndex} событий.`, {
          reply_markup: endKeyboard,
        });
      } else {
        // Если это последняя страница, показываем кнопки пагинации и "Главное Меню"
        await ctx.reply('Это все события.', {
          reply_markup: endKeyboard,
        });
      }
      
      logger.debug(`Sent ${paginatedEvents.length} events (page ${currentPage + 1}/${totalPages}) to chat ${ctx.chat.id}`);
    } catch (error) {
      logger.error('Error showing events:', error);
      const errorMessage = '❌ Произошла ошибка при загрузке событий. Попробуй позже.';
      const targetMessageId = messageId || loadingMessageId;
      
      if (targetMessageId) {
        try {
          await ctx.api.editMessageText(ctx.chat.id, targetMessageId, errorMessage);
        } catch {
          await ctx.reply(errorMessage);
        }
      } else {
        await ctx.reply(errorMessage);
      }
    }
  }

  private async showEventsByType(
    ctx: Context,
    eventType: EventType,
    messageId?: number
  ): Promise<void> {
    if (!ctx.chat) return;
    let loadingMessageId: number | undefined;
    
    try {
      logger.debug(`showEventsByType called for chat ${ctx.chat.id}, type: ${eventType}, messageId: ${messageId}`);
      
      if (!messageId) {
        const loadingMsg = await ctx.reply('⏳ Загружаю события...');
        loadingMessageId = loadingMsg.message_id;
      }

      const events = await this.eventService.getEvents(eventType);
      const upcomingEvents = this.eventService.getUpcomingEvents(events);

      if (upcomingEvents.length === 0) {
        const text = `К сожалению, ближайших событий типа "${EVENT_TYPE_LABELS[eventType]}" не найдено.`;
        const keyboard = new InlineKeyboard()
          .text('🔍 Выбрать другой тип', 'show_types').row()
          .text('📅 Все события', 'show_all_events').row()
          .text('⬅️ Назад', 'back_to_menu');

        const targetMessageId = messageId || loadingMessageId;
        if (targetMessageId) {
          try {
            await ctx.api.editMessageText(ctx.chat.id, targetMessageId, text, {
              reply_markup: keyboard,
            });
          } catch (error: any) {
            logger.warn('Error editing message:', error.message);
            await ctx.reply(text, { reply_markup: keyboard });
          }
        } else {
          await ctx.reply(text, { reply_markup: keyboard });
        }
        return;
      }

      // Отправляем список событий
      const typeLabel = EVENT_TYPE_LABELS[eventType];
      const formattedText = `${typeLabel}\n\n${formatEventsList(upcomingEvents)}`;

      // Создаем клавиатуру с кнопкой "Назад"
      const backKeyboard = new InlineKeyboard()
        .text('⬅️ Назад', 'back_to_menu');

      const targetMessageId = messageId || loadingMessageId;
      
      // Telegram имеет лимит 4096 символов для editMessageText
      if (targetMessageId && formattedText.length <= 4000) {
        try {
          await ctx.api.editMessageText(ctx.chat.id, targetMessageId, formattedText, {
            parse_mode: 'HTML',
            link_preview_options: { is_disabled: true },
            reply_markup: backKeyboard,
          });
        } catch (editError: any) {
          logger.warn('Error editing message, sending new one:', editError.message);
          await ctx.reply(formattedText, {
            parse_mode: 'HTML',
            link_preview_options: { is_disabled: true },
            reply_markup: backKeyboard,
          });
        }
      } else {
        if (targetMessageId && formattedText.length > 4000) {
          logger.debug(`Message too long (${formattedText.length} chars), sending new message instead of editing`);
        }
        await ctx.reply(formattedText, {
          parse_mode: 'HTML',
          link_preview_options: { is_disabled: true },
          reply_markup: backKeyboard,
        });
      }

      // Отправляем детали по каждому событию (ограничим до 5)
      const eventsToShow = upcomingEvents.slice(0, 5);
      
      for (const event of eventsToShow) {
        const eventText = formatEventMessage(event);
        try {
          if (event.image_url) {
            await ctx.replyWithPhoto(event.image_url, {
              caption: eventText,
              parse_mode: 'HTML',
            });
          } else {
            await ctx.reply(eventText, {
              parse_mode: 'HTML',
            });
          }
        } catch (error) {
          logger.error('Error sending event:', error);
          try {
            await ctx.reply(eventText, {
              parse_mode: 'HTML',
            });
          } catch (sendError) {
            logger.error('Error sending event without photo:', sendError);
          }
        }
      }

      // Добавляем кнопку "Назад" только в конце списка событий
      const endKeyboard = new InlineKeyboard()
        .text('⬅️ Назад', 'back_to_menu');
      
      if (upcomingEvents.length > 5) {
        await ctx.reply(`И еще ${upcomingEvents.length - 5} событий этого типа.`, {
          reply_markup: endKeyboard,
        });
      } else {
        // Если событий не больше 5, показываем кнопку "Назад" в конце
        await ctx.reply('Это все ближайшие события этого типа.', {
          reply_markup: endKeyboard,
        });
      }
      
      logger.debug(`Sent ${eventsToShow.length} events of type ${eventType} to chat ${ctx.chat.id}`);
    } catch (error) {
      logger.error('Error showing events by type:', error);
      const errorMessage = '❌ Произошла ошибка при загрузке событий. Попробуй позже.';
      const targetMessageId = messageId || loadingMessageId;
      
      if (targetMessageId) {
        try {
          await ctx.api.editMessageText(ctx.chat.id, targetMessageId, errorMessage);
        } catch {
          await ctx.reply(errorMessage);
        }
      } else {
        await ctx.reply(errorMessage);
      }
    }
  }

  // Вспомогательные методы для фильтров
  private setUserDateFilter(userId: number, filter: 'today' | 'tomorrow' | 'week' | 'month'): void {
    const state = this.userFilters.get(userId) || {};
    state.dateFilter = filter;
    this.userFilters.set(userId, state);
    // Сбрасываем пагинацию при изменении фильтра
    this.userPagination.set(userId, 0);
  }

  private setUserPriceFilter(userId: number, filter: 'free' | 'cheap' | 'medium' | 'expensive' | 'luxury'): void {
    const state = this.userFilters.get(userId) || {};
    state.priceFilter = filter;
    this.userFilters.set(userId, state);
    this.userPagination.set(userId, 0);
  }

  private setUserEventType(userId: number, eventType: EventType): void {
    const state = this.userFilters.get(userId) || {};
    state.eventType = eventType;
    this.userFilters.set(userId, state);
    this.userPagination.set(userId, 0);
  }

  private clearUserFilters(userId: number): void {
    this.userFilters.delete(userId);
    this.userPagination.set(userId, 0);
  }

  private getDateFilterLabel(filter: 'today' | 'tomorrow' | 'week' | 'month'): string {
    const labels = {
      today: 'Сегодня',
      tomorrow: 'Завтра',
      week: 'Эта неделя',
      month: 'Этот месяц',
    };
    return labels[filter];
  }

  private getPriceFilterLabel(filter: 'free' | 'cheap' | 'medium' | 'expensive' | 'luxury'): string {
    const labels = {
      free: 'Бесплатно',
      cheap: 'До 500₽',
      medium: '500-1500₽',
      expensive: '1500-3000₽',
      luxury: '3000₽+',
    };
    return labels[filter];
  }

  // Создание клавиатуры фильтров
  private createFiltersKeyboard(hasActiveFilters: boolean): InlineKeyboard {
    const keyboard = new InlineKeyboard();
    
    // Фильтры по датам
    keyboard
      .text('📅 Сегодня', 'filter_date_today')
      .text('📅 Завтра', 'filter_date_tomorrow').row()
      .text('📅 Неделя', 'filter_date_week')
      .text('📅 Месяц', 'filter_date_month').row();
    
    // Фильтры по цене
    keyboard
      .text('💰 Бесплатно', 'filter_price_free')
      .text('💰 До 500₽', 'filter_price_cheap').row()
      .text('💰 500-1500₽', 'filter_price_medium')
      .text('💰 1500-3000₽', 'filter_price_expensive').row()
      .text('💰 3000₽+', 'filter_price_luxury').row();
    
    if (hasActiveFilters) {
      keyboard.text('🔄 Сбросить фильтры', 'filter_reset').row();
    }
    
    keyboard.text('⬅️ Назад', 'back_to_menu');
    
    return keyboard;
  }

  // Создание клавиатуры только с фильтрами (без пагинации)
  private createFiltersOnlyKeyboard(hasActiveFilters: boolean): InlineKeyboard {
    const keyboard = new InlineKeyboard();
    
    keyboard.text('⚙️ Фильтры', 'show_filters').row();
    
    if (hasActiveFilters) {
      keyboard.text('🔄 Сбросить фильтры', 'filter_reset').row();
    }
    
    return keyboard;
  }

  // Создание клавиатуры пагинации для конца списка
  private createPaginationEndKeyboard(
    currentPage: number,
    totalPages: number,
    hasActiveFilters: boolean
  ): InlineKeyboard {
    const keyboard = new InlineKeyboard();
    
    if (totalPages > 1) {
      if (currentPage > 0) {
        keyboard.text('◀️ Назад', 'page_prev');
      }
      // Неактивная кнопка для отображения страницы
      keyboard.text(`${currentPage + 1}/${totalPages}`, 'page_info');
      if (currentPage < totalPages - 1) {
        keyboard.text('Вперед ▶️', 'page_next');
      }
      keyboard.row();
    }
    
    keyboard.text('⚙️ Фильтры', 'show_filters').row();
    
    if (hasActiveFilters) {
      keyboard.text('🔄 Сбросить фильтры', 'filter_reset').row();
    }
    
    keyboard.text('Главное Меню', 'back_to_menu');
    
    return keyboard;
  }

  // Показ избранного
  private async showFavorites(ctx: Context): Promise<void> {
    if (!ctx.chat) return;
    
    try {
      const favorites = await this.favoritesService.getFavorites(ctx.chat.id);
      
      if (favorites.length === 0) {
        const text = '⭐ У вас пока нет избранных событий.\n\nДобавьте события в избранное, нажав кнопку ⭐ на интересующем событии.';
        const keyboard = new InlineKeyboard()
          .text('📅 Все события', 'show_all_events').row()
          .text('⬅️ Назад', 'back_to_menu');
        await ctx.reply(text, { reply_markup: keyboard });
        return;
      }

      const upcomingFavorites = this.eventService.getUpcomingEvents(favorites);
      
      if (upcomingFavorites.length === 0) {
        const text = '⭐ В вашем избранном нет предстоящих событий.';
        const keyboard = new InlineKeyboard()
          .text('📅 Все события', 'show_all_events').row()
          .text('⬅️ Назад', 'back_to_menu');
        await ctx.reply(text, { reply_markup: keyboard });
        return;
      }

      const formattedText = `⭐ <b>Избранные события</b> <i>(${upcomingFavorites.length})</i>\n\n${formatEventsList(upcomingFavorites)}`;
      
      const keyboard = new InlineKeyboard()
        .text('📅 Все события', 'show_all_events').row()
        .text('⬅️ Назад', 'back_to_menu');
      
      await ctx.reply(formattedText, {
        parse_mode: 'HTML',
        link_preview_options: { is_disabled: true },
        reply_markup: keyboard,
      });

      // Показываем детали избранных событий
      for (const event of upcomingFavorites.slice(0, 5)) {
        const eventText = formatEventMessage(event);
        const isFavorite = await this.favoritesService.isFavorite(ctx.chat.id, event.uuid);
        const favoriteKeyboard = new InlineKeyboard();
        
        if (isFavorite) {
          favoriteKeyboard.text('❌ Удалить из избранного', `favorite_remove_${event.uuid}`);
        } else {
          favoriteKeyboard.text('⭐ В избранное', `favorite_add_${event.uuid}`);
        }

        try {
          if (event.image_url) {
            await ctx.replyWithPhoto(event.image_url, {
              caption: eventText,
              parse_mode: 'HTML',
              reply_markup: favoriteKeyboard,
            });
          } else {
            await ctx.reply(eventText, {
              parse_mode: 'HTML',
              reply_markup: favoriteKeyboard,
            });
          }
        } catch (error) {
          logger.error('Error sending favorite event:', error);
        }
      }
      
      // Добавляем кнопку "Главное Меню" только в конце списка избранного
      const endFavoriteKeyboard = new InlineKeyboard()
        .text('Главное Меню', 'back_to_menu');
      await ctx.reply('Это все избранные события.', {
        reply_markup: endFavoriteKeyboard,
      });
    } catch (error) {
      logger.error('Error showing favorites:', error);
      await ctx.reply('❌ Произошла ошибка при загрузке избранного.');
    }
  }

  // Обработка действий с избранным
  private async handleFavoriteAction(
    ctx: Context,
    eventUuid: string,
    action: 'add' | 'remove'
  ): Promise<void> {
    if (!ctx.chat) return;
    
    try {
      // Нужно получить событие по UUID из всех событий
      const allEvents = await this.eventService.getEvents();
      const event = allEvents.find(e => e.uuid === eventUuid);
      
      if (!event) {
        await ctx.answerCallbackQuery({ text: 'Событие не найдено', show_alert: true });
        return;
      }

      if (action === 'add') {
        const added = await this.favoritesService.addFavorite(ctx.chat.id, event);
        await ctx.answerCallbackQuery({
          text: added ? '⭐ Добавлено в избранное' : 'Уже в избранном',
        });
      } else {
        const removed = await this.favoritesService.removeFavorite(ctx.chat.id, eventUuid);
        await ctx.answerCallbackQuery({
          text: removed ? '❌ Удалено из избранного' : 'Не было в избранном',
        });
      }
    } catch (error) {
      logger.error('Error handling favorite action:', error);
      await ctx.answerCallbackQuery({ text: 'Ошибка', show_alert: true });
    }
  }

  // Показ фильтров
  private async showFiltersMenu(ctx: Context, messageId?: number): Promise<void> {
    if (!ctx.chat) return;
    
    const filters = this.userFilters.get(ctx.chat.id) || {};
    const hasFilters = !!(filters.dateFilter || filters.priceFilter);
    
    let text = '⚙️ <b>Фильтры событий</b>\n\n';
    
    if (filters.dateFilter) {
      text += `📅 <b>Дата:</b> ${this.getDateFilterLabel(filters.dateFilter)}\n`;
    }
    if (filters.priceFilter) {
      text += `💰 <b>Цена:</b> ${this.getPriceFilterLabel(filters.priceFilter)}\n`;
    }
    
    if (!hasFilters) {
      text += '\nВыберите фильтры для поиска событий:';
    }
    
    const keyboard = this.createFiltersKeyboard(hasFilters);
    
    if (messageId) {
      try {
        await ctx.api.editMessageText(ctx.chat.id, messageId, text, {
          parse_mode: 'HTML',
          reply_markup: keyboard,
        });
      } catch (error: any) {
        await ctx.reply(text, { parse_mode: 'HTML', reply_markup: keyboard });
      }
    } else {
      await ctx.reply(text, { parse_mode: 'HTML', reply_markup: keyboard });
    }
  }
}
