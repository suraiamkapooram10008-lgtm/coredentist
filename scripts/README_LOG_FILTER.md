# Log Filter and Search Utility

A powerful Python utility for filtering and searching Docker/Nginx logs to diagnose deployment issues.

## Features

- **Filter by log level**: INFO, NOTICE, WARNING, ERROR, DEBUG
- **Filter by source**: Docker entrypoint scripts, nginx modules
- **Search with regex**: Find specific patterns in logs
- **Time range filtering**: Narrow down logs to specific time periods
- **Error/Warning detection**: Automatically find problematic entries
- **Worker process tracking**: Extract nginx worker process information
- **Statistics**: Get overview of log composition

## Installation

No installation required! Just ensure you have Python 3.6+ installed.

## Usage Examples

### 1. Show all logs with statistics

```bash
# From a file
python scripts/log_filter.py your_logs.txt --stats

# From stdin (pipe logs)
cat your_logs.txt | python scripts/log_filter.py --stats
```

### 2. Search for errors

```bash
python scripts/log_filter.py your_logs.txt --errors
```

### 3. Search for warnings

```bash
python scripts/log_filter.py your_logs.txt --warnings
```

### 4. Search for specific pattern

```bash
# Case-insensitive search for "nginx"
python scripts/log_filter.py your_logs.txt -s "nginx"

# Search for "entrypoint" or "docker"
python scripts/log_filter.py your_logs.txt -s "entrypoint|docker"
```

### 5. Filter by log level

```bash
# Show only NOTICE level logs
python scripts/log_filter.py your_logs.txt -l notice

# Show both ERROR and WARNING
python scripts/log_filter.py your_logs.txt -l error -l warning
```

### 6. Filter by source

```bash
# Show logs from docker-entrypoint.sh
python scripts/log_filter.py your_logs.txt --source "docker-entrypoint"

# Show logs from numbered scripts (10-listen, 20-envsubst, etc.)
python scripts/log_filter.py your_logs.txt --source "^\d+-"
```

### 7. Extract worker process information

```bash
python scripts/log_filter.py your_logs.txt --workers
```

### 8. Show line numbers

```bash
python scripts/log_filter.py your_logs.txt --errors --line-numbers
```

### 9. Combine multiple filters

```bash
# Show errors from docker-entrypoint with line numbers
python scripts/log_filter.py your_logs.txt --errors --source "docker-entrypoint" --line-numbers
```

## Analyzing Your Nginx Logs

Based on the logs you provided, here's how to diagnose issues:

### Quick Health Check

```bash
# Check for any errors or warnings
python scripts/log_filter.py your_logs.txt --errors --warnings --stats
```

### Check Startup Sequence

```bash
# View all entrypoint script activity
python scripts/log_filter.py your_logs.txt --source "docker-entrypoint"
```

### Check Worker Processes

```bash
# See how many workers started
python scripts/log_filter.py your_logs.txt --workers
```

### Search for Configuration Issues

```bash
# Look for configuration-related messages
python scripts/log_filter.py your_logs.txt -s "config|configuration|template"
```

## Understanding Your Logs

Your nginx logs show:

1. **Normal startup**: Docker entrypoint scripts executed successfully
2. **Configuration applied**: nginx.conf was loaded
3. **Workers started**: Multiple worker processes (PIDs 24-55) started
4. **No errors**: The logs show a clean startup

If your frontend is failing despite these logs looking normal, check:

1. **Health check endpoint**: Ensure `/health` returns 200
2. **Build output**: Verify `dist/index.html` exists
3. **Port binding**: Ensure nginx is listening on the correct port
4. **Runtime errors**: Check browser console for JavaScript errors

## Troubleshooting Railway Deployment

### Common Issues

1. **Build fails**: Check if `npm run build` completes successfully
2. **Missing index.html**: Ensure Vite generates the file
3. **Health check fails**: Verify `/health` endpoint responds
4. **Port mismatch**: Railway expects port 80 for HTTP

### Debug Commands

```bash
# Test build locally
cd coredent-style-main
npm run build
ls -la dist/

# Check if index.html exists
test -f dist/index.html && echo "OK" || echo "MISSING"

# Test Docker build
docker build -t test-frontend .
docker run -p 8080:80 test-frontend
curl http://localhost:8080/health
```

## Advanced Usage

### Custom Time Range

```python
from datetime import datetime
from scripts.log_filter import LogFilter

# Load logs
with open('your_logs.txt') as f:
    logs = f.read()

filter = LogFilter(logs)

# Filter to specific time range
start = datetime(2026, 3, 24, 11, 30, 0)
end = datetime(2026, 3, 24, 12, 0, 0)
filtered = filter.filter_by_time_range(start, end)

for entry in filtered:
    print(filter.format_entry(entry))
```

### Custom Search Patterns

```python
# Search for specific error patterns
errors = filter.search(r'502|503|504|timeout|connection refused')
```

## Support

For issues or questions, check:
- Railway deployment logs in dashboard
- Docker build logs
- Browser developer console
- Network tab for failed requests