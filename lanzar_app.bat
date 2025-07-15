@echo off
REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Instalar dependencias
echo Instalando paquetes...
pip install -r requirements.txt

REM Instalar módulo matplotlib de Kivy Garden
python -m garden install matplotlib

REM Lanzar la aplicación
echo Lanzando la app...
python main.py

pause
