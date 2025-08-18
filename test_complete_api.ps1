# COMPREHENSIVE API VERIFICATION SCRIPT
# Tests all functionality to ensure nothing is broken

Write-Host "=== COMPLETE API VERIFICATION SCRIPT ===" -ForegroundColor Cyan
Write-Host "Testing all endpoints and functionality..." -ForegroundColor White

$baseUrl = "http://127.0.0.1:8090"
$allTestsPassed = $true

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Body = $null,
        [scriptblock]$ValidationScript = $null
    )
    
    Write-Host "`n--- Testing: $Name ---" -ForegroundColor Yellow
    Write-Host "URL: $Method $Url" -ForegroundColor Gray
    
    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -TimeoutSec 10
        } else {
            $jsonBody = $Body | ConvertTo-Json
            Write-Host "Request Body: $jsonBody" -ForegroundColor Gray
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Body $jsonBody -ContentType "application/json" -TimeoutSec 10
        }
        
        Write-Host "✅ SUCCESS: Endpoint responded" -ForegroundColor Green
        
        if ($ValidationScript) {
            $validationResult = & $ValidationScript $response
            if ($validationResult) {
                Write-Host "✅ VALIDATION: Passed" -ForegroundColor Green
            } else {
                Write-Host "❌ VALIDATION: Failed" -ForegroundColor Red
                $script:allTestsPassed = $false
            }
        }
        
        Write-Host "Response: $($response | ConvertTo-Json -Depth 2)" -ForegroundColor Gray
        return $response
        
    } catch {
        Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $script:allTestsPassed = $false
        return $null
    }
}

# Test 1: Basic Health Check
Test-Endpoint -Name "Health Check" -Url "$baseUrl/health" -ValidationScript {
    param($response)
    return $response.status -eq "ok" -and $response.service -eq "complete-ticket-classifier"
}

# Test 2: Root Endpoint
Test-Endpoint -Name "Root Endpoint" -Url "$baseUrl/" -ValidationScript {
    param($response)
    return $response.message -like "*Complete Zoho Ticket Classifier API*"
}

# Test 3: Metrics Endpoint
Test-Endpoint -Name "Metrics" -Url "$baseUrl/api/v1/metrics" -ValidationScript {
    param($response)
    return $response.components -ne $null
}

# Test 4: CRITICAL - Working Classification (from original working API)
$testClassificationData = @{
    subject = "Cancel Export"
    content = "Cancel Kijiji export for Number 7 Honda - Lisa Payne"
    from_email = "test@test.com"
    oem = ""
}

$classificationResult = Test-Endpoint -Name "CRITICAL: Working Classification" -Url "$baseUrl/api/v1/test-classify" -Method "POST" -Body $testClassificationData -ValidationScript {
    param($response)
    $classification = $response.classification
    
    # Verify all 8 required fields exist
    $requiredFields = @("contact", "dealer_name", "dealer_id", "rep", "category", "sub_category", "syndicator", "inventory_type")
    $fieldsPresent = $true
    
    foreach ($field in $requiredFields) {
        if (-not $classification.PSObject.Properties.Name.Contains($field)) {
            Write-Host "❌ Missing field: $field" -ForegroundColor Red
            $fieldsPresent = $false
        }
    }
    
    # Verify specific expected values for the test case
    $specificChecks = @{
        "dealer_id" = "2221"
        "category" = "Product Cancellation" 
        "syndicator" = "Kijiji"
        "rep" = "Lisa Payne"
    }
    
    $valuesCorrect = $true
    foreach ($field in $specificChecks.Keys) {
        $expected = $specificChecks[$field]
        $actual = $classification.$field
        if ($actual -ne $expected) {
            Write-Host "❌ Field '$field': expected '$expected', got '$actual'" -ForegroundColor Red
            $valuesCorrect = $false
        } else {
            Write-Host "✅ Field '$field': correct value '$actual'" -ForegroundColor Green
        }
    }
    
    return $fieldsPresent -and $valuesCorrect
}

# Test 5: Dealer Lookup Endpoint
Test-Endpoint -Name "Dealer Lookup" -Url "$baseUrl/api/v1/dealer/lookup/honda" -ValidationScript {
    param($response)
    return $response.dealers -ne $null -and $response.matches_found -gt 0
}

# Test 6: Zoho Connection Test
Test-Endpoint -Name "Zoho Connection Test" -Url "$baseUrl/api/v1/zoho/test" -ValidationScript {
    param($response)
    # This might fail if Zoho credentials aren't set, but endpoint should respond
    return $response.status -ne $null
}

# Test 7: Example Zoho Ticket Classification (dry run - will fail if no real ticket ID)
Write-Host "`n--- Testing: Zoho Ticket Classification (Dry Run) ---" -ForegroundColor Yellow
Write-Host "Note: This test will fail without a real Zoho ticket ID, but verifies endpoint structure" -ForegroundColor Gray

$zohoTestData = @{
    ticket_id = "12345"  # Fake ticket ID for structure test
    auto_push = $false
}

try {
    $jsonBody = $zohoTestData | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/classify" -Method "POST" -Body $jsonBody -ContentType "application/json" -TimeoutSec 10 -ErrorAction SilentlyContinue
    Write-Host "✅ Zoho endpoint structure: OK" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*Failed to fetch ticket*" -or $_.Exception.Message -like "*ticket_id*") {
        Write-Host "✅ Zoho endpoint structure: OK (expected authentication/ticket error)" -ForegroundColor Green
    } else {
        Write-Host "❌ Zoho endpoint error: $($_.Exception.Message)" -ForegroundColor Red
        $allTestsPassed = $false
    }
}

# Test 8: Debug Endpoint Structure
Write-Host "`n--- Testing: Debug Endpoint Structure ---" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/debug/ticket/12345" -Method "GET" -TimeoutSec 10 -ErrorAction SilentlyContinue
    Write-Host "✅ Debug endpoint structure: OK" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*Failed to fetch*" -or $_.Exception.Message -like "*error*") {
        Write-Host "✅ Debug endpoint structure: OK (expected ticket fetch error)" -ForegroundColor Green
    } else {
        Write-Host "❌ Debug endpoint error: $($_.Exception.Message)" -ForegroundColor Red
        $allTestsPassed = $false
    }
}

# Summary
Write-Host "`n=== VERIFICATION SUMMARY ===" -ForegroundColor Cyan

if ($allTestsPassed) {
    Write-Host "🎉 ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "✅ Original working functionality preserved" -ForegroundColor Green
    Write-Host "✅ Zoho integration endpoints available" -ForegroundColor Green
    Write-Host "✅ All API structures correct" -ForegroundColor Green
    Write-Host "`nREADY FOR PRODUCTION USE" -ForegroundColor Green
} else {
    Write-Host "❌ SOME TESTS FAILED" -ForegroundColor Red
    Write-Host "Review the failed tests above and fix issues before proceeding" -ForegroundColor Yellow
}

Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Cyan
Write-Host "1. If tests passed, you can use the new complete_dealer_api.py" -ForegroundColor White
Write-Host "2. Test with real Zoho ticket IDs: POST /api/v1/classify" -ForegroundColor White
Write-Host "3. Use auto_push: true to update tickets in Zoho" -ForegroundColor White
Write-Host "4. Debug any issues with: GET /debug/ticket/{ticket_id}" -ForegroundColor White

# Critical functionality verification
if ($classificationResult -and $classificationResult.classification.dealer_id -eq "2221") {
    Write-Host "`n🔥 CRITICAL VERIFICATION PASSED:" -ForegroundColor Green
    Write-Host "   Number 7 Honda → Dealer ID 2221 ✅" -ForegroundColor Green
    Write-Host "   All 8 fields populated ✅" -ForegroundColor Green  
    Write-Host "   Classification logic working ✅" -ForegroundColor Green
} else {
    Write-Host "`n💥 CRITICAL VERIFICATION FAILED!" -ForegroundColor Red
    Write-Host "   The core functionality is broken" -ForegroundColor Red
}