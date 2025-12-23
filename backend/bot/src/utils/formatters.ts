import { Event, EVENT_TYPE_LABELS, EventType } from '../types/event';

// Вспомогательная функция для получения русского названия типа события
function getEventTypeLabel(eventType: string): string | null {
  if (eventType && EVENT_TYPE_LABELS[eventType as EventType]) {
    return EVENT_TYPE_LABELS[eventType as EventType];
  }
  return null;
}

export function formatEventMessage(event: Event): string {
  const datePreview = new Date(event.date_preview);
  const formattedDate = datePreview.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const datesList = event.date_list
    .map(date => {
      const d = new Date(date);
      return d.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    })
    .join(', ');

  let message = `<b>${escapeHtml(event.title)}</b>\n\n`;
  
  if (event.description) {
    const description = event.description.length > 300 
      ? event.description.substring(0, 300) + '...'
      : event.description;
    message += `${escapeHtml(description)}\n\n`;
  }

  message += `📅 <b>Дата:</b> ${formattedDate}\n`;
  
  if (event.date_list.length > 1) {
    message += `📆 <b>Все даты:</b> ${datesList}\n`;
  }

  message += `📍 <b>Место:</b> ${escapeHtml(event.place)}\n`;
  message += `💰 <b>Цена:</b> ${event.price} ₽\n`;

  // Добавляем тип события на русском
  const eventTypeLabel = getEventTypeLabel(event.event_type);
  if (eventTypeLabel) {
    message += `🎯 <b>Тип:</b> ${eventTypeLabel}\n`;
  }

  if (event.genre) {
    message += `🎭 <b>Жанр:</b> ${escapeHtml(event.genre)}\n`;
  }

  if (event.age) {
    message += `👤 <b>Возраст:</b> ${escapeHtml(event.age)}\n`;
  }

  // Формируем ссылку "Подробнее" на основе UUID
  const eventUrl = event.url || `https://oxluma.space/event/${event.uuid}`;
  message += `\n🔗 <a href="${eventUrl}">Подробнее</a>`;

  return message;
}

export function formatEventsList(events: Event[]): string {
  if (events.length === 0) {
    return 'События не найдены.';
  }

  let message = '';

  // Не ограничиваем события здесь - пагинация уже применена в botHandlers
  // Просто форматируем все переданные события
  events.forEach((event, index) => {
    const date = new Date(event.date_preview);
    const formattedDate = date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });

    // Более красивое и структурированное форматирование
    message += `🎯 <b>${escapeHtml(event.title)}</b>\n`;
    message += `   📅 ${formattedDate}\n`;
    message += `   📍 ${escapeHtml(event.place)}\n`;
    message += `   💰 <b>${event.price} ₽</b>\n`;
    
    // Добавляем тип события на русском
    const eventTypeLabel = getEventTypeLabel(event.event_type);
    if (eventTypeLabel) {
      message += `   ${eventTypeLabel}\n`;
    }
    
    // Добавляем разделитель между событиями (кроме последнего)
    if (index < events.length - 1) {
      message += `\n`;
    }
  });

  return message;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
