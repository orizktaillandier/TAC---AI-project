[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
# Comprehensive Automotive Dealer Classifier Test Suite
param(
    [string]$ApiUrl = "http://127.0.0.1:8090",
    [switch]$AutoPush = $false,
    [switch]$Verbose = $false
)

# Test cases based on real dealer/rep data
$testCases = @(
    @{
        name = "Clear Rep + Dealer ID (Alexandra)"
        subject = "Inventory Sync Issues at Honda Victoriaville"
        content = "Hi team, Alexandra Biron here from Honda Victoriaville (dealer 2806). Our new vehicle feed stopped updating yesterday around 3pm. No new inventory is showing on AutoTrader. Can you investigate?"
        from_email = "a.biron@hondavictoriaville.com"
        oem = "Honda"
        expected_rep = "Alexandra Biron"
        expected_dealer_id = "2806"
        expected_dealer_name = "honda victoriaville"
        category = "CLEAR_MATCH"
    },
    @{
        name = "French Rep with Encoding"
        subject = "Problème avec Chevrolet Méga Centre"
        content = "Bonjour, c'est Véronique Fournier de St-Georges Chevrolet et Méga Centre. Nous avons un problème avec la synchronisation des prix. Le dealer ID est 2166. Merci de votre aide."
        from_email = "f.giguere@sgchevrolet.ca"
        oem = "Chevrolet"
        expected_rep = "Véronique Fournier"
        expected_dealer_id = "2166"
        expected_dealer_name = "st-georges chevrolet"
        category = "ENCODING_TEST"
    },
    @{
        name = "Rep Name Only (Multiple Dealers)"
        subject = "Website Logo Update"
        content = "From Taylor Moore: Need to update our dealership logo across all platforms. The current one is outdated and doesn't match our new branding guidelines."
        from_email = "t.moore@dealer.com"
        oem = ""
        expected_rep = "Taylor Moore"
        expected_dealer_id = $null
        expected_dealer_name = $null
        category = "AMBIGUOUS_MULTIPLE"
    },
    @{
        name = "Partial Dealer Name + Geographic"
        subject = "Service Integration Down"
        content = "The Subaru dealer in Levis is having issues with service appointment booking. Customers can't schedule online. Please check integration status."
        from_email = "support@subaru-levis.com"
        oem = "Subaru"
        expected_rep = "Véronique Fournier"
        expected_dealer_id = "99"
        expected_dealer_name = "levis subaru"
        category = "GEOGRAPHIC_MATCH"
    },
    @{
        name = "Dealer ID in Context (Jaguar)"
        subject = "PA Code Application Request"
        content = "Hi, we need to apply the same promotional pricing code to dealer 3052 as was used for the Toronto region campaign. This is for the Jaguar location in Thornhill."
        from_email = "promo@jaguar-thornhill.com"
        oem = "Jaguar"
        expected_rep = "Taylor Moore"
        expected_dealer_id = "3052"
        expected_dealer_name = "jaguar thornhill"
        category = "ID_CONTEXT_MATCH"
    },
    @{
        name = "No Clear Dealer Info"
        subject = "API Documentation Request"
        content = "Can someone send me the latest API documentation for inventory uploads? We're implementing a new DMS system and need the current specs."
        from_email = "tech@unknowndealer.com"
        oem = ""
        expected_rep = $null
        expected_dealer_id = $null
        expected_dealer_name = $null
        category = "NO_MATCH"
    },
    @{
        name = "Email Signature Format (KIA)"
        subject = "Photo Upload Issues"
        content = "Vehicle photos aren't displaying properly on our listings. Best regards, Sarah Mitchell, Uptown KIA | Dealer ID: 3244 | Phone: 613-555-0199"
        from_email = "s.mitchell@uptownkia.com"
        oem = "KIA"
        expected_rep = "Taylor Moore"
        expected_dealer_id = "3244"
        expected_dealer_name = "uptown kia"
        category = "SIGNATURE_MATCH"
    },
    @{
        name = "Multiple Alexandra Ford Dealers"
        subject = "Ford Direct Integration Problems"
        content = "Multiple Ford dealers are reporting the same issue: Olivier Ford St-Hubert (4620), Perron Ford (3299), and Beauce Auto Ford (2184). All experiencing delayed inventory updates since the weekend maintenance."
        from_email = "support@ford-regional.com"
        oem = "Ford"
        expected_rep = "Alexandra Biron"
        expected_dealer_id = "4620"  # Should pick first mentioned
        expected_dealer_name = "olivier ford st-hubert"
        category = "MULTI_DEALER"
    },
    @{
        name = "Direct Dealer Name Match"
        subject = "Service Appointment Integration"
        content = "The service booking system at Sterling Honda isn't working. Customers can't schedule appointments online. Need immediate assistance."
        from_email = "service@sterlinghonda.com"
        oem = "Honda"
        expected_rep = "Taylor Moore"
        expected_dealer_id = "3169"
        expected_dealer_name = "sterling honda"
        category = "DIRECT_NAME_MATCH"
    },
    @{
        name = "Complex Case - Belliveau (Base Location Preference)"
        subject = "Employee Pricing Issues"
        content = "Hey team, Evan Walsh from Belliveau Ford. We're having the same pricing issue as discussed for dealer 4119. Can you apply the PA code from 3842? Thanks."
        from_email = "e.walsh@bellivetumotors.com"
        oem = "Ford"
        expected_rep = "Evan Walsh"
        expected_dealer_id = "3842"  # Should prefer base location over variants
        expected_dealer_name = "belliveau motors ford"
        category = "BASE_LOCATION_PREFERENCE"
    }
)

function Test-DealerClassifier {
    Write-Host "=== AUTOMOTIVE DEALER CLASSIFIER TEST SUITE ===" -ForegroundColor Cyan
    Write-Host "Testing $($testCases.Length) scenarios against dealer matching logic" -ForegroundColor Gray
    Write-Host "API Endpoint: $ApiUrl" -ForegroundColor Gray
    Write-Host ""
    
    $results = @()
    $passCount = 0
    $failCount = 0
    $errorCount = 0
    
    foreach ($test in $testCases) {
        Write-Host "[$($testCases.IndexOf($test) + 1)/$($testCases.Length)] Testing: $($test.name)" -ForegroundColor Yellow
        if ($Verbose) {
            Write-Host "  Subject: $($test.subject)" -ForegroundColor Gray
            Write-Host "  Category: $($test.category)" -ForegroundColor Gray
        }
        
        try {
            # Create test request
            $body = @{
                subject = $test.subject
                content = $test.content
                from_email = $test.from_email
                oem = $test.oem
            } | ConvertTo-Json -Depth 3
            
            # Make API request
            $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/test-classify" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
            
            if ($response.error) {
                Write-Host "  ? API Error: $($response.error)" -ForegroundColor Red
                $errorCount++
                continue
            }
            
            # Analyze results
            $classification = $response.classification
            $dealerMatch = $true
            $repMatch = $true
            $issues = @()
            
            # Check dealer ID matching
            if ($test.expected_dealer_id -and $classification.dealer_id -ne $test.expected_dealer_id) {
                $dealerMatch = $false
                $issues += "Dealer ID: Expected '$($test.expected_dealer_id)', Got '$($classification.dealer_id)'"
            } elseif (-not $test.expected_dealer_id -and $classification.dealer_id) {
                # Unexpected match - might be acceptable
                if ($Verbose) { Write-Host "  ??  Unexpected dealer ID found: $($classification.dealer_id)" -ForegroundColor Blue }
            }
            
            # Check rep matching
            if ($test.expected_rep -and $classification.rep -ne $test.expected_rep) {
                $repMatch = $false
                $issues += "Rep: Expected '$($test.expected_rep)', Got '$($classification.rep)'"
            } elseif (-not $test.expected_rep -and $classification.rep) {
                if ($Verbose) { Write-Host "  ??  Unexpected rep found: $($classification.rep)" -ForegroundColor Blue }
            }
            
            # Display results
            $testResult = $dealerMatch -and $repMatch
            
            if ($testResult) {
                $passCount++
                Write-Host "  ? PASS" -ForegroundColor Green
                if ($Verbose) {
                    Write-Host "    Rep: $($classification.rep)" -ForegroundColor Green
                    Write-Host "    Dealer: $($classification.dealer_name) ($($classification.dealer_id))" -ForegroundColor Green
                }
            } else {
                $failCount++
                Write-Host "  ? FAIL" -ForegroundColor Red
                foreach ($issue in $issues) {
                    Write-Host "    $issue" -ForegroundColor Red
                }
            }
            
            # Show AI classification results
            if ($Verbose -and ($classification.category -or $classification.sub_category)) {
                Write-Host "    AI: $($classification.category) > $($classification.sub_category)" -ForegroundColor Cyan
            }
            
            $results += @{
                test = $test.name
                category = $test.category
                passed = $testResult
                dealer_id_actual = $classification.dealer_id
                dealer_id_expected = $test.expected_dealer_id
                rep_actual = $classification.rep
                rep_expected = $test.expected_rep
                ai_category = $classification.category
                ai_sub_category = $classification.sub_category
                issues = $issues
            }
            
        } catch {
            Write-Host "  ? Request Error: $($_.Exception.Message)" -ForegroundColor Red
            $errorCount++
            
            $results += @{
                test = $test.name
                passed = $false
                error = $_.Exception.Message
            }
        }
        
        if (-not $Verbose) { Start-Sleep -Milliseconds 500 }  # Brief pause for readability
    }
    
    # Summary Report
    Write-Host ""
    Write-Host "=== TEST RESULTS SUMMARY ===" -ForegroundColor Cyan
    Write-Host "Total Tests: $($testCases.Length)" -ForegroundColor White
    Write-Host "Passed: $passCount" -ForegroundColor Green
    Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Errors: $errorCount" -ForegroundColor $(if ($errorCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Success Rate: $(($passCount / ($testCases.Length - $errorCount) * 100).ToString('F1'))%" -ForegroundColor $(if ($passCount -eq ($testCases.Length - $errorCount)) { "Green" } else { "Yellow" })
    
    # Category Analysis
    Write-Host ""
    Write-Host "=== RESULTS BY CATEGORY ===" -ForegroundColor Cyan
    $categoryResults = $results | Where-Object { $_.category } | Group-Object category
    foreach ($category in $categoryResults) {
        $passed = ($category.Group | Where-Object { $_.passed }).Count
        $total = $category.Group.Count
        $rate = if ($total -gt 0) { ($passed / $total * 100).ToString('F0') } else { "0" }
        
        $color = if ($passed -eq $total) { "Green" } elseif ($passed -eq 0) { "Red" } else { "Yellow" }
        Write-Host "$($category.Name): $passed/$total ($rate%)" -ForegroundColor $color
    }
    
    # Failure Details
    if ($failCount -gt 0) {
        Write-Host ""
        Write-Host "=== FAILURE ANALYSIS ===" -ForegroundColor Red
        $failures = $results | Where-Object { -not $_.passed -and -not $_.error }
        foreach ($failure in $failures) {
            Write-Host "$($failure.test) [$($failure.category)]:" -ForegroundColor Yellow
            foreach ($issue in $failure.issues) {
                Write-Host "  $issue" -ForegroundColor Red
            }
        }
    }
    
    return $results
}

# Export results to CSV for analysis
function Export-TestResults {
    param($results, $filename = "classifier_test_results.csv")
    
    $results | Export-Csv -Path $filename -NoTypeInformation
    Write-Host "Test results exported to: $filename" -ForegroundColor Green
}

Write-Host @"
=== USAGE INSTRUCTIONS ===

1. Run basic test suite:
   Test-DealerClassifier

2. Run with verbose output:
   Test-DealerClassifier -Verbose

3. Export results to CSV:
   `$results = Test-DealerClassifier
   Export-TestResults `$results

4. Test against different endpoint:
   Test-DealerClassifier -ApiUrl "http://localhost:8091"

=== RUNNING TESTS NOW ===
"@ -ForegroundColor Yellow

# Run the test suite automatically
Test-DealerClassifier -Verbose


