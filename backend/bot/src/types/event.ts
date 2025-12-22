export interface Event {
  id: number;
  uuid: string;
  source_id?: string;
  title: string;
  description: string;
  price: number;
  date_preview: string;
  date_list: string[];
  place: string;
  event_type: string;
  genre: string;
  age?: string;
  image_url: string;
  url: string;
  created_at: string;
}

export type EventType = 
  | 'concert'
  | 'stand_up'
  | 'exhibition'
  | 'theater'
  | 'cinema'
  | 'sport'
  | 'excursion'
  | 'show'
  | 'quest'
  | 'master_class';

export const EVENT_TYPES: EventType[] = [
  'concert',
  'stand_up',
  'exhibition',
  'theater',
  'cinema',
  'sport',
  'excursion',
  'show',
  'quest',
  'master_class',
];

export const EVENT_TYPE_LABELS: Record<EventType, string> = {
  concert: '🎵 Концерты',
  stand_up: '🎤 Стендап',
  exhibition: '🖼 Выставки',
  theater: '🎭 Театр',
  cinema: '🎬 Кино',
  sport: '⚽ Спорт',
  excursion: '🚶 Экскурсии',
  show: '🎪 Шоу',
  quest: '🔍 Квесты',
  master_class: '🎓 Мастер-классы',
};
