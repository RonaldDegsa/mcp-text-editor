# PowerShell script to run individual test functions separately
# This provides more detailed information about which specific test functions pass or fail

# Set up an array to store test results
$global:testResults = @()

# Function to extract test function names from a Python test file
function Get-TestFunctions {
    param (
        [string]$FilePath
    )
    
    $content = Get-Content -Path $FilePath -Raw
    $matches = [regex]::Matches($content, '(?<=def )test_[a-zA-Z0-9_]+\(')
    $testFunctions = $matches | ForEach-Object { $_.Value.TrimEnd('(') }
    return $testFunctions
}

# Function to run a single test function and record the result
function Run-SingleTestFunction {
    param (
        [string]$FilePath,
        [string]$TestFunction
    )
    
    $testIdentifier = "$FilePath::$TestFunction"
    Write-Host "Running test: $testIdentifier" -ForegroundColor Yellow
    $startTime = Get-Date
    
    # Run the test using pytest
    pytest $testIdentifier -v
    $exitCode = $LASTEXITCODE
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    # Store the test result
    $global:testResults += [PSCustomObject]@{
        TestFile = $FilePath
        TestFunction = $TestFunction
        Status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
        Duration = [math]::Round($duration, 2)
        ExitCode = $exitCode
    }
    
    # Display immediate result
    if ($exitCode -eq 0) {
        Write-Host "PASS: $TestFunction ($duration seconds)" -ForegroundColor Green
    } else {
        Write-Host "FAIL: $TestFunction ($duration seconds)" -ForegroundColor Red
    }
    
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    
    # Return the status for counting
    return ($exitCode -eq 0)
}

# Get all test files
Write-Host "Finding all test files..." -ForegroundColor Cyan
$testFiles = Get-ChildItem -Path "tests" -Filter "test_*.py" -Recurse | ForEach-Object { $_.FullName }
Write-Host "Found $($testFiles.Count) test files" -ForegroundColor Cyan

# Initialize counters
$totalTests = 0
$completedTests = 0
$passedTests = 0
$failedTests = 0

# Count total test functions first
foreach ($testFile in $testFiles) {
    $testFunctions = Get-TestFunctions -FilePath $testFile
    $totalTests += $testFunctions.Count
}

Write-Host "Found a total of $totalTests test functions across all files" -ForegroundColor Cyan

# Run each test function individually
foreach ($testFile in $testFiles) {
    $testFunctions = Get-TestFunctions -FilePath $testFile
    $fileRelativePath = $testFile.Replace("$PWD\", "")
    
    Write-Host "`nProcessing file: $fileRelativePath ($($testFunctions.Count) tests)" -ForegroundColor Cyan
    
    foreach ($testFunction in $testFunctions) {
        $testResult = Run-SingleTestFunction -FilePath $fileRelativePath -TestFunction $testFunction
        $completedTests++
        
        # Update counters
        if ($testResult) {
            $passedTests++
        } else {
            $failedTests++
        }
        
        # Display progress
        $percentComplete = [math]::Round(($completedTests / $totalTests) * 100, 2)
        Write-Host "Progress: $completedTests of $totalTests tests completed ($percentComplete%)" -ForegroundColor Cyan
        Write-Host "Current Status: $passedTests passed, $failedTests failed" -ForegroundColor Cyan
    }
}

# Double-check counters match actual results
$actualPassed = ($global:testResults | Where-Object { $_.Status -eq "PASS" }).Count
$actualFailed = ($global:testResults | Where-Object { $_.Status -eq "FAIL" }).Count

if ($actualPassed -ne $passedTests -or $actualFailed -ne $failedTests) {
    Write-Host "Warning: Counter mismatch detected, using actual counts from results" -ForegroundColor Yellow
    $passedTests = $actualPassed
    $failedTests = $actualFailed
}

# Display summary
Write-Host "`nTest Summary:" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor Cyan
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor Red
Write-Host "Actual test count: $($global:testResults.Count) tests processed" -ForegroundColor Cyan

# Display detailed results by file
Write-Host "`nDetailed Test Results by File:" -ForegroundColor Cyan
$fileGroupResults = $global:testResults | Group-Object -Property TestFile

foreach ($fileGroup in $fileGroupResults) {
    $filePassed = ($fileGroup.Group | Where-Object { $_.Status -eq "PASS" }).Count
    $fileFailed = ($fileGroup.Group | Where-Object { $_.Status -eq "FAIL" }).Count
    $fileStatus = if ($fileFailed -eq 0) { "PASS" } else { "FAIL" }
    $statusColor = if ($fileStatus -eq "PASS") { "Green" } else { "Red" }
    
    Write-Host "File: $($fileGroup.Name) - $fileStatus ($filePassed passed, $fileFailed failed)" -ForegroundColor $statusColor
    
    if ($fileFailed -gt 0) {
        Write-Host "  Failed tests:" -ForegroundColor Yellow
        foreach ($test in ($fileGroup.Group | Where-Object { $_.Status -eq "FAIL" })) {
            Write-Host "  - $($test.TestFunction)" -ForegroundColor Red
        }
    }
}

# Save results to a CSV file with absolute path
$csvPath = "$(Get-Location)\test_function_results_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').csv"
try {
    $global:testResults | Export-Csv -Path $csvPath -NoTypeInformation -Force
    Write-Host "`nResults saved to CSV: $csvPath" -ForegroundColor Green
}
catch {
    Write-Error "Failed to save CSV file: $_"
}

# Output failed tests for easy rerun
if ($failedTests -gt 0) {
    Write-Host "`nFailed tests (copy these commands to rerun individual failures):" -ForegroundColor Yellow
    foreach ($test in ($global:testResults | Where-Object { $_.Status -eq "FAIL" })) {
        Write-Host "pytest $($test.TestFile)::$($test.TestFunction) -v" -ForegroundColor Yellow
    }
}