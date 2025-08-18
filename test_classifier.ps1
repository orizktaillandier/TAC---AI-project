# Automotive Ticket Classifier Test Suite
# Tests 10 diverse scenarios against the dealer matching and classification system

$testCases = @(
    @{
        name = "Clear Rep + Dealer ID"
        subject = "Inventory Sync Issues at Honda Victoriaville"
        content = "Hi team, Alexandra Biron here from Honda Victoriaville (dealer 2806). Our new vehicle feed stopped updating yesterday around 3pm. No new inventory is showing on AutoTrader. Can you investigate?"
        from_email = "a.biron@hondavictoriaville.com"
        expected_rep = "Alexandra Biron"
        expected_dealer_id = "2806"
        expected_dealer_name = "honda victoriaville"
    },
    @{
        name = "French Rep with Encoding Issues"
        subject = "Problème avec Chevrolet Méga Centre"
        content = "Bonjour, c'est Frédéric Giguere de St-Georges Chevrolet et Méga Centre. Nous avons un problème avec la synchronisation des prix. Le dealer ID est 2166. Merci de votre aide."
        from_email = "f.giguere@sgchevrolet.ca"
        expected_rep = "Frédéric Giguere"
        expected_dealer_id = "2166"
        expected_dealer_name = "st-georges chevrolet"
    },
    @{
        name = "Rep Name Only, Multiple Dealers"
        subject = "Website Logo Update"
        content = "From Taylor Moore: Need to update our dealership logo across all platforms. The current one is outdated and doesn't match our new branding guidelines."
        from_email = "t.moore@dealer.com"
        expected_rep = "Taylor Moore"
        expected_dealer_id = $null  # Should be ambiguous
        expected_dealer_name = $null
    },
    @{
        name = "Partial Dealer Name + Geographic"
        subject = "Service Integration Down"
        content = "The Subaru dealer in Levis is having issues with service appointment booking. Customers can't schedule online. Please check integration status."
        from_email = "support@subaru-levis.com"
        expected_rep = "Frédéric Giguere"
        expected_dealer_id = "99"
        expected_dealer_name = "levis subaru"
    },
    @{
        name = "Dealer ID in Context"
        subject = "PA Code Application Request"
        content = "Hi, we need to apply the same promotional pricing code to dealer 3052 as was used for the Toronto region campaign. This is for the Jaguar location in Thornhill."
        from_email = "promo@jaguar-thornhill.com"
        expected_rep = "Taylor Moore"
        expected_dealer_id = "3052"
        expected_dealer_name = "jaguar thornhill"
    },
    @{
        name = "No Clear Dealer Info"
        subject = "API Documentation Request"
        content = "Can someone send me the latest API documentation for inventory uploads? We're implementing a new DMS system and need the current specs."
        from_email = "tech@unknowndealer.com"
        expected_rep = $null
        expected_dealer_id = $null
        expected_dealer_name = $null
    },
    @{
        name = "Not Dealer Specific Edge Case"
        subject = "Regional Training Question"
        content = "Hi Frédéric, this is about the new syndication training for Quebec dealers. Do you have the schedule for next week's sessions?"
        from_email = "training@regional.com"
        expected_rep = "Frédéric Giguere"
        expected_dealer_id = $null  # "not dealer specific" case
        expected_dealer_name = $null
    },
    @{
        name = "Multiple Dealers Cross-Territory"
        subject = "Coordinated Launch Campaign"
        content = "We need to coordinate the new model launch across Alexandra Biron's Honda dealers (Victoriaville and Shawinigan) and Taylor Moore's Toyota locations. Launch date is March 15th."
        from_email = "marketing@autogroup.com"
        expected_rep = $null  # Ambiguous - multiple reps mentioned
        expected_dealer_id = $null
        expected_dealer_name = $null
    },
    @{
        name = "Email Signature Format"
        subject = "Photo Upload Issues"
        content = "Vehicle photos aren't displaying properly on our listings. Best regards, Sarah Mitchell, Uptown KIA | Dealer ID: 3244 | Phone: 613-555-0199"
        from_email = "s.mitchell@uptownkia.com"
        expected_rep = "Taylor Moore"  # Uptown KIA is Taylor's
        expected_dealer_id = "3244"
        expected_dealer_name = "uptown kia"
    },
    @{
        name = "Complex Multi-Ford Issue"
        subject = "Ford Direct Integration Problems"
        content = "Multiple Ford dealers are reporting the same issue: Olivier Ford St-Hubert (4620), Perron Ford (3299), and Beauce Auto Ford (2184). All experiencing delayed inventory updates since the weekend maintenance."
        from_email = "support@ford-regional.com"
        expected_rep = "Alexandra Biron"  # All three are Alexandra's Ford dealers
        expected_dealer_id = "4620"  # Should pick first mentioned or most specific
        expected_dealer_name = "olivier ford st-hubert"
    }
)

function Test-ClassifierAPI {
    param(
        [string]$apiUrl = "http://127.0.0.1:8090",
        [switch]$autoPush = $false
    )
    
    Write-Host "=== AUTOMOTIVE TICKET CLASSIFIER TEST SUITE ===" -ForegroundColor Cyan
    Write-Host "Testing $($testCases.Length) scenarios against dealer matching logic" -ForegroundColor Gray
    Write-Host ""
    
    $results = @()
    $passCount = 0
    $failCount = 0
    
    foreach ($test in $testCases) {
        Write-Host "Testing: $($test.name)" -ForegroundColor Yellow
        Write-Host "Subject: $($test.subject)" -ForegroundColor Gray
        
        # For now, we'll test using synthetic ticket IDs since we don't have a synthetic endpoint
        # In production, you'd want to create a test endpoint that accepts raw content
        
        try {
            # Create request body (using placeholder ticket ID for testing)
            $body = @{
                ticket_id = "TEST_$([System.Guid]::NewGuid().ToString().Substring(0,8))"
                auto_push = $autoPush.IsPresent
                # For testing, we'd need to modify the API to accept synthetic content
                test_mode = $true
                test_data = @{
                    subject = $test.subject
                    content = $test.content
                    from_email = $test.from_email
                }
            } | ConvertTo-Json -Depth 3
            
            # Make API request
            try {
                $response = Invoke-RestMethod -Uri "$apiUrl/api/v1/classify" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
                
                # Analyze results
                $classification = $response.classification
                $dealerMatch = $true
                $repMatch = $true
                
                # Check dealer matching
                if ($test.expected_dealer_id -and $classification.dealer_id -ne $test.expected_dealer_id) {
                    $dealerMatch = $false
                    Write-Host "  ❌ Dealer ID: Expected '$($test.expected_dealer_id)', Got '$($classification.dealer_id)'" -ForegroundColor Red
                } elseif ($test.expected_dealer_id) {
                    Write-Host "  ✅ Dealer ID: $($classification.dealer_id)" -ForegroundColor Green
                }
                
                # Check rep matching
                if ($test.expected_rep -and $classification.rep -ne $test.expected_rep) {
                    $repMatch = $false
                    Write-Host "  ❌ Rep: Expected '$($test.expected_rep)', Got '$($classification.rep)'" -ForegroundColor Red
                } elseif ($test.expected_rep) {
                    Write-Host "  ✅ Rep: $($classification.rep)" -ForegroundColor Green
                }
                
                # Show classification results
                Write-Host "  📊 Category: $($classification.category)" -ForegroundColor Cyan
                Write-Host "  📊 Sub-category: $($classification.sub_category)" -ForegroundColor Cyan
                Write-Host "  📊 Syndicator: $($classification.syndicator)" -ForegroundColor Cyan
                
                $testResult = $dealerMatch -and $repMatch
                if ($testResult) {
                    $passCount++
                    Write-Host "  ✅ PASS" -ForegroundColor Green
                } else {
                    $failCount++
                    Write-Host "  ❌ FAIL" -ForegroundColor Red
                }
                
                $results += @{
                    test = $test.name
                    passed = $testResult
                    dealer_id_actual = $classification.dealer_id
                    dealer_id_expected = $test.expected_dealer_id
                    rep_actual = $classification.rep
                    rep_expected = $test.expected_rep
                    category = $classification.category
                    sub_category = $classification.sub_category
                    response_time = 0  # Could measure this
                }
                
            } catch {
                Write-Host "  ❌ API Error: $($_.Exception.Message)" -ForegroundColor Red
                $failCount++
                
                $results += @{
                    test = $test.name
                    passed = $false
                    error = $_.Exception.Message
                }
            }
            
        } catch {
            Write-Host "  ❌ Request Error: $($_.Exception.Message)" -ForegroundColor Red
            $failCount++
        }
        
        Write-Host ""
    }
    
    # Summary
    Write-Host "=== TEST RESULTS SUMMARY ===" -ForegroundColor Cyan
    Write-Host "Total Tests: $($testCases.Length)" -ForegroundColor White
    Write-Host "Passed: $passCount" -ForegroundColor Green
    Write-Host "Failed: $failCount" -ForegroundColor Red
    Write-Host "Success Rate: $(($passCount / $testCases.Length * 100).ToString('F1'))%" -ForegroundColor $(if ($passCount -eq $testCases.Length) { "Green" } else { "Yellow" })
    Write-Host ""
    
    # Detailed failure analysis
    if ($failCount -gt 0) {
        Write-Host "=== FAILURE ANALYSIS ===" -ForegroundColor Red
        $failures = $results | Where-Object { -not $_.passed }
        foreach ($failure in $failures) {
            Write-Host "$($failure.test):" -ForegroundColor Yellow
            if ($failure.error) {
                Write-Host "  Error: $($failure.error)" -ForegroundColor Red
            } else {
                if ($failure.dealer_id_expected -ne $failure.dealer_id_actual) {
                    Write-Host "  Dealer ID mismatch: Expected '$($failure.dealer_id_expected)', Got '$($failure.dealer_id_actual)'" -ForegroundColor Red
                }
                if ($failure.rep_expected -ne $failure.rep_actual) {
                    Write-Host "  Rep mismatch: Expected '$($failure.rep_expected)', Got '$($failure.rep_actual)'" -ForegroundColor Red
                }
            }
        }
    }
    
    return $results
}

# Alternative: Test with real ticket format (create synthetic tickets)
function Create-SyntheticTickets {
    Write-Host "=== CREATING SYNTHETIC TICKET TEST DATA ===" -ForegroundColor Cyan
    
    foreach ($test in $testCases) {
        $ticketData = @{
            id = "SYNTHETIC_$([System.Guid]::NewGuid().ToString().Substring(0,12))"
            subject = $test.subject
            description = $test.content
            email = $test.from_email
            custom_fields = @{
                cf_oem = if ($test.content -match "ford|Ford") { "Ford" } 
                        elseif ($test.content -match "honda|Honda") { "Honda" }
                        elseif ($test.content -match "toyota|Toyota") { "Toyota" }
                        elseif ($test.content -match "chevrolet|Chevrolet") { "Chevrolet" }
                        elseif ($test.content -match "subaru|Subaru") { "Subaru" }
                        elseif ($test.content -match "jaguar|Jaguar") { "Jaguar" }
                        elseif ($test.content -match "kia|KIA") { "KIA" }
                        else { "" }
            }
            threads = @()
        }
        
        $filename = "synthetic_ticket_$($test.name -replace '[^a-zA-Z0-9]', '_').json"
        $ticketData | ConvertTo-Json -Depth 3 | Out-File -FilePath $filename -Encoding UTF8
        Write-Host "Created: $filename" -ForegroundColor Green
    }
}

# Usage instructions
Write-Host @"
=== USAGE INSTRUCTIONS ===

1. Run basic test suite:
   Test-ClassifierAPI

2. Run with auto-push enabled (WARNING: Will modify real tickets!):
   Test-ClassifierAPI -autoPush

3. Create synthetic ticket files for manual testing:
   Create-SyntheticTickets

4. Test against different API endpoint:
   Test-ClassifierAPI -apiUrl "http://localhost:8091"

NOTE: The current API expects real Zoho ticket IDs. For comprehensive testing,
you may need to create a test endpoint that accepts synthetic content directly.
"@ -ForegroundColor Yellow

# Run the test suite
# Test-ClassifierAPI