# Runbook: Service Down Alarm

## Alarm Details

- **Alarm Name**: `{environment}-{service}-down`
- **Severity**: CRITICAL
- **Metric**: ECS RunningTaskCount < 1
- **Threshold**: Less than 1 running task for 2 consecutive periods

## Impact

- Service is completely unavailable
- API endpoints return 503 Service Unavailable
- Users cannot access affected functionality
- Potential data loss if prolonged outage

## Common Causes

1. Failed health checks (most common)
2. Database connection failures
3. Out of memory (OOM) kills
4. Application crash on startup
5. ECS task definition issues
6. Resource constraints (CPU/Memory)

## Diagnosis Steps

### 1. Check ECS Console

Navigate to ECS Console and check task status:

```bash
# Get service status
aws ecs describe-services \
  --cluster cat-house-staging \
  --services cat-house-staging-auth-service \
  --query 'services[0].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount,Events:events[0:3]}'

# List recent tasks
aws ecs list-tasks \
  --cluster cat-house-staging \
  --service-name cat-house-staging-auth-service \
  --desired-status STOPPED \
  --max-items 5
```

### 2. Check Why Task Stopped

```bash
# Get stopped reason
aws ecs describe-tasks \
  --cluster cat-house-staging \
  --tasks TASK_ARN_HERE \
  --query 'tasks[0].{StoppedReason:stoppedReason,StoppedAt:stoppedAt,Containers:containers[*].{Name:name,Reason:reason,ExitCode:exitCode}}'
```

### 3. Check CloudWatch Logs

View last logs before crash:

```bash
# Tail service logs
aws logs tail /ecs/cat-house/staging/auth-service \
  --follow \
  --since 30m

# Filter for errors
aws logs tail /ecs/cat-house/staging/auth-service \
  --filter-pattern "ERROR" \
  --since 1h
```

**Or use CloudWatch Console**:
1. Go to CloudWatch > Log Groups
2. Select `/ecs/cat-house/staging/auth-service`
3. View recent log streams
4. Look for errors before task stopped

### 4. Check Health Endpoint

Test health check manually:

```bash
# If ALB is accessible
curl -v https://api.gamificator.click/api/v1/auth/health

# Check health target group in ALB
aws elbv2 describe-target-health \
  --target-group-arn TARGET_GROUP_ARN
```

### 5. Check Database Connectivity

Verify Neon database is accessible:

```bash
# From local machine with DATABASE_URL
psql $DATABASE_URL -c "SELECT 1;"

# Check from within AWS (if VPC endpoint configured)
# This would require exec into a running task
```

### 6. Check Recent Deployments

```bash
# Get recent task definition revisions
aws ecs describe-task-definition \
  --task-definition cat-house-staging-auth-service \
  --query 'taskDefinition.{Family:family,Revision:revision,RegisteredAt:registeredAt}'

# List recent deployments
aws ecs list-tasks \
  --cluster cat-house-staging \
  --service-name cat-house-staging-auth-service \
  --max-items 10
```

## Resolution Steps

### Scenario A: Failed Health Check

**Symptoms**: Task stops after starting, stoppedReason mentions health check

**Steps**:
1. Review health endpoint code
2. Check if dependencies (database) are accessible
3. Verify environment variables are correct
4. Check if migrations need to run
5. Redeploy with fixes

```bash
# Force new deployment to restart tasks
aws ecs update-service \
  --cluster cat-house-staging \
  --service cat-house-staging-auth-service \
  --force-new-deployment
```

### Scenario B: Database Connection Failed

**Symptoms**: Logs show database connection errors

**Steps**:
1. Verify Neon database is running
2. Check DATABASE_URL in GitHub Secrets
3. Verify environment variables in ECS task definition
4. Test database connection from local machine
5. Check if database migrations completed

```bash
# Update service with corrected environment variables
# (Must be done through GitHub Actions or Terraform)

# Force restart after fixing
aws ecs update-service \
  --cluster cat-house-staging \
  --service cat-house-staging-auth-service \
  --force-new-deployment
```

### Scenario C: Out of Memory (OOM)

**Symptoms**: Exit code 137, logs show gradual memory increase

**Steps**:
1. Check CloudWatch Container Insights for memory usage
2. Review code for memory leaks
3. Increase memory limit in task definition

```bash
# Update task definition with more memory (via Terraform)
# Edit terraform/ecs_services.tf
# Change memory from 512 to 1024

# Apply with Terraform
cd terraform
terraform plan
terraform apply

# Service will auto-deploy with new task definition
```

### Scenario D: Application Crash

**Symptoms**: Python traceback in logs, non-zero exit code

**Steps**:
1. Review error logs for stack trace
2. Identify bug in code
3. Fix code locally
4. Create PR and deploy via CI/CD
5. Monitor for successful startup

### Scenario E: Resource Constraints

**Symptoms**: Tasks pending, not enough CPU/memory in cluster

**Steps**:
1. Check ECS cluster capacity
2. Scale up cluster if needed
3. Or reduce resource requirements

```bash
# Check cluster capacity
aws ecs describe-clusters \
  --clusters cat-house-staging \
  --query 'clusters[0].{RegisteredContainerInstancesCount:registeredContainerInstancesCount,ActiveServicesCount:activeServicesCount,RunningTasksCount:runningTasksCount}'

# This shouldn't happen with Fargate, but check service limits
aws service-quotas get-service-quota \
  --service-code fargate \
  --quota-code L-3032A538
```

## Rollback Procedure

If recent deployment caused the issue:

```bash
# Get previous task definition revision
aws ecs describe-task-definition \
  --task-definition cat-house-staging-auth-service \
  --query 'taskDefinition.revision'

# Rollback to previous revision (N-1)
aws ecs update-service \
  --cluster cat-house-staging \
  --service cat-house-staging-auth-service \
  --task-definition cat-house-staging-auth-service:PREVIOUS_REVISION

# Force new deployment
aws ecs update-service \
  --cluster cat-house-staging \
  --service cat-house-staging-auth-service \
  --force-new-deployment
```

## Verification

After applying fix:

```bash
# Watch task status
watch -n 5 'aws ecs describe-services \
  --cluster cat-house-staging \
  --services cat-house-staging-auth-service \
  --query "services[0].runningCount"'

# Test health endpoint
curl -v https://api.gamificator.click/api/v1/auth/health

# Check metrics endpoint
curl https://api.gamificator.click/api/v1/auth/metrics
```

## Escalation

- **If not resolved in 15 minutes**: Contact on-call engineer
- **If critical and not resolved in 30 minutes**: Page engineering manager
- **Emergency contact**: [Add emergency contact info]

## Post-Incident

1. Document what happened in incident report
2. Create GitHub issue for root cause analysis
3. Update runbook if new scenario discovered
4. Schedule post-mortem if critical impact
5. Review monitoring and add alerts if gaps found

## Prevention

- Enable auto-scaling for ECS services
- Implement circuit breakers for database connections
- Add startup probes with longer grace periods
- Monitor memory usage trends
- Set up pre-deployment validation tests

## Related Runbooks

- [High Error Rate Runbook](./runbook-high-error-rate.md)
- [High Latency Runbook](./runbook-high-latency.md)
- [Database Issues Runbook](./runbook-database-issues.md)

## Last Updated

- **Date**: 2025-12-31
- **Updated by**: DevOps Team
- **Changes**: Initial version
