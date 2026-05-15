FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY dist/ dist/
EXPOSE 8080
CMD ["node", "--max-old-space-size=450", "dist/index.js"]