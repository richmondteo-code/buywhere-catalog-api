FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY src/ src/
COPY tsconfig.json ./
RUN npx tsc && rm -rf src tsconfig.json
RUN npm ci --omit=dev
EXPOSE 8080
CMD ["node", "dist/index.js"]