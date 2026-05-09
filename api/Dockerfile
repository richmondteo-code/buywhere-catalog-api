FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev

COPY dist/ dist/

# BUY-14329: Cap COUNT(*) queries to avoid statement_timeout on 14M row products table
RUN sed -i "s|SELECT COUNT(\*) FROM products WHERE \${dealWhere}|SELECT COUNT(*) FROM (SELECT 1 FROM products WHERE \${dealWhere} LIMIT 1001) _sub|g" dist/routes/products.js && \
    sed -i "s|SELECT COUNT(\*) FROM products \${where}|SELECT COUNT(*) FROM (SELECT 1 FROM products \${where} LIMIT 1001) _sub|g" dist/routes/mcp.js && \
    sed -i "s|SELECT COUNT(\*) FROM products WHERE \${whereClause}|SELECT COUNT(*) FROM (SELECT 1 FROM products WHERE \${whereClause} LIMIT 1001) _sub|g" dist/routes/mcp.js && \
    sed -i "s|SELECT COUNT(\*) FROM products'|SELECT reltuples::bigint AS count FROM pg_class WHERE oid = '\\\\''public.products'\\\\''::regclass'|g" dist/mcp-server.js

ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "dist/index.js"]
