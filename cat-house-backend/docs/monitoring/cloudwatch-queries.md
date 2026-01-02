# CloudWatch Logs Insights Queries

This document contains common CloudWatch Logs Insights queries for troubleshooting and monitoring the Cat House services.

## Prerequisites

- Access to AWS Console with CloudWatch Logs permissions
- Log groups for all 4 production services are available

## Log Groups

```
/ecs/cat-house/staging/auth-service
/ecs/cat-house/staging/catalog-service
/ecs/cat-house/staging/installation-service
/ecs/cat-house/staging/proxy-service
```

## Common Queries

### 1. Find All Errors in Last Hour

```
fields @timestamp, service, message, trace_id, function, line
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

**Use case**: Quickly identify recent errors across all services
**Time range**: Last 1 hour

---

### 2. Track Request by Trace ID

```
fields @timestamp, service, level, message, extra
| filter trace_id = "REPLACE_WITH_TRACE_ID"
| sort @timestamp asc
```

**Use case**: Follow a specific request across all services using correlation ID
**Instructions**: Replace `REPLACE_WITH_TRACE_ID` with actual trace ID from response headers

---

### 3. Calculate Average Response Time by Endpoint

```
fields @timestamp, extra.path as endpoint, extra.duration_ms as duration
| filter extra.duration_ms > 0
| stats avg(duration) as avg_duration, 
        max(duration) as max_duration, 
        min(duration) as min_duration,
        count(*) as request_count 
  by endpoint
| sort avg_duration desc
```

**Use case**: Identify slow endpoints
**Time range**: Last 15 minutes to 1 hour

---

### 4. Error Rate by Service

```
fields @timestamp, service
| stats count(*) as total, 
        sum(level = "ERROR") as errors 
  by service
| fields service, errors, total, (errors / total * 100) as error_rate
| sort error_rate desc
```

**Use case**: Compare error rates across services
**Time range**: Last 1 hour

---

### 5. Slow Queries (> 200ms)

```
fields @timestamp, service, extra.path, extra.duration_ms, trace_id
| filter extra.duration_ms > 200
| sort extra.duration_ms desc
| limit 50
```

**Use case**: Identify requests taking longer than 200ms
**Time range**: Last 15 minutes

---

### 6. Requests per Minute

```
fields @timestamp
| filter extra.method != ""
| stats count(*) as requests by bin(1m)
| sort @timestamp desc
```

**Use case**: Track request volume over time
**Time range**: Last 1 hour

---

### 7. User Activity by Trace

```
fields @timestamp, trace_id, extra.path, extra.method, extra.status_code
| filter trace_id like /YOUR_PREFIX/
| sort @timestamp asc
```

**Use case**: Debug user-specific issues
**Instructions**: Replace `YOUR_PREFIX` with first few characters of user's trace ID

---

### 8. Database Connection Issues

```
fields @timestamp, service, message
| filter message like /database|connection|pool/
| sort @timestamp desc
| limit 100
```

**Use case**: Troubleshoot database connectivity problems
**Time range**: Last 1 hour

---

### 9. 5XX Errors

```
fields @timestamp, service, extra.path, extra.status_code, message, trace_id
| filter extra.status_code >= 500 and extra.status_code < 600
| sort @timestamp desc
| limit 100
```

**Use case**: Find all server errors
**Time range**: Last 1 hour

---

### 10. Requests by HTTP Method

```
fields @timestamp, extra.method as method
| filter extra.method != ""
| stats count(*) as count by method
| sort count desc
```

**Use case**: Analyze API usage patterns
**Time range**: Last 1 hour

---

## Creating Saved Queries

1. Go to CloudWatch Console
2. Select **Logs > Insights**
3. Select relevant log groups
4. Paste query from above
5. Click **Run query**
6. Click **Save** button
7. Give it a descriptive name
8. Query will appear in **Saved queries** tab

## Best Practices

- Use appropriate time ranges to avoid scanning too much data
- Save frequently used queries for quick access
- Use specific filters to reduce query execution time
- Include trace_id in queries when debugging specific requests
- Set up CloudWatch Insights query aliases for team members

## Query Performance Tips

- Filter early in the query (use `filter` before `stats`)
- Limit result sets with `limit` clause
- Use `bin()` function for time-based aggregations
- Index on frequently queried fields (trace_id, service, level)

## Support

For questions or issues with queries, contact the platform team.
