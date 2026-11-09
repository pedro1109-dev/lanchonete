@echo off
cd /d "%~dp0"
python configurar.py
if errorlevel 1 goto erro
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 goto erro
.venv\Scripts\python.exe -m pip install -r sistema\requirements.txt
if errorlevel 1 goto erro
set USE_SQLITE=1
set DEBUG=1
.venv\Scripts\python.exe sistema\manage.py migrate
if errorlevel 1 goto erro
.venv\Scripts\python.exe sistema\manage.py seed_demo
if errorlevel 1 goto erro
echo Abra http://127.0.0.1:8000 no navegador.
echo Usuario admin. Senha em ADMIN_PASSWORD no arquivo .env.
.venv\Scripts\python.exe sistema\manage.py runserver
goto fim
:erro
echo Ocorreu um erro. Confira a mensagem acima e o README.md.
pause
:fim
