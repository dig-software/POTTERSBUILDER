<#
Simple environment diagnostic for POTTERSBUILDER on Windows.
Run from project root: `powershell -ExecutionPolicy Bypass -File .\scripts\check_env.ps1`
#>
Write-Host "== POTTERSBUILDER Environment Diagnostic ==" -ForegroundColor Cyan

function Try-Command($name) {
    try {
        $cmd = Get-Command $name -ErrorAction Stop
        return $cmd.Source
    } catch {
        return $null
    }
}

Write-Host "\n1) Checking Python launchers..." -ForegroundColor Yellow
$pyCmd = Try-Command py
$pythonCmd = Try-Command python
if ($pyCmd) { Write-Host "Found 'py' launcher at: $pyCmd" -ForegroundColor Green } else { Write-Host "'py' launcher not found." -ForegroundColor Red }
if ($pythonCmd) { Write-Host "Found 'python' at: $pythonCmd" -ForegroundColor Green } else { Write-Host "'python' not found in PATH." -ForegroundColor Red }

Write-Host "\n2) Where.exe results (may show multiple locations):" -ForegroundColor Yellow
Write-Host "where python:" -NoNewline; where.exe python 2>$null; if ($LASTEXITCODE -ne 0) { Write-Host " (none)" -ForegroundColor Red }
Write-Host "where py:" -NoNewline; where.exe py 2>$null; if ($LASTEXITCODE -ne 0) { Write-Host " (none)" -ForegroundColor Red }

Write-Host "\n3) PATH (first 30 entries):" -ForegroundColor Yellow
$env:PATH -split ';' | Select-Object -First 30 | ForEach-Object { Write-Host " - $_" }

Write-Host "\n4) App execution aliases (GUI fix if installed from Microsoft Store):" -ForegroundColor Yellow
Write-Host "If you see the message 'Python was not found; run without arguments to install from the Microsoft Store', disable App execution aliases:" -ForegroundColor White
Write-Host "Settings -> Apps -> App execution aliases -> turn off 'python.exe' and 'python3.exe' aliases, then ensure a real Python install is on PATH." -ForegroundColor White

Write-Host "\n5) Versions (if available):" -ForegroundColor Yellow
if ($pythonCmd) {
    try { & python --version } catch { Write-Host "python --version failed" -ForegroundColor Red }
    try { & python -m pip --version } catch { Write-Host "pip not available for this python" -ForegroundColor Red }
} elseif ($pyCmd) {
    try { & py -3 --version } catch { Write-Host "py -3 --version failed" -ForegroundColor Red }
}

Write-Host "\n6) PHP and cURL check (for the frontend):" -ForegroundColor Yellow
if (Try-Command php) {
    Write-Host "Found PHP: $(Try-Command php)" -ForegroundColor Green
    try { & php -r "echo extension_loaded('curl') ? 'curl:installed' : 'curl:missing';" } catch { Write-Host "php test failed" -ForegroundColor Red }
} else {
    Write-Host "PHP not found in PATH." -ForegroundColor Red
}

Write-Host "\n7) Helpful next commands (copy/paste):" -ForegroundColor Yellow
Write-Host "# If you have 'python' available use these:" -ForegroundColor White
Write-Host "python -m venv .venv" -ForegroundColor Green
Write-Host ".\\.venv\\Scripts\\Activate.ps1" -ForegroundColor Green
Write-Host "pip install --upgrade pip" -ForegroundColor Green
Write-Host "pip install -r requirements.txt" -ForegroundColor Green

Write-Host "# If 'python' is not available but 'py' is available, use:" -ForegroundColor White
Write-Host "py -3 -m venv .venv" -ForegroundColor Green
Write-Host ".\\.venv\\Scripts\\Activate.ps1" -ForegroundColor Green
Write-Host "python -m pip install --upgrade pip" -ForegroundColor Green
Write-Host "python -m pip install -r requirements.txt" -ForegroundColor Green

Write-Host "\nIf you still see 'Python was not found', install Python from https://www.python.org/downloads/windows and check 'Add Python to PATH' during installer." -ForegroundColor White
Write-Host "Or use the Microsoft Store installer, then disable App execution aliases as described above if the 'store' alias blocks the real Python." -ForegroundColor White

Write-Host "\n-- End of diagnostic --" -ForegroundColor Cyan
