$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$quantPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $quantPython)) {
    python -m venv .venv
    & $quantPython -m pip install -r requirements.txt
    & $quantPython -m pip install -e . --no-deps
}
& $quantPython -m streamlit run app.py

