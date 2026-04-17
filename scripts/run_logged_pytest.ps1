param(
    [string]$Label = "pytest",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"

$argsForPython = @("run", "python", "scripts/run_logged_pytest.py", "--label", $Label, "--")
$argsForPython += $PytestArgs

& uv @argsForPython
exit $LASTEXITCODE
