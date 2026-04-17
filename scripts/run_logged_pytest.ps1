param(
    [string]$Label = "pytest",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = "logs/test-runs"
$logPath = Join-Path $logDir "$Label-$timestamp.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$hasWorkerArg = $false
foreach ($arg in $PytestArgs) {
    if ($arg -eq "-n" -or $arg -eq "--numprocesses" -or $arg -like "--numprocesses=*") {
        $hasWorkerArg = $true
        break
    }
}

$defaultPytestArgs = @("-vv")
if (-not $hasWorkerArg) {
    $workerCount = [Math]::Min([Environment]::ProcessorCount, 16)
    if ($workerCount -lt 1) {
        $workerCount = 1
    }
    $defaultPytestArgs += @("-n", [string]$workerCount, "--dist", "worksteal")
}

$uvArgs = @("run", "pytest") + $defaultPytestArgs + $PytestArgs
$quotedArgs = foreach ($arg in $uvArgs) {
    if ($arg -match '[\s"]') {
        '"' + ($arg -replace '"', '\"') + '"'
    }
    else {
        $arg
    }
}
$uvCommand = "uv " + ($quotedArgs -join " ")
cmd.exe /d /c "$uvCommand 2>&1" | Tee-Object -FilePath $logPath
$exitCode = $LASTEXITCODE

Write-Output "LOG_PATH=$logPath"
exit $exitCode
