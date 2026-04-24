param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RunnerScript = Join-Path $PSScriptRoot "run_logged_pytest.py"

$Label = "pytest"
$NoSources = $false
$Index = 0

while ($Index -lt $Arguments.Count) {
    $Arg = $Arguments[$Index]
    if ($Arg -eq "--label" -or $Arg -eq "-Label") {
        if ($Index + 1 -ge $Arguments.Count) {
            throw "Missing value for $Arg"
        }
        $Label = $Arguments[$Index + 1]
        $Index += 2
        continue
    }
    if ($Arg -eq "--no-sources" -or $Arg -eq "-NoSources") {
        $NoSources = $true
        $Index += 1
        continue
    }
    break
}

$PytestArgs = @()
if ($Index -lt $Arguments.Count) {
    $PytestArgs = $Arguments[$Index..($Arguments.Count - 1)]
}

if ($NoSources) {
    $env:PROPSTORE_UV_NO_SOURCES = "1"
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "Expected synced virtualenv at '$venvPython'. Run 'uv sync --dev --locked --no-sources' first."
    }
    & $venvPython $RunnerScript --label $Label -- $PytestArgs
    exit $LASTEXITCODE
}

$argsForPython = @("run", "python", $RunnerScript)
$argsForPython += @("--label", $Label, "--")
$argsForPython += $PytestArgs

& uv @argsForPython
exit $LASTEXITCODE
