# Test Slack Alerts via AWS Chatbot
# Sends test messages to SNS topics configured with AWS Chatbot

$region = "sa-east-1"
$criticalTopicArn = "arn:aws:sns:sa-east-1:578492750346:cat-house-staging-critical-alerts"
$warningTopicArn = "arn:aws:sns:sa-east-1:578492750346:cat-house-staging-warning-alerts"

Write-Host "Testing Slack alerts via AWS Chatbot" -ForegroundColor Cyan
Write-Host ""

# Test 1: Critical Alert
Write-Host "Sending CRITICAL alert..." -ForegroundColor Yellow
aws sns publish `
    --topic-arn $criticalTopicArn `
    --subject "TEST: Critical Alert" `
    --message "This is a test of the critical alerts system via AWS Chatbot. A real alert would indicate a service down or severe issue." `
    --region $region

if ($LASTEXITCODE -eq 0) {
    Write-Host "Critical alert sent successfully" -ForegroundColor Green
} else {
    Write-Host "Error sending critical alert" -ForegroundColor Red
}

Write-Host ""
Start-Sleep -Seconds 2

# Test 2: Warning Alert
Write-Host "Sending WARNING alert..." -ForegroundColor Yellow
aws sns publish `
    --topic-arn $warningTopicArn `
    --subject "TEST: Warning Alert" `
    --message "This is a test of the warning alerts system via AWS Chatbot. A real alert would indicate high CPU, latency, or other performance issues." `
    --region $region

if ($LASTEXITCODE -eq 0) {
    Write-Host "Warning alert sent successfully" -ForegroundColor Green
} else {
    Write-Host "Error sending warning alert" -ForegroundColor Red
}

Write-Host ""
Write-Host "Tests completed. Check your Slack channel #aws-alerts for messages." -ForegroundColor Cyan
Write-Host ""
Write-Host "If you don't see messages in Slack:" -ForegroundColor Yellow
Write-Host "  1. Verify AWS Chatbot configuration in AWS Console" -ForegroundColor White
Write-Host "  2. Check that SNS topics are associated with the Slack channel" -ForegroundColor White
Write-Host "  3. Ensure AWS Chatbot (Amazon Q) is authorized in your workspace" -ForegroundColor White

