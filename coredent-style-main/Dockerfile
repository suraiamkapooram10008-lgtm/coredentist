# Multi-stage build for production

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build arguments
ARG VITE_API_BASE_URL=https://coredentist-production.up.railway.app/api/v1
ARG VITE_ENABLE_DEMO_MODE=false
ARG VITE_DEBUG=false

# Set environment variables for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_ENABLE_DEMO_MODE=$VITE_ENABLE_DEMO_MODE
ENV VITE_DEBUG=$VITE_DEBUG
ENV CI=true

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including dev) for build, skip prepare script
RUN npm ci --ignore-scripts

# Copy source code
COPY . .

# Build the application with verbose output
RUN npm run build || (echo "Build failed, checking dist..." && ls -la dist/ && exit 1)

# Verify dist folder exists and has content
RUN if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then echo "ERROR: dist folder is empty!"; exit 1; fi

# Remove dev dependencies, keep only production
RUN npm prune --omit=dev

# Stage 2: Production
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Verify files were copied
RUN ls -la /usr/share/nginx/html/ || echo "WARNING: dist files not found"

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
