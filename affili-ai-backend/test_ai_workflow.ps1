# Test Task Creation for AI Agent
# This script creates a test task to verify the AI agent workflow

$taskData = @{
    task_type = "APPLY_PROGRAM"
    payload = @{
        program_id = "test-program-123"
        program_name = "Test Affiliate Program"
        application_url = "https://example.com/affiliate/apply"
        prefill_data = @{
            company_name = "Test Company Inc"
            website = "https://testcompany.com"
            email = "test@testcompany.com"
            name = "John Doe"
        }
    }
    agent_pool = "default"
    max_retries = 3
} | ConvertTo-Json -Depth 5

Write-Host "Creating test task..." -ForegroundColor Cyan
Write-Host "Task Data:" -ForegroundColor Yellow
Write-Host $taskData

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks" `
        -Method POST `
        -Body $taskData `
        -ContentType "application/json" `
        -ErrorAction Stop

    Write-Host "`nTask created successfully!" -ForegroundColor Green
    Write-Host "Task ID: $($response.id)" -ForegroundColor Cyan
    Write-Host "Status: $($response.status)" -ForegroundColor Cyan
    Write-Host "Type: $($response.task_type)" -ForegroundColor Cyan
    
    # Wait a few seconds and check task status
    Write-Host "`nWaiting 5 seconds for agent to pick up task..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host "Checking task status..." -ForegroundColor Cyan
    $taskStatus = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks/$($response.id)" -Method GET
    
    Write-Host "`nCurrent Task Status:" -ForegroundColor Green
    Write-Host "Status: $($taskStatus.status)" -ForegroundColor Cyan
    Write-Host "Agent ID: $($taskStatus.agent_id)" -ForegroundColor Cyan
    Write-Host "Created: $($taskStatus.created_at)" -ForegroundColor Cyan
    if ($taskStatus.claimed_at) {
        Write-Host "Claimed: $($taskStatus.claimed_at)" -ForegroundColor Green
    }
    if ($taskStatus.started_at) {
        Write-Host "Started: $($taskStatus.started_at)" -ForegroundColor Green
    }
    
} catch {
    Write-Host "`nError creating task:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
}
