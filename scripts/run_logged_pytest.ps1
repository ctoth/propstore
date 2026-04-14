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
