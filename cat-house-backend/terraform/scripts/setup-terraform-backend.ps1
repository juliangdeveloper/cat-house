$ErrorActionPreference = "Stop"

$AWS_REGION = "sa-east-1"
$BUCKET_NAME = "cat-house-terraform-state"

Write-Host "🚀 Setting up Terraform backend..." -ForegroundColor Cyan
Write-Host ""

# Crear bucket S3
Write-Host "📦 Creating S3 bucket: $BUCKET_NAME" -ForegroundColor Yellow
$bucketExists = $null
$bucketExists = aws s3api head-bucket --bucket $BUCKET_NAME 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Bucket already exists" -ForegroundColor Gray
} else {
    aws s3api create-bucket --bucket $BUCKET_NAME --region $AWS_REGION --create-bucket-configuration LocationConstraint=$AWS_REGION
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Bucket created successfully" -ForegroundColor Green
    }
}

# Habilitar versionado
Write-Host ""
Write-Host "🔄 Enabling versioning..." -ForegroundColor Yellow
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled
Write-Host "✓ Versioning enabled" -ForegroundColor Green

# Habilitar cifrado
Write-Host ""
Write-Host "🔐 Enabling encryption..." -ForegroundColor Yellow
$encryptionConfig = '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"},"BucketKeyEnabled": true}]}'
$encryptionConfig | aws s3api put-bucket-encryption --bucket $BUCKET_NAME --server-side-encryption-configuration file:///dev/stdin
Write-Host "✓ Encryption enabled" -ForegroundColor Green

# Bloquear acceso público
Write-Host ""
Write-Host "🚫 Blocking public access..." -ForegroundColor Yellow
aws s3api put-public-access-block --bucket $BUCKET_NAME --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
Write-Host "✓ Public access blocked" -ForegroundColor Green

Write-Host ""
Write-Host "✅ Terraform backend setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend configuration:" -ForegroundColor Cyan
Write-Host "  S3 Bucket: $BUCKET_NAME"
Write-Host "  Region: $AWS_REGION"
Write-Host ""
Write-Host "⚠️  Note: State locking is disabled (no DynamoDB table)" -ForegroundColor Yellow
Write-Host "   Only one person should run terraform at a time" -ForegroundColor Yellow
Write-Host ""
Write-Host "Estimated monthly cost: ~`$0.03 USD (S3 only)" -ForegroundColor Gray
