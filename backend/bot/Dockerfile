FROM node:20-alpine

WORKDIR /app

# Копируем package.json и package-lock.json (если есть)
COPY package*.json ./

# Устанавливаем ВСЕ зависимости (включая devDependencies для сборки)
RUN npm ci

# Копируем исходный код
COPY . .

# Компилируем TypeScript
RUN npm run build

# Удаляем devDependencies для уменьшения размера образа
RUN npm prune --production

# Открываем порт для Local API (healthcheck и добавление событий)
EXPOSE 3001

# Запускаем бота напрямую (без npm start, чтобы избежать prestart hook)
CMD ["node", "dist/index.js"]
