# Multi-stage build for production
# Updated: 2026-03-24 - Fixed healthcheck and PWA config
# CACHE BUSTING: Changed order to break all caches

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy ALL source code first (breaks npm cache)
COPY . .

# Set build environment variables
ENV VITE_API_BASE_URL=https://coredentist-production.up.railway.app/api/v1
ENV VITE_ENABLE_DEMO_MODE=false
ENV VITE_DEBUG=false
ENV CI=true

# Install dependencies (will run fresh because source changed)
RUN npm ci --ignore-scripts

# Build the application
RUN npm run build

# Verify build output
RUN ls -la dist/ && test -f dist/index.html

# Stage 2: Production
FROM nginx:alpine

# Install wget for healthcheck
RUN apk add --no-cache wget

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Verify nginx config is valid
RUN nginx -t

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
