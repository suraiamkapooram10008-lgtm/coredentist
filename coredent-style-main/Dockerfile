# Multi-stage build for production
# Updated: 2026-03-24 - Fixed healthcheck and PWA config
# Force fresh build by including build timestamp file

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy build timestamp file FIRST (changes on every deploy)
COPY .build-timestamp ./

# Copy ALL source code
COPY . .

# Set build environment variables
ENV VITE_API_BASE_URL=https://coredentist-production.up.railway.app/api/v1
ENV VITE_ENABLE_DEMO_MODE=false
ENV VITE_DEBUG=false
ENV CI=true

# Install dependencies
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

# Fallback: copy index.html from source if not in dist (fixes PWA build issue)
RUN if [ ! -f /usr/share/nginx/html/index.html ]; then \
    cp /app/index.html /usr/share/nginx/html/index.html; \
    fi

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Verify nginx config is valid
RUN nginx -t

# Expose port 80
EXPOSE 80

# Health check - increased start period to allow nginx to fully initialize
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=10 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
