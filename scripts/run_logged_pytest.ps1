param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"

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

$argsForPython = @("run")
if ($NoSources) {
    $env:PROPSTORE_UV_NO_SOURCES = "1"
    $argsForPython += @("--locked", "--no-sources")
}
$argsForPython += @("python", "scripts/run_logged_pytest.py")
$argsForPython += @("--label", $Label, "--")
$argsForPython += $PytestArgs

& uv @argsForPython
exit $LASTEXITCODE
