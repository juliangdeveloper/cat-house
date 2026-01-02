# CI/CD Validation Checklist

## Pre-Push Validation (MANDATORY - NO EXCEPTIONS)

### 1. Run Tests
```bash
# Run from cat-house-backend/ directory

# Run tests for ALL services
foreach ($s in @("auth-service", "catalog-service", "installation-service", "proxy-service")) {
  Write-Host "`n=== Running tests in $s ===" -ForegroundColor Cyan
  cd $s
  if (Test-Path "tests") { pytest tests/ -v } else { Write-Host "No tests directory found" -ForegroundColor Yellow }
  cd ..
}
```

**EXPECTED RESULT:**
- All tests pass with "X passed in Y.YYs"
- No failed or skipped tests

**IF FAILED:** Fix the failing tests before proceeding.

---

### 2. Code Quality Checks
```bash
# Run from cat-house-backend/ directory

# Black formatting check (ALL services)
foreach ($s in @("auth-service", "catalog-service", "installation-service", "proxy-service")) {
  cd $s
  black --check app/
  cd ..
}

# Pylint check (ALL services) - must be 10.00/10
foreach ($s in @("auth-service", "catalog-service", "installation-service", "proxy-service")) {
  cd $s
  pylint app/ --max-line-length=100 --disable=C,W0621,W0613,E1101,W0122,R1715,R0903
  cd ..
}
```

**EXPECTED RESULT:**
- Black: "All done! ✨ 🍰 ✨" for all services
- Pylint: "Your code has been rated at 10.00/10" for all services

**IF FAILED:** Run `black app/` in the failing service, commit, then re-check.

---

### 3. Workflow Trigger Validation

**CRITICAL:** GitHub Actions workflows have **path filters**. Changes must be in the correct directory to trigger.

| Workflow | Trigger | Path Filter | How to Trigger |
|----------|---------|-------------|----------------|
| Backend CI | `push` to develop/main | `cat-house-backend/**` | Modify ANY file inside `cat-house-backend/` |
| Build Images | `workflow_run` after Backend CI | N/A (waits for Backend CI) | Backend CI must complete successfully |
| Deploy Staging | `workflow_run` after Build Images | N/A (waits for Build Images) | Build Images must complete successfully |
| Frontend CI | `push` to develop/main | `frontend/**` | Modify ANY file inside `frontend/` |
| Deploy Production | `workflow_dispatch` (manual) | N/A | Manual trigger only |

**BEFORE PUSHING:**
1. ✅ Check if your changes are inside `cat-house-backend/**` or `frontend/**`
2. ✅ If you only changed `.github/workflows/`, it will NOT trigger workflows
3. ✅ If you need to trigger: add a trivial file like `VERSION` or modify a docstring

**Trigger Backend CI manually:**
```bash
# Add a version file inside cat-house-backend
echo "1.0.0" > cat-house-backend/auth-service/VERSION
git add cat-house-backend/auth-service/VERSION
git commit -m "chore: bump version"
git push origin develop
```

---

### 4. Workflow Syntax Validation

**BEFORE committing workflow changes:**

```bash
# Check YAML syntax (no tabs, proper indentation)
cat .github/workflows/backend-ci.yml | Select-String "	"  # Should return NOTHING

# Validate workflow file exists
Test-Path .github/workflows/backend-ci.yml
Test-Path .github/workflows/build-images.yml
Test-Path .github/workflows/deploy-staging.yml
Test-Path .github/workflows/deploy-production.yml
Test-Path .github/workflows/retag-for-production.yml
```

**Common Syntax Errors:**
- Tabs instead of spaces (use 2 spaces for YAML indentation)
- Missing colons after keys
- Incorrect `if` condition syntax (must be `${{ ... }}`)
- Wrong workflow name in `workflow_run` trigger

---

### 5. Secrets Validation

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `NEON_STAGING_DATABASE_URL`
- `NEON_PRODUCTION_DATABASE_URL`
- `NEON_TEST_DATABASE_URL`
- `JWT_SECRET`
- `ENCRYPTION_KEY`
- `CODECOV_TOKEN`

**Validate secrets exist:**
1. Go to GitHub → Settings → Secrets and variables → Actions
2. Verify ALL secrets listed above exist
3. Click "Update" on each secret to verify it's not empty

---

### 6. Terraform State Validation

**BEFORE terraform apply:**

```bash
cd cat-house-backend/terraform

# Plan first, review changes
terraform plan -var-file="terraform.tfvars"

# Check for unexpected changes (should be specific to your intent)
# - If changing image tags: expect task definition changes
# - If adding resources: expect "X to add"
# - If removing: expect "X to destroy"

# Apply only if plan looks correct
terraform apply -var-file="terraform.tfvars" -auto-approve
```

**Red Flags:** Destroying unintended resources, excessive changes (>10 when modifying 1 file), or secrets in state

---

### 7. Post-Push Monitoring

**IMMEDIATELY after `git push`:**

1. **Open GitHub Actions:** https://github.com/juliangdeveloper/cat-house/actions
2. **Wait 10-30 seconds** for workflow to appear
3. **Verify the correct workflow started** (check commit SHA matches)
4. **Monitor for errors** in the first 2 minutes

**Timeline:** Backend CI (3-5m) → Build Images (6-7m) → Deploy Staging (3-4m) = **12-16m total**

**If nothing starts after 1 minute:** Check path filters match your changes (see section 2)

---

### 8. Deployment Verification

**After Deploy to Staging completes:**

```bash
# ALB health check (should return 200 OK)
curl http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com/health

# Individual service health checks
curl http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com/api/v1/auth/health
curl http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com/api/v1/catalog/health
curl http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com/api/v1/installation/health
curl http://cat-house-staging-alb-1968126506.sa-east-1.elb.amazonaws.com/api/v1/proxy/health

# CloudFront frontend (should return HTML)
curl https://d1vmti7es7a518.cloudfront.net
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "environment": "staging"
}
```

**If 503:** Wait 1-2 minutes for tasks to start, then check ECS console/CloudWatch logs

---

### 9. Emergency Rollback

```bash
# Revert commit
git revert <bad-commit-sha>
git push origin develop

# OR redeploy previous version via GitHub Actions → Deploy to Production → Re-run jobs
```

---

### 10. Debug Checklist

**Workflow failing:**
1. Read the FULL error message in the failed step
2. Linting error → run black/pylint locally
3. Secrets error → verify GitHub secrets exist
4. Dependency error → update requirements.txt

**Deployment not working:**
1. Check ECS console for task status and CloudWatch logs
2. Verify Docker images exist in ECR with correct tags
3. Verify target group health checks are passing

---

## Pre-Push Quick Reference

```bash
# 1. Run tests (see section 1 for details)
cd cat-house-backend
foreach ($s in @("auth-service", "catalog-service", "installation-service", "proxy-service")) {
  cd $s; if (Test-Path "tests") { pytest tests/ -v }; cd ..
}

# 2. Format & lint (see section 2 for details)
foreach ($s in @("auth-service", "catalog-service", "installation-service", "proxy-service")) {
  cd $s; black app/; pylint app/ --max-line-length=100 --disable=C,W0621,W0613,E1101,W0122,R1715,R0903; cd ..
}

# 3. Verify & push
git branch --show-current  # Should be 'develop'
git status                 # Changes must be in cat-house-backend/** or frontend/**
git push origin develop

# 4. Monitor: https://github.com/juliangdeveloper/cat-house/actions (should start within 30s)
```
