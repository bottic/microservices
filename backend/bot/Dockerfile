FROM node:20-alpine

WORKDIR /app

# Копируем package.json и package-lock.json (если есть)
COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci --only=production

# Копируем исходный код
COPY . .

# Компилируем TypeScript
RUN npm run build

# Открываем порт для Local API (healthcheck и добавление событий)
EXPOSE 3001

# Запускаем бота
CMD ["npm", "start"]
