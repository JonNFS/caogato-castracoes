@echo off
chcp 65001 >nul
echo.
echo  =====================================================
echo   Cao e Gato - Compilar .exe
echo  =====================================================
echo.

echo  Instalando dependencias...
pip install pyinstaller customtkinter Pillow --quiet --upgrade
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] pip falhou. Verifique se Python esta no PATH.
    pause & exit /b 1
)

echo  Gerando icone...
python make_icon.py

echo.
echo  Compilando... aguarde.
echo.

pyinstaller --noconfirm --onefile --windowed --name "CaoGato-Castracoes" --icon "Logo.ico" --add-data "Logo.png;." --add-data "Logo.ico;." --collect-all customtkinter --collect-all PIL main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Compilacao falhou.
    pause & exit /b 1
)

echo.
echo  CONCLUIDO! dist\CaoGato-Castracoes.exe
echo  O banco castracoes.db e criado automaticamente na mesma pasta do .exe
echo.
pause