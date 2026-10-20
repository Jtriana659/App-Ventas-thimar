@echo off
echo Encendiendo el motor de Thimar Store Ventas...
cd C:\app_negocio

:: 1. Activar el Entorno Virtual de VS Code (Si existe)
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate

:: 2. Inicia el servidor de Python en una ventana MINIMIZADA
start /min python main.py

:: 3. Cuenta regresiva oculta de 4 segundos para asegurar que Flask encendio bien
timeout /t 4 /nobreak > nul

