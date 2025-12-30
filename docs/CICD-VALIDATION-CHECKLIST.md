# CI/CD Validation Checklist

## Pre-Push Validation (MANDATORY - NO EXCEPTIONS)

### 1. Code Quality Checks
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

### 2. Workflow Trigger Validation

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

### 3. Workflow Syntax Validation

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

### 4. Secrets Validation

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

### 5. Terraform State Validation

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

**Red Flags:**
- Destroying resources you didn't intend to remove
- More than 10 resources changing when you only modified 1 file
- Secrets appearing in terraform state (they should NOT be there)

---

### 6. Post-Push Monitoring

**IMMEDIATELY after `git push`:**

1. **Open GitHub Actions:** https://github.com/juliangdeveloper/cat-house/actions
2. **Wait 10-30 seconds** for workflow to appear
3. **Verify the correct workflow started** (check commit SHA matches)
4. **Monitor for errors** in the first 2 minutes

**Expected Timeline:**
- Backend CI: ~3-5 minutes
- Build Images: ~6-7 minutes (starts after Backend CI ✅)
- Deploy Staging: ~3-4 minutes (starts after Build Images ✅)
- **Total: 12-16 minutes**

**If nothing appears after 1 minute:**
- ❌ Path filter didn't match (you need to modify a file in the right directory)
- ❌ Workflow file has syntax error (check Actions tab for parsing errors)
- ❌ Branch name is wrong (check you're on `develop` branch)

---

### 7. Deployment Verification

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

**If 503 Service Unavailable:**
- ECS tasks are still starting (wait 1-2 minutes)
- Check ECS console for task errors
- Check CloudWatch logs for application errors

---

### 8. Common Mistakes to Avoid

❌ **NEVER DO THIS:**
- Push without running black/pylint locally
- Commit workflow changes without validating YAML syntax
- Assume commit will trigger workflows (always verify path filters)
- Push to main branch directly (use develop → PR → main)
- Run `terraform apply` without reviewing `terraform plan` output
- Ignore workflow failures (fix them immediately)

✅ **ALWAYS DO THIS:**
- Run black and pylint before every commit
- Verify path filters match your changes
- Monitor GitHub Actions after every push
- Review terraform plan before apply
- Test health checks after deployment
- Read error messages completely before asking for help

---

### 9. Emergency Rollback

**If deployment breaks production:**

```bash
# Option 1: Revert commit
git revert <bad-commit-sha>
git push origin develop

# Option 2: Redeploy previous version
# Go to GitHub Actions → Deploy to Production → Re-run jobs (select previous successful run)

# Option 3: Terraform rollback
cd cat-house-backend/terraform
terraform plan -var-file="terraform.tfvars"  # Review what will change
terraform apply -var-file="terraform.tfvars"  # Apply previous state
```

---

### 10. Debug Checklist

**Workflow not triggering:**
1. ✅ Check branch name: `git branch --show-current` (should be `develop`)
2. ✅ Check path filter: Did you modify files in `cat-house-backend/**`?
3. ✅ Check GitHub Actions tab for parsing errors
4. ✅ Wait 60 seconds (GitHub Actions can be slow)

**Workflow failing:**
1. ✅ Click on the failed job
2. ✅ Expand the failed step
3. ✅ Read the FULL error message (don't skip lines)
4. ✅ Check if it's a linting error (run black/pylint locally)
5. ✅ Check if it's a secrets error (verify GitHub secrets exist)
6. ✅ Check if it's a dependency error (update requirements.txt)

**Deployment not working:**
1. ✅ Check ECS console for task status
2. ✅ Check CloudWatch logs for errors
3. ✅ Verify Docker images exist in ECR with correct tags
4. ✅ Verify secrets are injected correctly (check ECS task definition)
5. ✅ Verify target group health checks are passing

---

## Summary: Before Every Push

```bash
# 1. Format code
cd cat-house-backend
foreach ($s in @("auth-service", "catalog-service", "installation-service", "proxy-service")) {
  cd $s; black app/; cd ..
}

# 2. Check linting
foreach ($s in @("auth-service", "catalog-service", "installation-service", "proxy-service")) {
  cd $s
  pylint app/ --max-line-length=100 --disable=C,W0621,W0613,E1101,W0122,R1715,R0903
  cd ..
}

# 3. Verify branch
git branch --show-current  # Should be 'develop'

# 4. Check changes are in correct path
git status  # Should show files in cat-house-backend/** or frontend/**

# 5. Commit and push
git add .
git commit -m "descriptive message"
git push origin develop

# 6. Monitor GitHub Actions
# Open https://github.com/juliangdeveloper/cat-house/actions
# Wait for Backend CI to start (should appear within 30 seconds)
```

**If Backend CI doesn't start within 60 seconds → your changes didn't match path filters.**
