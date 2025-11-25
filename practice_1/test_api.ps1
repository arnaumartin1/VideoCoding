# PowerShell test script for FastAPI endpoints

Write-Host "`n=== Testing FastAPI Video Encoding API ===" -ForegroundColor Green

# Test 1: Health check
Write-Host "`n1. Testing Health Check..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method GET
    Write-Host "✓ API is running: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test 2: RGB to YUV conversion
Write-Host "`n2. Testing RGB to YUV Conversion (Red color)..." -ForegroundColor Cyan
try {
    $body = @{
        R = 255
        G = 0
        B = 0
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/convert/rgb_to_yuv/" -Method POST -Body $body -ContentType "application/json"
    Write-Host "✓ RGB(255,0,0) -> YUV($($response.Y),$($response.U),$($response.V))" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test 3: YUV to RGB conversion
Write-Host "`n3. Testing YUV to RGB Conversion..." -ForegroundColor Cyan
try {
    $body = @{
        Y = 82
        U = 90
        V = 240
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/convert/yuv_to_rgb/" -Method POST -Body $body -ContentType "application/json"
    Write-Host "✓ YUV(82,90,240) -> RGB($($response.R),$($response.G),$($response.B))" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Tests Complete ===" -ForegroundColor Green
Write-Host "`nTo test file upload endpoints (resize/convert), use the Swagger UI at:" -ForegroundColor Yellow
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
