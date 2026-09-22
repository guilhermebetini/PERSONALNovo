@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado. Criando .venv...
    py -m venv .venv
    if errorlevel 1 (
        echo Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
)

echo Instalando/verificando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Falha ao instalar as dependencias.
    pause
    exit /b 1
)

echo Aplicando migracoes...
".venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 (
    echo Falha ao aplicar as migracoes.
    pause
    exit /b 1
)

echo Iniciando o servidor Django em http://127.0.0.1:8000/
start "" "http://127.0.0.1:8000/"
".venv\Scripts\python.exe" manage.py runserver

pause
