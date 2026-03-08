# Frontend Dockerfile - Multi-stage: Node.js build → nginx serve

# Stage 1: Build React app
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files first (layer cache)
# Note: paths are relative to project root build context
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts

# Copy source and build
COPY frontend/ .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built static files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config (handles SPA routing + API proxy)
# Note: build context must be project root (see docker-compose.yml)
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
