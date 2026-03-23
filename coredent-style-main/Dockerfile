# Multi-stage build for production

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including dev) for build, skip prepare script
RUN npm ci --ignore-scripts

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Remove dev dependencies, keep only production
RUN npm prune --omit=dev

# Stage 2: Production
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create entrypoint script to handle PORT variable
RUN echo '#!/bin/sh\n\
PORT=${PORT:-80}\n\
sed -i "s/listen 80;/listen $PORT;/" /etc/nginx/conf.d/default.conf\n\
nginx -g "daemon off;"\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

# Expose port (default 80, but Railway will override with PORT env var)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:${PORT:-80}/ || exit 1

# Start with entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
