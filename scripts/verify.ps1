[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$virtualEnvironmentPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $virtualEnvironmentPython) {
    $pythonExecutable = $virtualEnvironmentPython
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        Write-Error "Python was not found. Install Python 3.11 and the development dependencies first."
    }
    $pythonExecutable = $pythonCommand.Source
}

$arguments = @(Join-Path $PSScriptRoot "verify.py")
if ($SkipTests) {
    $arguments += "--skip-tests"
}

Push-Location $repositoryRoot
try {
    & $pythonExecutable @arguments
    $verificationExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

exit $verificationExitCode

