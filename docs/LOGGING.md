# Structured Logging Documentation

## Overview

The AsterDEX Trading API uses structured logging with JSON output for machine-readable logs. This makes it easy to parse, search, and analyze logs in production environments.

## Features

- **JSON Output**: All logs are formatted as JSON for easy parsing
- **ISO Timestamps**: UTC timestamps in ISO 8601 format
- **Log Levels**: Support for DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context Processors**: Automatic addition of timestamp, log level, logger name, filename, function name, and line number
- **Sensitive Data Filtering**: Automatic redaction of private keys, signatures, and secrets
- **Request Logging**: Automatic logging of all HTTP requests with timing information
- **Error Logging**: Full stack traces with context for debugging

## Configuration

Logging is configured via the `LOG_LEVEL` environment variable:

```bash
LOG_LEVEL=INFO  # Default
LOG_LEVEL=DEBUG  # For development
LOG_LEVEL=WARNING  # For production (less verbose)
```

## Log Format

Each log entry is a JSON object with the following structure:

```json
{
  "event": "request_completed",
  "timestamp": "2024-01-01T12:00:00.000000Z",
  "level": "info",
  "logger": "src.app",
  "filename": "app.py",
  "func_name": "log_requests",
  "lineno": 123,
  "app": "asterdex-trading-api",
  "method": "POST",
  "path": "/webhook/tradingview",
  "status_code": 200,
  "process_time_ms": 45.23
}
```

## Sensitive Data Protection

The logging system automatically filters sensitive information:

- **Private Keys**: Any 0x-prefixed 64-character hex string is redacted
- **Signatures**: Any 0x-prefixed 130-character hex string is redacted
- **Webhook Secrets**: The `webhook_secret` field is always redacted
- **Authorization Headers**: Any authorization header is redacted

Example:
```python
logger.info("user_authenticated", private_key="0x1234...")
# Output: {"event": "user_authenticated", "private_key": "***REDACTED***"}
```

## Usage Examples

### Basic Logging

```python
from src.logging_config import get_logger

logger = get_logger(__name__)

# Info level
logger.info("operation_completed", user_id=123, action="trade")

# Warning level
logger.warning("rate_limit_approaching", remaining=10)

# Error level with exception
try:
    risky_operation()
except Exception as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
```

### Request Context

The middleware automatically logs all requests:

```json
{
  "event": "request_received",
  "method": "POST",
  "path": "/webhook/tradingview",
  "client_host": "192.168.1.1"
}
```

And responses:

```json
{
  "event": "request_completed",
  "method": "POST",
  "path": "/webhook/tradingview",
  "status_code": 200,
  "process_time_ms": 45.23
}
```

### Service Layer Logging

Services automatically log their operations:

```python
# Trading service
logger.info("opening_position", symbol="BTCUSDT", side="BUY", quantity="0.001")
logger.info("position_opened", symbol="BTCUSDT", order_id=12345, status="FILLED")

# Position service
logger.info("getting_positions", symbol="BTCUSDT")
logger.info("positions_retrieved", symbol="BTCUSDT", total_positions=5, non_zero_positions=2)

# Account service
logger.info("fetching_balance_from_api", use_cache=False)
logger.info("balance_retrieved", assets_count=3, cached=True)
```

### Error Logging

Errors are logged with full context:

```python
logger.error(
    "failed_to_open_position",
    symbol="BTCUSDT",
    error=str(e),
    exc_info=True  # Includes full stack trace
)
```

## Log Aggregation

For production deployments, consider using log aggregation tools:

- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Splunk**: Enterprise log management
- **Datadog**: Cloud monitoring and logging
- **CloudWatch**: AWS native logging (if deployed on AWS)

Example Logstash configuration:

```ruby
input {
  file {
    path => "/var/log/asterdex-trading-api/*.log"
    codec => json
  }
}

filter {
  # Logs are already in JSON format
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "asterdex-trading-api-%{+YYYY.MM.dd}"
  }
}
```

## Querying Logs

Since logs are in JSON format, you can easily query them:

### Using jq (command line)

```bash
# Get all error logs
cat app.log | jq 'select(.level == "error")'

# Get logs for specific symbol
cat app.log | jq 'select(.symbol == "BTCUSDT")'

# Get slow requests (> 1 second)
cat app.log | jq 'select(.process_time_ms > 1000)'

# Count errors by type
cat app.log | jq -r 'select(.level == "error") | .event' | sort | uniq -c
```

### Using grep

```bash
# Find all webhook requests
grep "webhook_received" app.log

# Find errors
grep '"level":"error"' app.log

# Find specific symbol trades
grep "BTCUSDT" app.log
```

## Best Practices

1. **Use Structured Fields**: Always use key-value pairs instead of string formatting
   ```python
   # Good
   logger.info("order_placed", symbol="BTCUSDT", order_id=123)
   
   # Bad
   logger.info(f"Order placed for {symbol} with ID {order_id}")
   ```

2. **Include Context**: Add relevant context to help with debugging
   ```python
   logger.error(
       "api_call_failed",
       endpoint="/fapi/v3/order",
       symbol="BTCUSDT",
       error=str(e),
       exc_info=True
   )
   ```

3. **Use Appropriate Log Levels**:
   - `DEBUG`: Detailed information for diagnosing problems
   - `INFO`: General informational messages
   - `WARNING`: Warning messages for potentially harmful situations
   - `ERROR`: Error messages for serious problems
   - `CRITICAL`: Critical messages for very serious errors

4. **Don't Log Sensitive Data**: The system filters common patterns, but be careful with custom data

5. **Log Performance Metrics**: Include timing information for operations
   ```python
   start_time = time.time()
   result = await operation()
   duration = time.time() - start_time
   logger.info("operation_completed", duration_ms=duration * 1000)
   ```

## Monitoring and Alerts

Set up alerts based on log patterns:

- **Error Rate**: Alert if error rate exceeds threshold
- **Response Time**: Alert if average response time is too high
- **Failed Trades**: Alert on failed order placements
- **API Errors**: Alert on AsterDEX API errors

Example alert query (for Elasticsearch):

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "error"}},
        {"range": {"timestamp": {"gte": "now-5m"}}}
      ]
    }
  }
}
```

## Troubleshooting

### Logs Not Appearing

1. Check `LOG_LEVEL` environment variable
2. Verify stdout is not being buffered
3. Check file permissions if writing to file

### Too Many Logs

1. Increase `LOG_LEVEL` to `WARNING` or `ERROR`
2. Implement log sampling for high-volume endpoints
3. Use log rotation to manage disk space

### Sensitive Data in Logs

1. Review the sensitive patterns in `src/logging_config.py`
2. Add custom patterns if needed
3. Test with sample data to verify filtering

## Performance Considerations

- Structured logging has minimal performance impact
- JSON serialization is fast with modern libraries
- Async logging prevents blocking the main thread
- Consider log sampling for very high-traffic endpoints
