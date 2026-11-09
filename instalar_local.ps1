$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python configurar.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m venv .venv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe -m pip install -r sistema/requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$env:USE_SQLITE = "1"
$env:DEBUG = "1"
& .\.venv\Scripts\python.exe sistema/manage.py migrate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe sistema/manage.py seed_demo
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe sistema/manage.py runserver
