# Monitoring and Logging Documentation

This directory contains monitoring and alerting documentation for the Cat House platform.

## Overview

The Cat House platform uses comprehensive monitoring and alerting based on:
- **Prometheus metrics** for application-level metrics
- **CloudWatch Logs** for centralized logging with JSON structure
- **CloudWatch Dashboards** for visualization
- **CloudWatch Alarms** for proactive alerting
- **SNS + AWS Chatbot** for Slack notifications

## Quick Links

### Dashboards

Access dashboards in AWS Console:
- [Service Health Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=sa-east-1#dashboards:)
- [API Performance Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=sa-east-1#dashboards:)
- [Business Metrics Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=sa-east-1#dashboards:)

### Log Groups

- `/ecs/cat-house/staging/auth-service`
- `/ecs/cat-house/staging/catalog-service`
- `/ecs/cat-house/staging/installation-service`
- `/ecs/cat-house/staging/proxy-service`

## Available Documentation

### [Slack Integration Guide](./slack-integration-guide.md)

Complete guide for setting up Slack notifications with AWS Chatbot:
- Why direct webhooks don't work with SNS
- AWS Chatbot setup (recommended approach)
- Alternative Lambda-based integration
- Troubleshooting common issues

### [AWS Chatbot Setup](./aws-chatbot-setup.md)

Quick reference for the configured AWS Chatbot integration:
- Configuration details and SNS topic ARNs
- Testing alerts with sample commands
- Slack commands available
- Security best practices

### [CloudWatch Queries](./cloudwatch-queries.md)

Common CloudWatch Logs Insights queries for troubleshooting:
- Find errors across all services
- Track requests by correlation ID
- Calculate latency by endpoint
- Monitor error rates
- Identify slow queries

### [Runbooks](./runbook-service-down.md)

Step-by-step guides for responding to alarms:
- **Service Down**: When a service has no running tasks
- **High Error Rate**: When 5XX errors exceed 5%
- **High Latency**: When p95 latency exceeds 500ms
- **High CPU/Memory**: When resource usage is high

## Metrics Available

### HTTP Metrics

- `http_requests_total` - Total count of HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Current requests being processed

### Database Metrics

- `db_connections_active` - Number of active database connections
- `db_query_duration_seconds` - Query execution time

### Business Metrics

- `business_events_total` - Count of business events (user_created, installation_created, etc.)

### Health Metrics

- `service_health_status` - Service health (1=healthy, 0=unhealthy)

## Alert Severity Levels

### Critical (SNS: critical_alerts)

- Service completely down
- Error rate > 5%
- Immediate action required
- Page on-call engineer

### Warning (SNS: warning_alerts)

- High latency (p95 > 500ms)
- High CPU usage (> 80%)
- High memory usage (> 85%)
- Review within 30 minutes

## Accessing Metrics

### Prometheus Endpoint

Each service exposes a `/metrics` endpoint:

```bash
# Auth Service
curl https://api.gamificator.click/api/v1/auth/metrics

# Catalog Service
curl https://api.gamificator.click/api/v1/catalog/metrics

# Installation Service
curl https://api.gamificator.click/api/v1/installation/metrics

# Proxy Service
curl https://api.gamificator.click/api/v1/proxy/metrics
```

### CloudWatch Logs

```bash
# View recent logs
aws logs tail /ecs/cat-house/staging/auth-service --follow

# Filter for errors
aws logs tail /ecs/cat-house/staging/auth-service \
  --filter-pattern "ERROR" \
  --since 1h
```

### CloudWatch Logs Insights

1. Go to CloudWatch Console > Logs > Insights
2. Select log groups
3. Run queries from [cloudwatch-queries.md](./cloudwatch-queries.md)

## Alert Response Workflow

1. **Receive Alert** - Email/Slack notification
2. **Check Dashboard** - Assess impact and scope
3. **Follow Runbook** - Execute diagnosis steps
4. **Resolve Issue** - Apply fix or rollback
5. **Verify** - Confirm alarm clears
6. **Document** - Create incident report

## On-Call Rotation

[Add on-call rotation details]

## Escalation

- **Not resolved in 15 min**: Contact secondary engineer
- **Not resolved in 30 min**: Page engineering manager
- **Production outage**: Immediate escalation

## Monitoring Best Practices

1. **Use Correlation IDs**: Always include X-Trace-ID in requests
2. **Check Dashboards First**: Visual overview helps assess scope
3. **Start with Recent Changes**: Check recent deployments
4. **Follow the Runbook**: Don't skip steps
5. **Document Everything**: Update incident log

## Adding New Metrics

To add custom metrics in your service code:

```python
from app.metrics import track_business_event

# In your route handler
@router.post("/users")
async def create_user(user: UserCreate):
    # ... create user logic ...
    
    # Track business event
    track_business_event("user_created")
    
    return {"id": user.id}
```

## Adding New Alarms

1. Edit `terraform/cloudwatch_alarms.tf`
2. Add new `aws_cloudwatch_metric_alarm` resource
3. Link to SNS topic (critical_alerts or warning_alerts)
4. Create corresponding runbook
5. Apply with Terraform

## Related Documentation

- [Logging Configuration](../../cat-house-backend/README.md)
- [Terraform Configuration](../../cat-house-backend/terraform/README.md)
- [Architecture Documentation](../../docs/architecture/)
