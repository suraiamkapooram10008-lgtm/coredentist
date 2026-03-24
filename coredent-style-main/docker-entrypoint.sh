#!/bin/sh
set -e

echo "Starting nginx..."

# Verify nginx configuration
echo "Verifying nginx configuration..."
nginx -t

# Start nginx in the background
nginx -g "daemon off;" &
NGINX_PID=$!

# Wait for nginx to be ready
echo "Waiting for nginx to be ready..."
for i in $(seq 1 60); do
    if wget --quiet --tries=1 --spider http://localhost/health 2>/dev/null; then
        echo "Nginx is ready!"
        break
    fi
    echo "Attempt $i: Nginx not ready yet..."
    sleep 1
done

# Check if nginx is ready
if ! wget --quiet --tries=1 --spider http://localhost/health 2>/dev/null; then
    echo "ERROR: Nginx failed to start properly"
    echo "Nginx process status:"
    ps aux | grep nginx || true
    echo "Nginx error log:"
    cat /var/log/nginx/error.log || true
    exit 1
fi

echo "Nginx started successfully with PID: $NGINX_PID"

# Keep the container running
wait $NGINX_PID
