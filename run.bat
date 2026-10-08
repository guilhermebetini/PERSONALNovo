@echo off
setlocal

cd /d "%~dp0"
if errorlevel 1 (
    echo Nao foi possivel acessar a pasta do projeto.
    pause
    exit /b 1
)

if not exist "manage.py" (
    echo manage.py nao foi encontrado. Coloque este arquivo na pasta raiz do projeto Django.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo requirements.txt nao foi encontrado.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando o ambiente virtual...
    where py >nul 2>nul
    if errorlevel 1 (
        where python >nul 2>nul
        if errorlevel 1 (
            echo Python nao foi encontrado. Instale o Python e tente novamente.
            pause
            exit /b 1
        )
        python -m venv .venv
    ) else (
        py -m venv .venv
    )
    if errorlevel 1 (
        echo Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
)

set "PYTHON=%CD%\.venv\Scripts\python.exe"
set "PORT=%~1"
if not defined PORT set "PORT=8000"

"%PYTHON%" -c "import sys; p=sys.argv[1]; sys.exit(0 if p.isdigit() and 1 <= int(p) <= 65535 else 1)" "%PORT%" >nul 2>nul
if errorlevel 1 (
    echo Porta invalida: %PORT%. Use um numero entre 1 e 65535.
    echo Exemplo: run.bat 8001
    pause
    exit /b 1
)

"%PYTHON%" -c "import socket,sys; s=socket.socket(); s.settimeout(1); result=s.connect_ex(('127.0.0.1',int(sys.argv[1]))); s.close(); sys.exit(1 if result == 0 else 0)" "%PORT%" >nul 2>nul
if errorlevel 1 (
    echo A porta %PORT% ja esta em uso. Feche o outro servidor ou execute:
    echo run.bat 8001
    pause
    exit /b 1
)

echo Instalando/verificando dependencias...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Falha ao instalar as dependencias. Verifique sua conexao e tente novamente.
    pause
    exit /b 1
)

echo Aplicando migracoes...
"%PYTHON%" manage.py migrate
if errorlevel 1 (
    echo Falha ao aplicar as migracoes.
    pause
    exit /b 1
)

echo Verificando a configuracao do Django...
"%PYTHON%" manage.py check
if errorlevel 1 (
    echo A verificacao do Django falhou.
    pause
    exit /b 1
)

echo Servidor Django em http://127.0.0.1:%PORT%/
echo Pressione Ctrl+C para encerrar o servidor.
"%PYTHON%" manage.py runserver 127.0.0.1:%PORT%
if errorlevel 1 (
    echo O servidor Django foi encerrado com erro.
    pause
    exit /b 1
)
