FROM node:20-slim
ARG CACHE_BUST=1
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY dist/ dist/
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=15s \
  CMD ["curl", "-sf", "http://localhost:3000/health"]
CMD ["node", "dist/index.js"]