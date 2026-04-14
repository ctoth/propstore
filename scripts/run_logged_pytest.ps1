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

$uvArgs = @("run", "pytest", "-vv") + $PytestArgs
& uv @uvArgs 2>&1 | Tee-Object -FilePath $logPath
$exitCode = $LASTEXITCODE

Write-Output "LOG_PATH=$logPath"
exit $exitCode
