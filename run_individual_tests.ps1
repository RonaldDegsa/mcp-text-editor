# PowerShell script to run each pytest test individually
# This helps identify which specific tests are passing or failing

# Set up an array to store test results
$global:testResults = @()

# Function to run a single test and record the result
function Run-SingleTest {
    param (
        [string]$TestPath
    )
    
    Write-Host "Running test: $TestPath" -ForegroundColor Yellow
    $startTime = Get-Date
    
    # Run the test using pytest
    pytest $TestPath -v
    $exitCode = $LASTEXITCODE
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    # Store the test result
    $global:testResults += [PSCustomObject]@{
        Test = $TestPath
        Status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
        Duration = [math]::Round($duration, 2)
        ExitCode = $exitCode
    }
    
    # Display immediate result
    if ($exitCode -eq 0) {
        Write-Host "PASS: $TestPath ($duration seconds)" -ForegroundColor Green
    } else {
        Write-Host "FAIL: $TestPath ($duration seconds)" -ForegroundColor Red
    }
    
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
}

# Get all test files
Write-Host "Finding all test files..." -ForegroundColor Cyan
$testFiles = Get-ChildItem -Path "tests" -Filter "test_*.py" -Recurse | ForEach-Object { $_.FullName }
Write-Host "Found $($testFiles.Count) test files" -ForegroundColor Cyan

# Initialize counters
$totalTests = $testFiles.Count
$completedTests = 0
$passedTests = 0
$failedTests = 0

# Run each test file individually
foreach ($testFile in $testFiles) {
    Run-SingleTest -TestPath $testFile
    $completedTests++
    
    # Update counters
    if ($global:testResults[-1].Status -eq "PASS") {
        $passedTests++
    } else {
        $failedTests++
    }
    
    # Display progress
    $percentComplete = [math]::Round(($completedTests / $totalTests) * 100, 2)
    Write-Host "Progress: $completedTests of $totalTests tests completed ($percentComplete%)" -ForegroundColor Cyan
    Write-Host "Current Status: $passedTests passed, $failedTests failed" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
}

# Display summary
Write-Host "`nTest Summary:" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor Cyan
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor Red

# Display detailed results
Write-Host "`nDetailed Test Results:" -ForegroundColor Cyan
$global:testResults | Sort-Object -Property Status | Format-Table -Property Test, Status, Duration, ExitCode -AutoSize

# Save results to a CSV file with full path
$csvPath = "$(Get-Location)\test_results_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').csv"
try {
    $global:testResults | Export-Csv -Path $csvPath -NoTypeInformation -Force
    Write-Host "Results saved to CSV: $csvPath" -ForegroundColor Green
}
catch {
    Write-Error "Failed to save CSV file: $_"
}

# To run individual tests within files (like specific test functions)
Write-Host "`nTo run a specific test function, use:" -ForegroundColor Yellow
Write-Host "pytest tests/test_file.py::test_function_name -v" -ForegroundColor Yellow